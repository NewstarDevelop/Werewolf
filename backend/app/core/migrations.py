"""Alembic migration runner.

用于在 Docker/FastAPI 启动阶段执行数据库 schema 迁移(方案 B)。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


def _project_root() -> Path:
    # backend/app/core/migrations.py -> backend/
    return Path(__file__).resolve().parents[2]


def _alembic_ini_path() -> Path:
    return _project_root() / "alembic.ini"


def upgrade_head() -> None:
    """执行 `alembic upgrade head` (通过 API 调用,避免依赖 shell)。"""
    disabled = os.getenv("RUN_DB_MIGRATIONS", "true").strip().lower() in {"0", "false", "no"}
    if disabled:
        logger.info("DB migrations disabled via RUN_DB_MIGRATIONS")
        return

    alembic_ini = _alembic_ini_path()
    if not alembic_ini.exists():
        raise FileNotFoundError(f"Alembic config not found: {alembic_ini}")

    cfg = Config(str(alembic_ini))
    # 防御式设置,避免 alembic.ini 被误改导致找不到版本脚本
    cfg.set_main_option("script_location", "alembic")

    logger.info("Running Alembic migrations: upgrade head")
    command.upgrade(cfg, "head")
    logger.info("Alembic migrations finished")
