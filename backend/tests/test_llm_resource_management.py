"""Tests for LLM client resource management - A7 fix.

Verifies that:
1. LLMService.close() properly closes all clients
2. Context manager pattern works correctly
3. Double-close is safe (idempotent)
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestLLMServiceResourceManagement:
    """Test LLM service resource cleanup."""

    @pytest.mark.asyncio
    async def test_close_method_closes_all_clients(self):
        """close() should close all AsyncOpenAI clients."""
        with patch('app.services.llm.settings') as mock_settings:
            mock_settings.LLM_USE_MOCK = False
            mock_settings.get_all_providers.return_value = {}

            from app.services.llm import LLMService

            service = LLMService()

            # Manually add mock clients
            mock_client1 = AsyncMock()
            mock_client2 = AsyncMock()
            service._clients = {"provider1": mock_client1, "provider2": mock_client2}

            await service.close()

            # Both clients should have close() called
            mock_client1.close.assert_called_once()
            mock_client2.close.assert_called_once()

            # Clients dict should be cleared
            assert len(service._clients) == 0
            assert service._closed is True

    @pytest.mark.asyncio
    async def test_close_is_idempotent(self):
        """Calling close() multiple times should be safe."""
        with patch('app.services.llm.settings') as mock_settings:
            mock_settings.LLM_USE_MOCK = False
            mock_settings.get_all_providers.return_value = {}

            from app.services.llm import LLMService

            service = LLMService()

            mock_client = AsyncMock()
            service._clients = {"provider1": mock_client}

            # First close
            await service.close()
            assert mock_client.close.call_count == 1

            # Second close should not call close again
            await service.close()
            assert mock_client.close.call_count == 1

    @pytest.mark.asyncio
    async def test_context_manager_closes_on_exit(self):
        """Async context manager should close on exit."""
        with patch('app.services.llm.settings') as mock_settings:
            mock_settings.LLM_USE_MOCK = False
            mock_settings.get_all_providers.return_value = {}

            from app.services.llm import LLMService

            mock_client = AsyncMock()

            async with LLMService() as service:
                service._clients = {"provider1": mock_client}
                assert service._closed is False

            # After exiting context, should be closed
            mock_client.close.assert_called_once()
            assert service._closed is True

    @pytest.mark.asyncio
    async def test_close_handles_client_errors(self):
        """close() should handle errors from individual clients gracefully."""
        with patch('app.services.llm.settings') as mock_settings:
            mock_settings.LLM_USE_MOCK = False
            mock_settings.get_all_providers.return_value = {}

            from app.services.llm import LLMService

            service = LLMService()

            # One client raises error, one succeeds
            mock_client1 = AsyncMock()
            mock_client1.close.side_effect = Exception("Connection error")

            mock_client2 = AsyncMock()

            service._clients = {"failing": mock_client1, "working": mock_client2}

            # Should not raise, just log warning
            await service.close()

            # Both clients should have close() attempted
            mock_client1.close.assert_called_once()
            mock_client2.close.assert_called_once()

            # Service should still be marked as closed
            assert service._closed is True


class TestGameEngineResourceManagement:
    """Test GameEngine resource cleanup."""

    @pytest.mark.asyncio
    async def test_game_engine_close(self):
        """GameEngine.close() should close LLM service."""
        with patch('app.services.game_engine.LLMService') as MockLLM:
            mock_llm_instance = AsyncMock()
            MockLLM.return_value = mock_llm_instance

            from app.services.game_engine import GameEngine

            engine = GameEngine()
            await engine.close()

            mock_llm_instance.close.assert_called_once()
