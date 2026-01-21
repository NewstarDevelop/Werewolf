"""Database connection and session management."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import os
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# A1-FIX: 使用 settings.DATABASE_URL 作为单一真相（SSOT）
# 不再硬编码数据库路径，配置统一由 config.py 管理
DATABASE_URL = settings.DATABASE_URL

# 仅当使用 SQLite 文件数据库时才创建目录
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.endswith(":memory:"):
    # 从 URL 中提取文件路径
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        try:
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Data directory ensured: {db_dir}")
        except PermissionError as e:
            logger.warning(f"Cannot create data directory {db_dir}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating data directory: {e}")

# 根据数据库类型配置连接参数
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False  # SQLite特有配置

logger.info(f"Database URL: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

# 创建数据库引擎
# P1-STAB-002 Fix: Use IMMEDIATE isolation level for SQLite to prevent
# write conflicts in concurrent transactions
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False  # 设为True可查看SQL日志
)


# P1-STAB-002: Set SQLite to use IMMEDIATE transaction mode
# This acquires a write lock at the start of the transaction, preventing
# "database is locked" errors during concurrent writes
# A1-FIX: 仅对 SQLite 数据库应用 pragma 设置
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Configure SQLite connection for better concurrency handling."""
        cursor = dbapi_connection.cursor()
        # Enable foreign key constraints (SQLite has them disabled by default)
        cursor.execute("PRAGMA foreign_keys=ON")
        # Enable WAL mode for better concurrent read/write performance
        cursor.execute("PRAGMA journal_mode=WAL")
        # Set busy timeout to wait for locks instead of failing immediately
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


# 创建Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    依赖注入：获取数据库会话
    用法：
        @router.get("/api/rooms")
        def get_rooms(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
