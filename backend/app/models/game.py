"""Game data models for in-memory storage."""
import uuid
import random
from typing import Optional
from dataclasses import dataclass, field

from app.schemas.enums import (
    GameStatus, GamePhase, Role, ActionType, MessageType, Winner
)
from app.schemas.player import Personality


# AI personality templates
AI_PERSONALITIES = [
    Personality(name="暴躁的老王", trait="激进", speaking_style="口语化"),
    Personality(name="理性的Alice", trait="逻辑流", speaking_style="严谨"),
    Personality(name="沉默的张三", trait="保守", speaking_style="简短"),
    Personality(name="热情的小红", trait="直觉流", speaking_style="幽默"),
    Personality(name="老练的李四", trait="随波逐流", speaking_style="口语化"),
    Personality(name="精明的王五", trait="逻辑流", speaking_style="严谨"),
    Personality(name="冲动的赵六", trait="激进", speaking_style="口语化"),
    Personality(name="稳重的钱七", trait="保守", speaking_style="简短"),
]


@dataclass
class Player:
    """Player model."""
    seat_id: int
    role: Role
    is_human: bool = False
    is_alive: bool = True
    personality: Optional[Personality] = None
    # Witch specific
    has_save_potion: bool = True
    has_poison_potion: bool = True
    # Hunter specific
    can_shoot: bool = True  # False if poisoned
    # Seer specific
    verified_players: dict[int, bool] = field(default_factory=dict)
    # Werewolf specific
    teammates: list[int] = field(default_factory=list)

    def __post_init__(self):
        if self.verified_players is None:
            self.verified_players = {}
        if self.teammates is None:
            self.teammates = []


@dataclass
class Message:
    """Message model."""
    id: int
    game_id: str
    day: int
    seat_id: int  # 0 for system
    content: str
    msg_type: MessageType = MessageType.SPEECH


@dataclass
class Action:
    """Action record model."""
    id: int
    game_id: str
    day: int
    phase: str
    player_id: int
    action_type: ActionType
    target_id: Optional[int] = None


@dataclass
class Game:
    """Game model."""
    id: str
    status: GameStatus = GameStatus.WAITING
    day: int = 1
    phase: GamePhase = GamePhase.NIGHT_START
    winner: Optional[Winner] = None
    players: dict[int, Player] = field(default_factory=dict)
    messages: list[Message] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    current_actor_seat: Optional[int] = None
    human_seat: int = 1
    # Night phase tracking
    night_kill_target: Optional[int] = None
    wolf_votes: dict[int, int] = field(default_factory=dict)  # wolf_seat -> target_seat
    wolf_chat_completed: set[int] = field(default_factory=set)  # Seats that completed wolf chat
    seer_verified_this_night: bool = False  # Track if seer verified this night
    witch_save_decided: bool = False  # Track if witch save decision made this night
    witch_poison_decided: bool = False  # Track if witch poison decision made this night
    # Day phase tracking
    day_votes: dict[int, int] = field(default_factory=dict)  # voter_seat -> target_seat
    speech_order: list[int] = field(default_factory=list)
    current_speech_index: int = 0
    # Death tracking
    pending_deaths: list[int] = field(default_factory=list)  # Seats to die
    last_night_deaths: list[int] = field(default_factory=list)
    # Message counter
    _message_counter: int = 0
    _action_counter: int = 0

    def get_player(self, seat_id: int) -> Optional[Player]:
        """Get player by seat ID."""
        return self.players.get(seat_id)

    def get_alive_players(self) -> list[Player]:
        """Get all alive players."""
        return [p for p in self.players.values() if p.is_alive]

    def get_alive_seats(self) -> list[int]:
        """Get all alive player seat IDs."""
        return [p.seat_id for p in self.get_alive_players()]

    def get_werewolves(self) -> list[Player]:
        """Get all werewolf players."""
        return [p for p in self.players.values() if p.role == Role.WEREWOLF]

    def get_alive_werewolves(self) -> list[Player]:
        """Get alive werewolves."""
        return [p for p in self.get_werewolves() if p.is_alive]

    def get_player_by_role(self, role: Role) -> Optional[Player]:
        """Get player by role (for unique roles)."""
        for p in self.players.values():
            if p.role == role:
                return p
        return None

    def add_message(
        self,
        seat_id: int,
        content: str,
        msg_type: MessageType = MessageType.SPEECH
    ) -> Message:
        """Add a message to the game."""
        self._message_counter += 1
        msg = Message(
            id=self._message_counter,
            game_id=self.id,
            day=self.day,
            seat_id=seat_id,
            content=content,
            msg_type=msg_type
        )
        self.messages.append(msg)
        return msg

    def add_action(
        self,
        player_id: int,
        action_type: ActionType,
        target_id: Optional[int] = None
    ) -> Action:
        """Record an action."""
        self._action_counter += 1
        action = Action(
            id=self._action_counter,
            game_id=self.id,
            day=self.day,
            phase=self.phase.value,
            player_id=player_id,
            action_type=action_type,
            target_id=target_id
        )
        self.actions.append(action)
        return action

    def kill_player(self, seat_id: int, by_poison: bool = False) -> None:
        """Kill a player."""
        player = self.get_player(seat_id)
        if player:
            player.is_alive = False
            if by_poison and player.role == Role.HUNTER:
                player.can_shoot = False

    def check_winner(self) -> Optional[Winner]:
        """Check if game has a winner."""
        alive_wolves = [p for p in self.get_alive_players() if p.role == Role.WEREWOLF]
        alive_gods = [p for p in self.get_alive_players()
                      if p.role in [Role.SEER, Role.WITCH, Role.HUNTER]]
        alive_villagers = [p for p in self.get_alive_players() if p.role == Role.VILLAGER]

        # Werewolves win if all gods or all villagers are dead
        if len(alive_wolves) > 0 and (len(alive_gods) == 0 or len(alive_villagers) == 0):
            return Winner.WEREWOLF

        # Villagers win if all werewolves are dead
        if len(alive_wolves) == 0:
            return Winner.VILLAGER

        return None


class GameStore:
    """In-memory game storage."""

    def __init__(self):
        self.games: dict[str, Game] = {}

    def create_game(
        self,
        human_seat: Optional[int] = None,
        human_role: Optional[Role] = None
    ) -> Game:
        """Create a new game with random role assignment."""
        game_id = str(uuid.uuid4())[:8]
        game = Game(id=game_id)

        # Role distribution: 3 werewolves, 3 villagers, 1 seer, 1 witch, 1 hunter
        roles = [
            Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
            Role.VILLAGER, Role.VILLAGER, Role.VILLAGER,
            Role.SEER, Role.WITCH, Role.HUNTER
        ]

        # Determine human seat
        if human_seat is None:
            human_seat = random.randint(1, 9)
        game.human_seat = human_seat

        # If human role is specified, ensure they get it
        if human_role:
            roles.remove(human_role)
            random.shuffle(roles)
            roles.insert(human_seat - 1, human_role)
        else:
            random.shuffle(roles)

        # Shuffle personalities
        personalities = AI_PERSONALITIES.copy()
        random.shuffle(personalities)

        # Create players
        werewolf_seats = []
        for i, role in enumerate(roles):
            seat_id = i + 1
            is_human = (seat_id == human_seat)

            player = Player(
                seat_id=seat_id,
                role=role,
                is_human=is_human,
                personality=None if is_human else personalities[i % len(personalities)]
            )

            if role == Role.WEREWOLF:
                werewolf_seats.append(seat_id)

            game.players[seat_id] = player

        # Set werewolf teammates
        for seat_id in werewolf_seats:
            player = game.players[seat_id]
            player.teammates = [s for s in werewolf_seats if s != seat_id]

        game.status = GameStatus.PLAYING
        self.games[game_id] = game
        return game

    def get_game(self, game_id: str) -> Optional[Game]:
        """Get game by ID."""
        return self.games.get(game_id)

    def delete_game(self, game_id: str) -> bool:
        """Delete a game."""
        if game_id in self.games:
            del self.games[game_id]
            return True
        return False


# Global game store instance
game_store = GameStore()
