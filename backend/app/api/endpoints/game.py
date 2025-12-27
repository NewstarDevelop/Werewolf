"""Game API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import List, Dict

from app.models.game import game_store
from app.schemas.enums import (
    GamePhase, GameStatus, Role, ActionType, MessageType
)
from app.schemas.game import (
    GameStartRequest, GameStartResponse, GameState, StepResponse, PendingAction
)
from app.schemas.action import ActionRequest, ActionResponse
from app.schemas.player import PlayerPublic
from app.schemas.message import MessageInGame
from app.services.game_engine import game_engine
from app.services.log_manager import get_game_logs

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/start", response_model=GameStartResponse)
def start_game(request: GameStartRequest) -> GameStartResponse:
    """
    Create a new game and assign roles.
    POST /api/game/start
    """
    game = game_store.create_game(
        human_seat=request.human_seat,
        human_role=request.human_role
    )

    human_player = game.get_player(game.human_seat)
    if not human_player:
        raise HTTPException(status_code=500, detail="Failed to create game")

    players = [
        PlayerPublic(
            seat_id=p.seat_id,
            is_alive=p.is_alive,
            is_human=p.is_human,
            name=p.personality.name if p.personality else None
        )
        for p in game.players.values()
    ]

    return GameStartResponse(
        game_id=game.id,
        player_role=human_player.role,
        player_seat=human_player.seat_id,
        players=players
    )


@router.get("/{game_id}/state", response_model=GameState)
def get_game_state(game_id: str) -> GameState:
    """
    Get current game state.
    GET /api/game/{game_id}/state
    """
    game = game_store.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    human_player = game.get_player(game.human_seat)
    if not human_player:
        raise HTTPException(status_code=500, detail="Human player not found")

    # Build player list (include roles if game is finished)
    players = [
        PlayerPublic(
            seat_id=p.seat_id,
            is_alive=p.is_alive,
            is_human=p.is_human,
            name=p.personality.name if p.personality else None,
            role=p.role if game.status == GameStatus.FINISHED else None
        )
        for p in game.players.values()
    ]

    # Build message log (filter wolf chat messages for non-werewolves)
    message_log = [
        MessageInGame(
            seat_id=m.seat_id,
            text=m.content,
            type=m.msg_type,
            day=m.day
        )
        for m in game.messages
        # Only werewolves can see wolf chat messages
        if m.msg_type != MessageType.WOLF_CHAT or human_player.role == Role.WEREWOLF
    ]

    # Determine pending action for human
    pending_action = _get_pending_action(game, human_player)

    # Get role-specific info
    wolf_teammates = []
    verified_results = {}
    wolf_votes_visible = {}

    if human_player.role == Role.WEREWOLF:
        wolf_teammates = human_player.teammates
        # Show teammate votes during werewolf night phase
        if game.phase == GamePhase.NIGHT_WEREWOLF:
            wolf_votes_visible = {
                seat: target
                for seat, target in game.wolf_votes.items()
                if seat in human_player.teammates
            }
    elif human_player.role == Role.SEER:
        verified_results = human_player.verified_players

    return GameState(
        game_id=game.id,
        status=game.status,
        day=game.day,
        phase=game.phase,
        current_actor=game.current_actor_seat,
        my_seat=human_player.seat_id,
        my_role=human_player.role,
        players=players,
        message_log=message_log,
        pending_action=pending_action,
        winner=game.winner,
        night_kill_target=game.night_kill_target if human_player.role == Role.WITCH else None,
        wolf_teammates=wolf_teammates,
        verified_results=verified_results,
        wolf_votes_visible=wolf_votes_visible
    )


def _get_pending_action(game, human_player) -> PendingAction | None:
    """Determine what action the human player needs to take."""
    phase = game.phase
    role = human_player.role

    # Hunter can shoot after being eliminated (by vote/kill). This phase is explicitly a "last action".
    if phase == GamePhase.HUNTER_SHOOT and role == Role.HUNTER:
        if game.current_actor_seat == human_player.seat_id and human_player.can_shoot:
            alive_seats = game.get_alive_seats()
            return PendingAction(
                type=ActionType.SHOOT,
                choices=alive_seats + [0],  # 0 = skip
                message="你可以开枪带走一名玩家"
            )

    if not human_player.is_alive:
        return None

    alive_seats = game.get_alive_seats()
    other_alive = [s for s in alive_seats if s != human_player.seat_id]

    # Night werewolf chat phase
    if phase == GamePhase.NIGHT_WEREWOLF_CHAT and role == Role.WEREWOLF:
        if human_player.seat_id not in game.wolf_chat_completed:
            return PendingAction(
                type=ActionType.SPEAK,
                choices=[],
                message="与狼队友讨论今晚击杀目标（发言后自动进入投票）"
            )

    # Night werewolf phase
    if phase == GamePhase.NIGHT_WEREWOLF and role == Role.WEREWOLF:
        if human_player.seat_id not in game.wolf_votes:
            non_wolves = [s for s in alive_seats if s not in human_player.teammates
                        and s != human_player.seat_id]
            return PendingAction(
                type=ActionType.KILL,
                choices=non_wolves,
                message="请选择今晚要击杀的目标"
            )

    # Night seer phase
    elif phase == GamePhase.NIGHT_SEER and role == Role.SEER:
        # If already verified this night, allow auto-step to proceed.
        if game.seer_verified_this_night:
            return None
        unverified = [s for s in other_alive if s not in human_player.verified_players]
        if not unverified:
            return None
        return PendingAction(
            type=ActionType.VERIFY,
            choices=unverified,
            message="请选择要查验的玩家"
        )

    # Night witch phase
    elif phase == GamePhase.NIGHT_WITCH and role == Role.WITCH:
        used_save_this_night = any(
            a.day == game.day
            and a.player_id == human_player.seat_id
            and a.action_type == ActionType.SAVE
            for a in game.actions
        )

        # 第一步：先决策解药（或跳过解药）
        if not game.witch_save_decided:
            if human_player.has_save_potion and game.night_kill_target:
                return PendingAction(
                    type=ActionType.SAVE,
                    choices=[game.night_kill_target, 0],  # 0 = skip
                    message=f"今晚{game.night_kill_target}号被杀，是否使用解药？"
                )

            no_save_reason = "今晚无人被杀" if game.night_kill_target is None else "你没有解药"
            # 为保持前端兼容，这里仍返回 SAVE 类型；前端点“技能”按钮将发送 SKIP 来跳过。
            return PendingAction(
                type=ActionType.SAVE,
                choices=[0],
                message=f"{no_save_reason}，点击技能按钮跳过解药决策"
            )

        # 第二步：再决策毒药（或跳过毒药）
        if not game.witch_poison_decided:
            # 规则：同一晚使用了解药则不能再用毒药
            if used_save_this_night:
                return PendingAction(
                    type=ActionType.POISON,
                    choices=[0],
                    message="你今晚已使用解药，无法再使用毒药，点击技能按钮继续"
                )

            if human_player.has_poison_potion:
                return PendingAction(
                    type=ActionType.POISON,
                    choices=other_alive + [0],  # 0 = skip
                    message="是否使用毒药？选择目标或跳过"
                )

            return PendingAction(
                type=ActionType.POISON,
                choices=[0],
                message="你没有可用的毒药，点击技能按钮继续"
            )

    # Day speech phase
    elif phase == GamePhase.DAY_SPEECH:
        if (game.current_speech_index < len(game.speech_order) and
            game.speech_order[game.current_speech_index] == human_player.seat_id):
            return PendingAction(
                type=ActionType.SPEAK,
                choices=[],
                message="轮到你发言了"
            )

    # Day vote phase
    elif phase == GamePhase.DAY_VOTE:
        if human_player.seat_id not in game.day_votes:
            return PendingAction(
                type=ActionType.VOTE,
                choices=other_alive + [0],  # 0 = abstain
                message="请投票选择要放逐的玩家，或弃票"
            )

    return None


@router.post("/{game_id}/step", response_model=StepResponse)
def step_game(game_id: str) -> StepResponse:
    """
    Advance the game state by one step.
    POST /api/game/{game_id}/step
    """
    result = game_engine.step(game_id)

    status = result.get("status", "error")
    new_phase = result.get("new_phase")
    message = result.get("message")
    winner = result.get("winner")

    if status == "error":
        raise HTTPException(status_code=400, detail=message or "Unknown error")

    return StepResponse(
        status=status,
        new_phase=new_phase,
        message=message or (f"Winner: {winner}" if winner else None)
    )


@router.post("/{game_id}/action", response_model=ActionResponse)
def submit_action(game_id: str, request: ActionRequest) -> ActionResponse:
    """
    Submit a player action.
    POST /api/game/{game_id}/action
    """
    result = game_engine.process_human_action(
        game_id=game_id,
        seat_id=request.seat_id,
        action_type=request.action_type,
        target_id=request.target_id,
        content=request.content
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Action failed")
        )

    return ActionResponse(
        success=True,
        message=result.get("message")
    )


@router.delete("/{game_id}")
def delete_game(game_id: str) -> dict:
    """
    Delete a game.
    DELETE /api/game/{game_id}
    """
    if game_store.delete_game(game_id):
        return {"success": True, "message": "Game deleted"}
    raise HTTPException(status_code=404, detail="Game not found")


@router.get("/{game_id}/logs")
def get_logs(game_id: str, limit: int = 100) -> Dict[str, List[Dict]]:
    """
    Get sanitized game logs (filtered to remove spoilers).
    GET /api/game/{game_id}/logs?limit=100
    """
    game = game_store.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    logs = get_game_logs(game_id, limit)
    return {"logs": logs}
