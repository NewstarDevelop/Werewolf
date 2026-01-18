"""
Alembic migrations verification script.

用途:
- 在本地或 CI 中验证: create_all + alembic upgrade head 后,关键 schema 满足预期。

运行方式(在 backend 目录下):
- python -m scripts.verify_alembic_migrations
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path


def _assert_table_exists(conn: sqlite3.Connection, table_name: str) -> None:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    assert row is not None, f"missing table: {table_name}"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["DATA_DIR"] = tmpdir

        # IMPORTANT: DATA_DIR 在 app.core.database import 时读取,必须先设置环境变量再导入。
        from app.init_db import init_database
        from app.core.migrations import upgrade_head

        init_database()
        upgrade_head()

        db_path = Path(tmpdir) / "werewolf.db"
        assert db_path.exists(), f"db file not created: {db_path}"

        conn = sqlite3.connect(str(db_path))
        try:
            # users.preferences
            cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
            assert "preferences" in cols, "missing column: users.preferences"

            # alembic_version
            _assert_table_exists(conn, "alembic_version")
            version = conn.execute("SELECT version_num FROM alembic_version").fetchone()
            assert version and version[0], "alembic_version is empty"

            print(f"✅ Migrations verified successfully (head: {version[0]})")
        finally:
            conn.close()


if __name__ == "__main__":
    main()
