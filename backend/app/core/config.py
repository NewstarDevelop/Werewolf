"""Application configuration with multi-AI provider support."""
import os
import json
import logging
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AIProviderConfig:
    """Configuration for a single AI provider."""
    name: str
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-4o-mini"
    max_retries: int = 2
    temperature: float = 0.7
    max_tokens: int = 500

    @classmethod
    def from_env(cls, prefix: str, name: str) -> "AIProviderConfig":
        """Create config from environment variables with given prefix."""
        return cls(
            name=name,
            api_key=os.getenv(f"{prefix}_API_KEY", ""),
            base_url=os.getenv(f"{prefix}_BASE_URL") or None,
            model=os.getenv(f"{prefix}_MODEL", "gpt-4o-mini"),
            max_retries=int(os.getenv(f"{prefix}_MAX_RETRIES", "2")),
            temperature=float(os.getenv(f"{prefix}_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv(f"{prefix}_MAX_TOKENS", "500")),
        )

    def is_valid(self) -> bool:
        """Check if this provider has valid configuration."""
        return bool(self.api_key)


@dataclass
class AIPlayerConfig:
    """Configuration for AI player to provider mapping."""
    seat_id: int
    provider_name: str  # References AIProviderConfig.name


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Default OpenAI configuration (backward compatible)
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL") or None

        # Default LLM settings
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
        self.LLM_USE_MOCK: bool = os.getenv("LLM_USE_MOCK", "false").lower() == "true"

        # Application settings
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

        # Multi-provider configuration
        self._providers: dict[str, AIProviderConfig] = {}
        self._player_mappings: dict[int, str] = {}  # seat_id -> provider_name

        self._load_providers()
        self._load_player_mappings()
        self._log_configuration_summary()

    def _load_providers(self):
        """Load AI provider configurations from environment.

        This method only loads provider definitions, does not establish player mappings.
        Player mappings are handled separately in _load_player_mappings().
        """
        # Default provider (OpenAI)
        default_provider = AIProviderConfig(
            name="default",
            api_key=self.OPENAI_API_KEY,
            base_url=self.OPENAI_BASE_URL,
            model=self.LLM_MODEL,
            max_retries=self.LLM_MAX_RETRIES,
        )
        if default_provider.is_valid():
            self._providers["default"] = default_provider

        # Load named providers: OPENAI_*, ANTHROPIC_*, DEEPSEEK_*, etc.
        named_providers = ["OPENAI", "ANTHROPIC", "DEEPSEEK", "MOONSHOT", "QWEN", "GLM", "DOUBAO", "MINIMAX"]
        for provider_name in named_providers:
            api_key = os.getenv(f"{provider_name}_API_KEY")
            if api_key:
                provider = AIProviderConfig(
                    name=provider_name.lower(),
                    api_key=api_key,
                    base_url=os.getenv(f"{provider_name}_BASE_URL") or None,
                    model=os.getenv(f"{provider_name}_MODEL", self._get_default_model(provider_name)),
                    max_retries=int(os.getenv(f"{provider_name}_MAX_RETRIES", "2")),
                    temperature=float(os.getenv(f"{provider_name}_TEMPERATURE", "0.7")),
                    max_tokens=int(os.getenv(f"{provider_name}_MAX_TOKENS", "500")),
                )
                self._providers[provider_name.lower()] = provider

        # Load additional custom providers from AI_PROVIDER_* env vars
        # Format: AI_PROVIDER_1_NAME, AI_PROVIDER_1_API_KEY, etc.
        for i in range(1, 10):  # Support up to 9 custom providers
            prefix = f"AI_PROVIDER_{i}"
            name = os.getenv(f"{prefix}_NAME")
            if name:
                provider = AIProviderConfig.from_env(prefix, name)
                if provider.is_valid():
                    self._providers[name] = provider

        # Load per-player specific providers (座位 2-9)
        # Format: AI_PLAYER_2_API_KEY, AI_PLAYER_2_MODEL, etc.
        # These create dedicated providers named "player_{seat_id}"
        # Note: Mapping is NOT established here, only provider definition is created
        for seat_id in range(2, 10):
            prefix = f"AI_PLAYER_{seat_id}"
            api_key = os.getenv(f"{prefix}_API_KEY")

            # Only create player-specific provider if API_KEY is explicitly configured
            if api_key:
                provider_name = f"player_{seat_id}"
                provider = AIProviderConfig(
                    name=provider_name,
                    api_key=api_key,
                    base_url=os.getenv(f"{prefix}_BASE_URL") or None,
                    model=os.getenv(f"{prefix}_MODEL", "gpt-4o-mini"),
                    max_retries=int(os.getenv(f"{prefix}_MAX_RETRIES", "2")),
                    temperature=float(os.getenv(f"{prefix}_TEMPERATURE", "0.7")),
                    max_tokens=int(os.getenv(f"{prefix}_MAX_TOKENS", "500")),
                )
                if provider.is_valid():
                    self._providers[provider_name] = provider

    def _get_default_model(self, provider_name: str) -> str:
        """Get default model for a provider."""
        defaults = {
            "OPENAI": "gpt-4o-mini",
            "ANTHROPIC": "claude-3-haiku-20240307",
            "DEEPSEEK": "deepseek-chat",
            "MOONSHOT": "moonshot-v1-8k",
            "QWEN": "qwen-turbo",
            "GLM": "glm-4-flash",
            "DOUBAO": "doubao-pro-4k",
            "MINIMAX": "abab6.5s-chat",
        }
        return defaults.get(provider_name, "gpt-4o-mini")

    def _load_player_mappings(self):
        """Load AI player to provider mappings with correct priority.

        Priority order (low to high, later overrides earlier):
        1. Auto-mapping for player-specific configs (player_{seat_id})
        2. JSON batch mapping (AI_PLAYER_MAPPING)
        3. Individual mapping (AI_PLAYER_{seat}_PROVIDER) - highest priority

        This ensures that explicit provider mappings always take precedence.
        """
        # Priority 1 (Lowest): Auto-map players with specific provider configs
        # If player_{seat_id} provider exists, automatically map to it
        for seat_id in range(2, 10):
            provider_name = f"player_{seat_id}"
            if provider_name in self._providers:
                self._player_mappings[seat_id] = provider_name

        # Priority 2 (Medium): JSON batch mapping
        # Format: AI_PLAYER_MAPPING={"2":"openai","3":"anthropic",...}
        mapping_json = os.getenv("AI_PLAYER_MAPPING")
        if mapping_json:
            try:
                mapping = json.loads(mapping_json)
                for seat_str, provider in mapping.items():
                    seat_id = int(seat_str)
                    if provider in self._providers:
                        self._player_mappings[seat_id] = provider
                    else:
                        logger.warning(
                            f"AI_PLAYER_MAPPING: provider '{provider}' not found for seat {seat_id}"
                        )
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse AI_PLAYER_MAPPING: {e}")

        # Priority 3 (Highest): Individual mapping per seat
        # Format: AI_PLAYER_{seat}_PROVIDER=openai
        # This overrides both auto-mapping and JSON mapping
        for seat_id in range(1, 10):
            provider = os.getenv(f"AI_PLAYER_{seat_id}_PROVIDER")
            if provider:
                if provider in self._providers:
                    self._player_mappings[seat_id] = provider
                else:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"AI_PLAYER_{seat_id}_PROVIDER: provider '{provider}' not found, "
                        f"falling back to default or auto-mapped provider"
                    )

    def get_provider(self, name: str) -> Optional[AIProviderConfig]:
        """Get provider configuration by name."""
        return self._providers.get(name)

    def get_provider_for_player(self, seat_id: int) -> Optional[AIProviderConfig]:
        """Get provider configuration for a specific player seat."""
        provider_name = self._player_mappings.get(seat_id, "default")
        return self._providers.get(provider_name) or self._providers.get("default")

    def get_all_providers(self) -> dict[str, AIProviderConfig]:
        """Get all configured providers."""
        return self._providers.copy()

    def get_player_mappings(self) -> dict[int, str]:
        """Get all player to provider mappings."""
        return self._player_mappings.copy()

    def _log_configuration_summary(self):
        """Log configuration summary for debugging."""
        logger.info(f"AI Configuration loaded: {len(self._providers)} providers configured")

        # Log all providers
        for name, provider in self._providers.items():
            logger.info(
                f"  Provider '{name}': model={provider.model}, "
                f"base_url={provider.base_url or 'default'}"
            )

        # Log player mappings
        if self._player_mappings:
            logger.info("Player to provider mappings:")
            for seat_id in sorted(self._player_mappings.keys()):
                provider_name = self._player_mappings[seat_id]
                provider = self._providers.get(provider_name)
                model_info = f" (model: {provider.model})" if provider else ""
                logger.info(f"  Seat {seat_id} -> {provider_name}{model_info}")
        else:
            logger.info("No explicit player mappings - all players use default provider")


settings = Settings()
