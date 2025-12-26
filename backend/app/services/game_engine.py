"""Game engine - core game logic and state machine."""
import random
from typing import Optional

from app.models.game import Game, Player, game_store
from app.schemas.enums import (
    GamePhase, GameStatus, Role, ActionType, MessageType, Winner
)
from app.services.llm import LLMService


class GameEngine:
    """Core game engine handling state transitions and AI turns."""

    def __init__(self):
        self.llm = LLMService()

    def step(self, game_id: str) -> dict:
        """
        Advance the game state by one step.
        Returns status and any relevant info.
        """
        game = game_store.get_game(game_id)
        if not game:
            return {"status": "error", "message": "Game not found"}

        if game.status == GameStatus.FINISHED:
            return {"status": "game_over", "winner": game.winner}

        # Route to appropriate phase handler
        phase_handlers = {
            GamePhase.NIGHT_START: self._handle_night_start,
            GamePhase.NIGHT_WEREWOLF: self._handle_night_werewolf,
            GamePhase.NIGHT_SEER: self._handle_night_seer,
            GamePhase.NIGHT_WITCH: self._handle_night_witch,
            GamePhase.DAY_ANNOUNCEMENT: self._handle_day_announcement,
            GamePhase.DAY_LAST_WORDS: self._handle_day_last_words,
            GamePhase.DAY_SPEECH: self._handle_day_speech,
            GamePhase.DAY_VOTE: self._handle_day_vote,
            GamePhase.DAY_VOTE_RESULT: self._handle_day_vote_result,
            GamePhase.HUNTER_SHOOT: self._handle_hunter_shoot,
            GamePhase.GAME_OVER: self._handle_game_over,
        }

        handler = phase_handlers.get(game.phase)
        if handler:
            return handler(game)

        return {"status": "error", "message": f"Unknown phase: {game.phase}"}

    def process_human_action(
        self,
        game_id: str,
        seat_id: int,
        action_type: ActionType,
        target_id: Optional[int] = None,
        content: Optional[str] = None
    ) -> dict:
        """Process an action from the human player."""
        game = game_store.get_game(game_id)
        if not game:
            return {"success": False, "message": "Game not found"}

        player = game.get_player(seat_id)
        if not player or not player.is_human:
            return {"success": False, "message": "Invalid player"}

        if not player.is_alive:
            return {"success": False, "message": "Player is dead"}

        # Validate action based on current phase
        result = self._validate_and_execute_action(
            game, player, action_type, target_id, content
        )

        return result

    def _validate_and_execute_action(
        self,
        game: Game,
        player: Player,
        action_type: ActionType,
        target_id: Optional[int],
        content: Optional[str]
    ) -> dict:
        """Validate and execute a player action."""
        phase = game.phase

        # Night werewolf phase
        if phase == GamePhase.NIGHT_WEREWOLF and player.role == Role.WEREWOLF:
            if action_type == ActionType.KILL and target_id:
                game.wolf_votes[player.seat_id] = target_id
                game.add_action(player.seat_id, ActionType.KILL, target_id)
                return {"success": True, "message": "Vote recorded"}

        # Night seer phase
        elif phase == GamePhase.NIGHT_SEER and player.role == Role.SEER:
            if action_type == ActionType.VERIFY and target_id:
                # Check if already verified someone this night
                if game.seer_verified_this_night:
                    return {"success": False, "message": "你今晚已经验过人了"}

                # Check if trying to verify self
                if target_id == player.seat_id:
                    return {"success": False, "message": "不能验证自己"}

                target = game.get_player(target_id)
                if target:
                    is_wolf = target.role == Role.WEREWOLF
                    player.verified_players[target_id] = is_wolf
                    game.seer_verified_this_night = True  # Mark as verified
                    game.add_action(player.seat_id, ActionType.VERIFY, target_id)
                    return {
                        "success": True,
                        "message": f"{target_id}号是{'狼人' if is_wolf else '好人'}"
                    }

        # Night witch phase
        elif phase == GamePhase.NIGHT_WITCH and player.role == Role.WITCH:
            if action_type == ActionType.SAVE:
                if player.has_save_potion and game.night_kill_target:
                    player.has_save_potion = False
                    game.pending_deaths.remove(game.night_kill_target)
                    game.add_action(player.seat_id, ActionType.SAVE, game.night_kill_target)
                    return {"success": True, "message": "已使用解药"}
            elif action_type == ActionType.POISON and target_id:
                if player.has_poison_potion:
                    player.has_poison_potion = False
                    game.pending_deaths.append(target_id)
                    game.add_action(player.seat_id, ActionType.POISON, target_id)
                    return {"success": True, "message": "已使用毒药"}
            elif action_type == ActionType.SKIP:
                return {"success": True, "message": "跳过"}

        # Day speech phase
        elif phase == GamePhase.DAY_SPEECH:
            if action_type == ActionType.SPEAK and content:
                game.add_message(player.seat_id, content, MessageType.SPEECH)
                game.add_action(player.seat_id, ActionType.SPEAK)
                # Move to next speaker
                game.current_speech_index += 1
                # Update current_actor_seat to next speaker
                if game.current_speech_index < len(game.speech_order):
                    game.current_actor_seat = game.speech_order[game.current_speech_index]
                else:
                    game.current_actor_seat = None
                return {"success": True, "message": "发言已记录"}

        # Day vote phase
        elif phase == GamePhase.DAY_VOTE:
            if action_type == ActionType.VOTE:
                game.day_votes[player.seat_id] = target_id if target_id else 0
                game.add_action(player.seat_id, ActionType.VOTE, target_id)
                return {"success": True, "message": "投票已记录"}

        # Hunter shoot phase
        elif phase == GamePhase.HUNTER_SHOOT and player.role == Role.HUNTER:
            if action_type == ActionType.SHOOT and target_id:
                if player.can_shoot:
                    game.pending_deaths.append(target_id)
                    game.add_action(player.seat_id, ActionType.SHOOT, target_id)
                    return {"success": True, "message": f"开枪带走{target_id}号"}
            elif action_type == ActionType.SKIP:
                return {"success": True, "message": "放弃开枪"}

        # Last words phase
        elif phase == GamePhase.DAY_LAST_WORDS:
            if action_type == ActionType.SPEAK and content:
                game.add_message(player.seat_id, content, MessageType.LAST_WORDS)
                return {"success": True, "message": "遗言已记录"}

        return {"success": False, "message": "Invalid action for current phase"}

    # ==================== Phase Handlers ====================

    def _handle_night_start(self, game: Game) -> dict:
        """Handle night start - transition to werewolf phase."""
        game.add_message(0, f"第{game.day}天夜晚降临，请闭眼。", MessageType.SYSTEM)
        game.phase = GamePhase.NIGHT_WEREWOLF
        game.wolf_votes = {}
        game.pending_deaths = []
        game.seer_verified_this_night = False  # Reset seer verification tracker
        return {"status": "updated", "new_phase": game.phase}

    def _handle_night_werewolf(self, game: Game) -> dict:
        """Handle werewolf kill phase."""
        alive_wolves = game.get_alive_werewolves()
        human_player = game.get_player(game.human_seat)

        # Check if human is werewolf and hasn't voted
        if human_player and human_player.is_alive and human_player.role == Role.WEREWOLF:
            if human_player.seat_id not in game.wolf_votes:
                return {"status": "waiting_for_human", "phase": game.phase}

        # AI werewolves vote
        for wolf in alive_wolves:
            if not wolf.is_human and wolf.seat_id not in game.wolf_votes:
                # AI picks a random non-wolf target
                targets = [p.seat_id for p in game.get_alive_players()
                          if p.role != Role.WEREWOLF]
                if targets:
                    target = self.llm.decide_kill_target(wolf, game, targets)
                    game.wolf_votes[wolf.seat_id] = target
                    game.add_action(wolf.seat_id, ActionType.KILL, target)

        # Determine kill target (majority or random from votes)
        if game.wolf_votes:
            vote_counts: dict[int, int] = {}
            for target in game.wolf_votes.values():
                vote_counts[target] = vote_counts.get(target, 0) + 1
            max_votes = max(vote_counts.values())
            top_targets = [t for t, v in vote_counts.items() if v == max_votes]
            game.night_kill_target = random.choice(top_targets)
            game.pending_deaths.append(game.night_kill_target)

        game.phase = GamePhase.NIGHT_SEER
        return {"status": "updated", "new_phase": game.phase}

    def _handle_night_seer(self, game: Game) -> dict:
        """Handle seer verification phase."""
        seer = game.get_player_by_role(Role.SEER)

        if seer and seer.is_alive:
            if seer.is_human:
                return {"status": "waiting_for_human", "phase": game.phase}
            else:
                # AI seer picks a target to verify
                targets = [p.seat_id for p in game.get_alive_players()
                          if p.seat_id != seer.seat_id
                          and p.seat_id not in seer.verified_players]
                if targets:
                    target = self.llm.decide_verify_target(seer, game, targets)
                    target_player = game.get_player(target)
                    if target_player:
                        is_wolf = target_player.role == Role.WEREWOLF
                        seer.verified_players[target] = is_wolf
                        game.add_action(seer.seat_id, ActionType.VERIFY, target)

        game.phase = GamePhase.NIGHT_WITCH
        return {"status": "updated", "new_phase": game.phase}

    def _handle_night_witch(self, game: Game) -> dict:
        """Handle witch save/poison phase."""
        witch = game.get_player_by_role(Role.WITCH)

        if witch and witch.is_alive:
            if witch.is_human:
                return {"status": "waiting_for_human", "phase": game.phase}
            else:
                # AI witch decision
                decision = self.llm.decide_witch_action(witch, game)

                if decision.get("save") and witch.has_save_potion:
                    if game.night_kill_target in game.pending_deaths:
                        witch.has_save_potion = False
                        game.pending_deaths.remove(game.night_kill_target)
                        game.add_action(witch.seat_id, ActionType.SAVE, game.night_kill_target)

                if decision.get("poison_target") and witch.has_poison_potion:
                    target = decision["poison_target"]
                    witch.has_poison_potion = False
                    game.pending_deaths.append(target)
                    game.add_action(witch.seat_id, ActionType.POISON, target)

        # Process deaths
        game.last_night_deaths = list(set(game.pending_deaths))
        for seat_id in game.last_night_deaths:
            # Check if poisoned (for hunter)
            was_poisoned = any(
                a.action_type == ActionType.POISON and a.target_id == seat_id
                for a in game.actions if a.day == game.day
            )
            game.kill_player(seat_id, by_poison=was_poisoned)

        game.phase = GamePhase.DAY_ANNOUNCEMENT
        return {"status": "updated", "new_phase": game.phase}

    def _handle_day_announcement(self, game: Game) -> dict:
        """Announce night deaths and check for hunter trigger."""
        if game.last_night_deaths:
            deaths_str = "、".join([f"{s}号" for s in game.last_night_deaths])
            game.add_message(0, f"天亮了，昨晚{deaths_str}死亡。", MessageType.SYSTEM)

            # Check for hunter death
            for seat_id in game.last_night_deaths:
                player = game.get_player(seat_id)
                if player and player.role == Role.HUNTER and player.can_shoot:
                    game.current_actor_seat = seat_id
                    game.phase = GamePhase.HUNTER_SHOOT
                    return {"status": "updated", "new_phase": game.phase}
        else:
            game.add_message(0, "天亮了，昨晚是平安夜。", MessageType.SYSTEM)

        # Check win condition
        winner = game.check_winner()
        if winner:
            game.winner = winner
            game.status = GameStatus.FINISHED
            game.phase = GamePhase.GAME_OVER
            return {"status": "game_over", "winner": winner}

        # Setup speech order (from seat 1 or random)
        alive_seats = game.get_alive_seats()
        start_seat = random.choice(alive_seats)
        start_idx = alive_seats.index(start_seat)
        game.speech_order = alive_seats[start_idx:] + alive_seats[:start_idx]
        game.current_speech_index = 0
        game.current_actor_seat = game.speech_order[0]

        game.phase = GamePhase.DAY_SPEECH
        game.add_message(0, f"请从{game.speech_order[0]}号开始发言。", MessageType.SYSTEM)
        return {"status": "updated", "new_phase": game.phase}

    def _handle_day_last_words(self, game: Game) -> dict:
        """Handle last words for dead player."""
        # For simplicity, skip last words in MVP
        game.phase = GamePhase.DAY_SPEECH
        return {"status": "updated", "new_phase": game.phase}

    def _handle_day_speech(self, game: Game) -> dict:
        """Handle day speech phase."""
        if game.current_speech_index >= len(game.speech_order):
            # All speeches done, move to vote
            game.phase = GamePhase.DAY_VOTE
            game.day_votes = {}
            game.add_message(0, "发言结束，请投票。", MessageType.SYSTEM)
            return {"status": "updated", "new_phase": game.phase}

        current_seat = game.speech_order[game.current_speech_index]
        game.current_actor_seat = current_seat
        player = game.get_player(current_seat)

        if not player:
            game.current_speech_index += 1
            return self._handle_day_speech(game)

        if player.is_human:
            return {"status": "waiting_for_human", "phase": game.phase}

        # AI speech
        speech = self.llm.generate_speech(player, game)
        game.add_message(player.seat_id, speech, MessageType.SPEECH)
        game.current_speech_index += 1

        return {"status": "updated", "new_phase": game.phase}

    def _handle_day_vote(self, game: Game) -> dict:
        """Handle day vote phase."""
        alive_players = game.get_alive_players()
        human_player = game.get_player(game.human_seat)

        # Check if human needs to vote
        if human_player and human_player.is_alive:
            if human_player.seat_id not in game.day_votes:
                return {"status": "waiting_for_human", "phase": game.phase}

        # AI players vote
        for player in alive_players:
            if not player.is_human and player.seat_id not in game.day_votes:
                targets = [p.seat_id for p in alive_players if p.seat_id != player.seat_id]
                target = self.llm.decide_vote_target(player, game, targets)
                game.day_votes[player.seat_id] = target
                game.add_action(player.seat_id, ActionType.VOTE, target)

        game.phase = GamePhase.DAY_VOTE_RESULT
        return {"status": "updated", "new_phase": game.phase}

    def _handle_day_vote_result(self, game: Game) -> dict:
        """Process vote results."""
        vote_counts: dict[int, int] = {}
        for target in game.day_votes.values():
            if target and target > 0:
                vote_counts[target] = vote_counts.get(target, 0) + 1

        # Announce votes
        vote_summary = []
        for voter, target in game.day_votes.items():
            if target and target > 0:
                vote_summary.append(f"{voter}号投{target}号")
            else:
                vote_summary.append(f"{voter}号弃票")
        game.add_message(0, "投票结果：" + "，".join(vote_summary), MessageType.SYSTEM)

        if not vote_counts:
            game.add_message(0, "全员弃票，无人出局。", MessageType.SYSTEM)
        else:
            max_votes = max(vote_counts.values())
            top_targets = [t for t, v in vote_counts.items() if v == max_votes]

            if len(top_targets) > 1:
                # Tie - no one dies (simplified rule)
                game.add_message(0, f"平票，无人出局。", MessageType.SYSTEM)
            else:
                eliminated = top_targets[0]
                game.add_message(0, f"{eliminated}号被投票出局。", MessageType.SYSTEM)
                game.kill_player(eliminated)

                # Check for hunter
                player = game.get_player(eliminated)
                if player and player.role == Role.HUNTER and player.can_shoot:
                    game.current_actor_seat = eliminated
                    game.phase = GamePhase.HUNTER_SHOOT
                    return {"status": "updated", "new_phase": game.phase}

        # Check win condition
        winner = game.check_winner()
        if winner:
            game.winner = winner
            game.status = GameStatus.FINISHED
            game.phase = GamePhase.GAME_OVER
            return {"status": "game_over", "winner": winner}

        # Next night
        game.day += 1
        game.phase = GamePhase.NIGHT_START
        return {"status": "updated", "new_phase": game.phase}

    def _handle_hunter_shoot(self, game: Game) -> dict:
        """Handle hunter shooting."""
        hunter = game.get_player(game.current_actor_seat)
        if not hunter or hunter.role != Role.HUNTER:
            # Skip if not hunter
            return self._continue_after_hunter(game)

        if not hunter.can_shoot:
            game.add_message(0, f"{hunter.seat_id}号猎人被毒死，无法开枪。", MessageType.SYSTEM)
            return self._continue_after_hunter(game)

        if hunter.is_human:
            return {"status": "waiting_for_human", "phase": game.phase}

        # AI hunter decides
        targets = [p.seat_id for p in game.get_alive_players()]
        if targets:
            target = self.llm.decide_shoot_target(hunter, game, targets)
            if target:
                game.add_message(0, f"{hunter.seat_id}号猎人开枪带走{target}号。", MessageType.SYSTEM)
                game.kill_player(target)
                game.add_action(hunter.seat_id, ActionType.SHOOT, target)
            else:
                game.add_message(0, f"{hunter.seat_id}号猎人放弃开枪。", MessageType.SYSTEM)

        return self._continue_after_hunter(game)

    def _continue_after_hunter(self, game: Game) -> dict:
        """Continue game flow after hunter action."""
        # Check win condition
        winner = game.check_winner()
        if winner:
            game.winner = winner
            game.status = GameStatus.FINISHED
            game.phase = GamePhase.GAME_OVER
            return {"status": "game_over", "winner": winner}

        # Determine next phase based on when hunter died
        if game.phase == GamePhase.HUNTER_SHOOT:
            # If during day announcement (night death), continue to speech
            if game.last_night_deaths:
                alive_seats = game.get_alive_seats()
                if alive_seats:
                    start_seat = random.choice(alive_seats)
                    start_idx = alive_seats.index(start_seat)
                    game.speech_order = alive_seats[start_idx:] + alive_seats[:start_idx]
                    game.current_speech_index = 0
                    game.current_actor_seat = game.speech_order[0]
                    game.phase = GamePhase.DAY_SPEECH
                    game.add_message(0, f"请从{game.speech_order[0]}号开始发言。", MessageType.SYSTEM)
            else:
                # After vote, go to next night
                game.day += 1
                game.phase = GamePhase.NIGHT_START

        return {"status": "updated", "new_phase": game.phase}

    def _handle_game_over(self, game: Game) -> dict:
        """Handle game over."""
        winner_text = "好人阵营" if game.winner == Winner.VILLAGER else "狼人阵营"
        game.add_message(0, f"游戏结束！{winner_text}获胜！", MessageType.SYSTEM)
        return {"status": "game_over", "winner": game.winner}


# Global engine instance
game_engine = GameEngine()
