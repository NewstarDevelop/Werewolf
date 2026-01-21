"""Alembic migration environment configuration."""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool

from alembic import context

# Import Base and all models to ensure they are registered
from app.models.base import Base
from app.models import user, room, game_history, notification, notification_broadcast  # Import all model modules

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def get_database_url() -> str:
    """Get database URL from environment or config.

    Priority:
    1. DATABASE_URL environment variable
    2. alembic.ini sqlalchemy.url
    3. Default SQLite path
    """
    # Check environment variable first (production/docker)
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Ensure we use sync driver for Alembic
        if "+aiosqlite" in db_url:
            db_url = db_url.replace("+aiosqlite", "")
        if "+asyncpg" in db_url:
            db_url = db_url.replace("+asyncpg", "")
        return db_url

    # Fall back to alembic.ini
    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url:
        return ini_url

    # Default for local development
    data_dir = os.getenv("DATA_DIR", "data")
    return f"sqlite:///{data_dir}/werewolf.db"

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Uses DATABASE_URL from environment for consistency with application.
    """
    url = get_database_url()

    # Create engine with appropriate settings
    if url.startswith("sqlite"):
        connectable = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=pool.StaticPool,
        )
    else:
        connectable = create_engine(
            url,
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
