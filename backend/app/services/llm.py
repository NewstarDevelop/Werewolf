"""LLM Service - Multi-provider AI implementation with retry and fallback."""
import json
import random
import logging
import time
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

from openai import OpenAI

from app.core.config import settings, AIProviderConfig
from app.services.prompts import (
    build_system_prompt,
    build_context_prompt,
    build_wolf_strategy_prompt,
)

if TYPE_CHECKING:
    from app.models.game import Game, Player

logger = logging.getLogger(__name__)

# Rate limiting configuration
INITIAL_RETRY_DELAY = 60  # Initial delay: 1 minute between first and second call
MAX_RETRY_DELAY = 180  # Maximum delay: 3 minutes
BACKOFF_INCREMENT = 60  # Add 1 minute on each failure

# Delay between consecutive LLM calls to avoid truncation
# Reduced from 15s to 2s for better game flow
# Most API providers allow 60 requests/minute, so 2s is safe
CALL_INTERVAL = 2  # seconds between calls

# Custom User-Agent to bypass Cloudflare bot detection
CUSTOM_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class LLMResponse:
    """Structured response from LLM."""
    thought: str
    speak: str
    action_target: Optional[int]
    raw_response: str = ""
    is_fallback: bool = False
    provider_name: str = ""


# Fallback responses for different scenarios
FALLBACK_SPEECHES = {
    "werewolf": [
        "我觉得场上形势不太明朗,先听听大家的意见。",
        "我是好人，大家可以相信我。",
        "我没什么特别想说的，过。",
        "我觉得我们应该把票集中一下。",
        "这局形势很复杂，大家冷静分析。",
    ],
    "villager": [
        "我是普通村民，没有什么特殊信息。",
        "大家冷静分析一下，不要乱投。",
        "我选择相信场上的预言家。",
        "过。",
        "我没有什么特别的信息，听大家的。",
    ],
    "seer": [
        "我是预言家，请大家相信我。",
        "我手里有验人信息，大家听我说。",
        "请大家相信我的查验结果。",
        "我是真预言家，对跳的是假的。",
        "我会用我的查验帮助好人阵营。",
    ],
    "witch": [
        "我是好人，大家可以信任我。",
        "我手里有重要信息，但现在不方便说。",
        "过。",
        "我觉得场上有问题，但需要再观察。",
        "我是神职，请大家保护我。",
    ],
    "hunter": [
        "我是猎人，狼人不要点我。",
        "我有枪，死了会带走一个。",
        "我是好人牌，大家可以相信我。",
        "过。",
        "我觉得场上形势还需要观察。",
    ],
}


class LLMService:
    """LLM service with multi-provider support, retry mechanism, and fallback."""

    def __init__(self):
        self.use_mock = settings.LLM_USE_MOCK
        self._clients: dict[str, OpenAI] = {}
        self._last_call_time: float = 0  # Track last API call time

        # Initialize clients for all configured providers
        for name, provider in settings.get_all_providers().items():
            if provider.is_valid():
                try:
                    client = OpenAI(
                        api_key=provider.api_key,
                        base_url=provider.base_url if provider.base_url else None,
                        default_headers={"User-Agent": CUSTOM_USER_AGENT},
                        timeout=120.0,  # 120 seconds timeout
                    )
                    self._clients[name] = client
                    logger.info(f"Initialized LLM client for provider: {name} (model: {provider.model})")
                except Exception as e:
                    logger.error(f"Failed to initialize client for provider {name}: {e}")

        if not self._clients and not self.use_mock:
            logger.warning("No LLM providers configured - using mock mode")
            self.use_mock = True

    def _wait_for_rate_limit(self):
        """Wait if needed to avoid calling API too frequently."""
        elapsed = time.time() - self._last_call_time
        if elapsed < CALL_INTERVAL:
            wait_time = CALL_INTERVAL - elapsed
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s before next call")
            time.sleep(wait_time)

    def _get_client_for_player(self, seat_id: int) -> tuple[Optional[OpenAI], Optional[AIProviderConfig]]:
        """Get the appropriate client and config for a player."""
        provider = settings.get_provider_for_player(seat_id)
        if provider and provider.name in self._clients:
            return self._clients[provider.name], provider

        # Fallback to default
        if "default" in self._clients:
            return self._clients["default"], settings.get_provider("default")

        # Try any available client
        for name, client in self._clients.items():
            provider = settings.get_provider(name)
            if provider:
                return client, provider

        return None, None

    def _call_llm(
        self,
        client: OpenAI,
        provider: AIProviderConfig,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """Make actual LLM API call."""
        # Wait for rate limit before making call
        self._wait_for_rate_limit()

        # Build request params - don't set max_tokens to let API use default
        request_params = {
            "model": provider.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": provider.temperature,
        }

        response = client.chat.completions.create(**request_params)

        # Update last call time after successful call
        self._last_call_time = time.time()

        # Safely extract content from response with try-except
        try:
            if response is None:
                raise ValueError("API returned None response")

            if response.choices is None or len(response.choices) == 0:
                raise ValueError("API returned empty or None choices")

            choice = response.choices[0]
            if choice is None:
                raise ValueError("API returned None choice")

            message = choice.message
            if message is None:
                raise ValueError("API returned None message")

            content = message.content
            if content is None:
                raise ValueError("API returned None content")

            logger.debug(f"LLM raw response from {provider.name}: {content}")
            return content
        except (TypeError, AttributeError) as e:
            logger.error(f"Error extracting response: {e}, response={response}")
            raise ValueError(f"Failed to extract content: {e}")

    def _parse_response(self, raw_response: str, provider_name: str = "") -> LLMResponse:
        """Parse LLM response JSON."""
        try:
            # Clean markdown code blocks if present
            cleaned_response = raw_response.strip()

            # Remove markdown code block wrapper (```json ... ``` or ``` ... ```)
            if cleaned_response.startswith("```"):
                # Find the first newline after opening ```
                first_newline = cleaned_response.find("\n")
                if first_newline != -1:
                    # Remove opening ``` and optional language identifier
                    cleaned_response = cleaned_response[first_newline + 1:]

                # Remove closing ```
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]

                cleaned_response = cleaned_response.strip()

            data = json.loads(cleaned_response)
            # Use 'or' to handle both missing keys and null values
            thought = data.get("thought") or ""
            speak = data.get("speak") or "过。"
            return LLMResponse(
                thought=thought,
                speak=speak,
                action_target=data.get("action_target"),
                raw_response=raw_response,
                is_fallback=False,
                provider_name=provider_name,
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.error(f"Original response: {raw_response[:200]}...")
            raise ValueError(f"Invalid JSON response: {raw_response[:200]}")

    def _get_fallback_response(
        self, player: "Player", action_type: str, targets: list[int] = None
    ) -> LLMResponse:
        """Generate fallback response when LLM fails."""
        role = player.role.value
        speeches = FALLBACK_SPEECHES.get(role, FALLBACK_SPEECHES["villager"])
        speak = random.choice(speeches)

        # Determine action target for non-speech actions
        action_target = None
        if action_type in ["vote", "kill", "verify", "shoot"] and targets:
            action_target = random.choice(targets)
        elif action_type in ["witch_save", "witch_poison"]:
            # 50% chance to use potion
            if random.random() < 0.5 and targets:
                action_target = targets[0] if action_type == "witch_save" else random.choice(targets)
            else:
                action_target = 0  # Skip

        return LLMResponse(
            thought="（AI回退模式）",
            speak=speak if action_type == "speech" else "",
            action_target=action_target,
            raw_response="",
            is_fallback=True,
            provider_name="fallback",
        )

    def generate_response(
        self,
        player: "Player",
        game: "Game",
        action_type: str,
        targets: list[int] = None,
    ) -> LLMResponse:
        """
        Generate AI response with retry and fallback.

        Args:
            player: The AI player
            game: Current game state
            action_type: Type of action (speech, vote, kill, verify, etc.)
            targets: Available target seat IDs for actions

        Returns:
            LLMResponse with thought, speak, and action_target
        """
        # Use mock mode if configured
        if self.use_mock:
            logger.info(f"Using mock response for player {player.seat_id}")
            return self._get_fallback_response(player, action_type, targets)

        # Get client for this player
        client, provider = self._get_client_for_player(player.seat_id)
        if not client or not provider:
            logger.warning(f"No LLM client available for player {player.seat_id}, using fallback")
            return self._get_fallback_response(player, action_type, targets)

        # Build prompts
        system_prompt = build_system_prompt(player, game)
        context_prompt = build_context_prompt(player, game, action_type)

        # Add wolf strategy for werewolves
        if player.role.value == "werewolf":
            strategy = build_wolf_strategy_prompt(player, game)
            if strategy:
                context_prompt = strategy + "\n" + context_prompt

        # Try with retries and exponential backoff
        last_error = None
        max_retries = max(provider.max_retries, 4)  # At least 4 retries for rate limiting

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"LLM call attempt {attempt + 1} for player {player.seat_id} "
                    f"using provider {provider.name} (model: {provider.model})"
                )

                raw_response = self._call_llm(client, provider, system_prompt, context_prompt)
                response = self._parse_response(raw_response, provider.name)

                # Validate action_target if needed
                if action_type in ["vote", "kill", "verify", "shoot"]:
                    if response.action_target is not None and targets:
                        if response.action_target not in targets and response.action_target != 0:
                            logger.warning(
                                f"Invalid target {response.action_target}, expected one of {targets}"
                            )
                            response.action_target = random.choice(targets)

                # Safe logging with None check for speak
                speak_preview = (response.speak or "")[:50]
                logger.info(
                    f"LLM response for player {player.seat_id} from {provider.name}: "
                    f"{speak_preview}..."
                )
                return response

            except Exception as e:
                last_error = e
                logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}")

                # Apply linear backoff for rate limiting (403 errors)
                # First retry: 60s, then add 60s each time, max 180s
                if "403" in str(e) or "blocked" in str(e).lower() or "rate" in str(e).lower():
                    delay = min(INITIAL_RETRY_DELAY + (BACKOFF_INCREMENT * attempt), MAX_RETRY_DELAY)
                    logger.info(f"Rate limited, waiting {delay}s before retry...")
                    time.sleep(delay)
                elif attempt < max_retries - 1:
                    # Longer delay for truncation errors
                    time.sleep(5)

        # All retries failed, use fallback
        logger.error(f"All LLM retries failed for player {player.seat_id}: {last_error}")
        return self._get_fallback_response(player, action_type, targets)

    # ==================== Convenience Methods ====================

    def generate_speech(self, player: "Player", game: "Game") -> str:
        """Generate speech for an AI player."""
        response = self.generate_response(player, game, "speech")
        return response.speak

    def decide_kill_target(
        self, player: "Player", game: "Game", targets: list[int]
    ) -> int:
        """Decide who to kill as werewolf."""
        response = self.generate_response(player, game, "kill", targets)
        return response.action_target if response.action_target else random.choice(targets)

    def decide_verify_target(
        self, player: "Player", game: "Game", targets: list[int]
    ) -> int:
        """Decide who to verify as seer."""
        response = self.generate_response(player, game, "verify", targets)
        return response.action_target if response.action_target else random.choice(targets)

    def decide_witch_action(self, player: "Player", game: "Game") -> dict:
        """Decide witch action (save/poison)."""
        result = {"save": False, "poison_target": None}

        # First check if should save
        if player.has_save_potion and game.night_kill_target:
            response = self.generate_response(
                player, game, "witch_save", [game.night_kill_target, 0]
            )
            if response.action_target == game.night_kill_target:
                result["save"] = True
                return result  # Can't use both in same night

        # Then check if should poison
        if player.has_poison_potion:
            alive_others = [
                p.seat_id for p in game.get_alive_players()
                if p.seat_id != player.seat_id
            ]
            if alive_others:
                response = self.generate_response(
                    player, game, "witch_poison", alive_others + [0]
                )
                if response.action_target and response.action_target != 0:
                    result["poison_target"] = response.action_target

        return result

    def decide_vote_target(
        self, player: "Player", game: "Game", targets: list[int]
    ) -> int:
        """Decide who to vote for."""
        response = self.generate_response(player, game, "vote", targets + [0])
        return response.action_target if response.action_target is not None else random.choice(targets)

    def decide_shoot_target(
        self, player: "Player", game: "Game", targets: list[int]
    ) -> Optional[int]:
        """Decide who to shoot as hunter."""
        response = self.generate_response(player, game, "shoot", targets + [0])
        if response.action_target and response.action_target != 0:
            return response.action_target
        return None

    # Legacy method for compatibility
    def generate_player_action(self, system_prompt: str, context: str) -> dict:
        """Legacy method - returns mock decision data."""
        return {
            "thought": "我是AI，正在思考中...",
            "speak": "我是AI，以后再说。",
            "action_target": None,
        }
