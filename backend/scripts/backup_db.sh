#!/bin/bash
# SQLite数据库自动备份脚本
# 作者: Database Optimization Team
# 创建日期: 2026-01-02
# 用途: 定期备份SQLite数据库，保留最近7天的备份

set -e  # 遇到错误立即退出

# ============================================================
# 配置变量
# ============================================================
DATA_DIR="${DATA_DIR:-data}"
BACKUP_DIR="backups/database"
DB_FILE="werewolf.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================
# 函数定义
# ============================================================

log_info() {
    echo -e "${GREEN}$1${NC}"
}

log_warn() {
    echo -e "${YELLOW}$1${NC}"
}

log_error() {
    echo -e "${RED}$1${NC}"
}

# ============================================================
# 备份流程
# ============================================================

echo -e "${GREEN}=== SQLite Database Backup ===${NC}"
echo "Time: $(date)"
echo ""

# 检查数据库文件是否存在
if [ ! -f "$DATA_DIR/$DB_FILE" ]; then
    log_error "ERROR: Database file not found: $DATA_DIR/$DB_FILE"
    exit 1
fi

# 创建备份目录
mkdir -p "$BACKUP_DIR"
log_info "Backup directory: $BACKUP_DIR"
echo ""

# WAL模式下执行checkpoint（确保所有数据写入主库）
log_info "Executing WAL checkpoint..."
if sqlite3 "$DATA_DIR/$DB_FILE" "PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null; then
    log_info "✓ WAL checkpoint completed"
else
    log_warn "WARNING: WAL checkpoint failed (database may not be in WAL mode)"
fi
echo ""

# 执行备份
BACKUP_FILE="$BACKUP_DIR/${DB_FILE%.db}_$TIMESTAMP.db"
log_info "Backing up to: $BACKUP_FILE"

if cp "$DATA_DIR/$DB_FILE" "$BACKUP_FILE"; then
    log_info "✓ File copied successfully"
else
    log_error "ERROR: Failed to copy database file"
    exit 1
fi
echo ""

# 验证备份文件完整性
log_info "Verifying backup integrity..."
if sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" 2>/dev/null | grep -q "ok"; then
    log_info "✓ Backup verified successfully"
else
    log_error "ERROR: Backup integrity check failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi
echo ""

# 获取备份文件大小
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log_info "✓ Backup completed: $BACKUP_SIZE"
echo ""

# 清理旧备份（保留最近N天）
log_info "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."
DELETED_COUNT=0

# 查找并删除超过保留期的备份
while IFS= read -r old_backup; do
    if [ -n "$old_backup" ]; then
        rm -f "$old_backup"
        ((DELETED_COUNT++))
    fi
done < <(find "$BACKUP_DIR" -name "${DB_FILE%.db}_*.db" -mtime +$RETENTION_DAYS 2>/dev/null)

if [ $DELETED_COUNT -gt 0 ]; then
    log_info "✓ Deleted $DELETED_COUNT old backup(s)"
fi

REMAINING=$(find "$BACKUP_DIR" -name "${DB_FILE%.db}_*.db" 2>/dev/null | wc -l)
log_info "✓ Cleanup completed. Remaining backups: $REMAINING"
echo ""

# 生成备份报告
log_info "Backup Report:"
echo "  Database: $DATA_DIR/$DB_FILE"
echo "  Backup File: $BACKUP_FILE"
echo "  Size: $BACKUP_SIZE"
echo "  Timestamp: $TIMESTAMP"
echo "  Total Backups: $REMAINING"
echo ""

log_info "=== Backup completed successfully ==="
exit 0
