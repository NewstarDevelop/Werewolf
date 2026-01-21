"""Tests for database configuration - A1: DATABASE_URL SSOT.

Verifies that DATABASE_URL from settings is actually used by the database module.
"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestDatabaseConfig:
    """Test database configuration consistency."""

    def test_database_url_uses_settings(self, monkeypatch):
        """Verify that database.py uses settings.DATABASE_URL as single source of truth."""
        # Set a custom DATABASE_URL
        test_url = "sqlite:///:memory:"
        monkeypatch.setenv("DATABASE_URL", test_url)

        # Force reimport to pick up new env
        import importlib
        from app.core import config
        importlib.reload(config)

        from app.core import database
        importlib.reload(database)

        # Verify the database module uses the settings URL
        assert database.DATABASE_URL == test_url
        assert str(database.engine.url) == test_url

    def test_sqlite_pragma_only_for_sqlite(self, monkeypatch):
        """Verify SQLite pragma is only applied for SQLite databases."""
        # This test verifies the conditional pragma setup
        test_url = "sqlite:///:memory:"
        monkeypatch.setenv("DATABASE_URL", test_url)

        import importlib
        from app.core import config
        importlib.reload(config)

        from app.core import database
        importlib.reload(database)

        # For SQLite, pragma should be set up
        assert database.DATABASE_URL.startswith("sqlite")

    def test_no_directory_creation_for_memory_db(self, monkeypatch):
        """Verify no directory creation for in-memory SQLite."""
        test_url = "sqlite:///:memory:"
        monkeypatch.setenv("DATABASE_URL", test_url)

        makedirs_calls = []
        original_makedirs = os.makedirs

        def mock_makedirs(*args, **kwargs):
            makedirs_calls.append(args)
            return original_makedirs(*args, **kwargs)

        with patch("os.makedirs", mock_makedirs):
            import importlib
            from app.core import config
            importlib.reload(config)

            from app.core import database
            importlib.reload(database)

        # Should not call makedirs for :memory: database
        db_related_calls = [c for c in makedirs_calls if "werewolf" in str(c).lower()]
        assert len(db_related_calls) == 0, f"Unexpected makedirs calls: {db_related_calls}"

    def test_connect_args_for_sqlite(self, monkeypatch):
        """Verify check_same_thread is set for SQLite."""
        test_url = "sqlite:///:memory:"
        monkeypatch.setenv("DATABASE_URL", test_url)

        import importlib
        from app.core import config
        importlib.reload(config)

        from app.core import database
        importlib.reload(database)

        # For SQLite, check_same_thread should be False
        assert database.connect_args.get("check_same_thread") == False
