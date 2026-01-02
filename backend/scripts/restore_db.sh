#!/bin/bash
# SQLite数据库恢复脚本
# 作者: Database Optimization Team
# 创建日期: 2026-01-02
# 用途: 从备份文件恢复SQLite数据库

set -e  # 遇到错误立即退出

# ============================================================
# 配置变量
# ============================================================
BACKUP_DIR="backups/database"
DATA_DIR="${DATA_DIR:-data}"
DB_FILE="werewolf.db"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_blue() {
    echo -e "${BLUE}$1${NC}"
}

# ============================================================
# 恢复流程
# ============================================================

echo -e "${GREEN}=== SQLite Database Restore ===${NC}"
echo ""

# 检查备份目录是否存在
if [ ! -d "$BACKUP_DIR" ]; then
    log_error "ERROR: Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# 检查是否有可用备份
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "*.db" -type f 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -eq 0 ]; then
    log_error "ERROR: No backup files found in $BACKUP_DIR"
    exit 1
fi

# 列出可用备份
log_blue "Available backups:"
echo ""

# 使用数组存储备份文件
mapfile -t BACKUPS < <(find "$BACKUP_DIR" -name "*.db" -type f 2>/dev/null | sort -r)

# 显示备份列表
for i in "${!BACKUPS[@]}"; do
    BACKUP_FILE="${BACKUPS[$i]}"
    BACKUP_NAME=$(basename "$BACKUP_FILE")
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    BACKUP_DATE=$(stat -c %y "$BACKUP_FILE" 2>/dev/null | cut -d'.' -f1 || stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$BACKUP_FILE" 2>/dev/null)

    printf "%2d) %-40s %8s  %s\n" "$((i+1))" "$BACKUP_NAME" "$BACKUP_SIZE" "$BACKUP_DATE"
done

echo ""

# 用户选择备份
while true; do
    read -p "Enter backup number to restore (or 'q' to cancel): " BACKUP_NUM

    if [ "$BACKUP_NUM" = "q" ] || [ "$BACKUP_NUM" = "Q" ]; then
        log_warn "Restore cancelled by user"
        exit 0
    fi

    # 验证输入
    if ! [[ "$BACKUP_NUM" =~ ^[0-9]+$ ]]; then
        log_error "ERROR: Please enter a valid number"
        continue
    fi

    # 转换为数组索引（从1开始转为从0开始）
    ARRAY_INDEX=$((BACKUP_NUM - 1))

    # 检查索引是否有效
    if [ "$ARRAY_INDEX" -ge 0 ] && [ "$ARRAY_INDEX" -lt "${#BACKUPS[@]}" ]; then
        SELECTED_BACKUP="${BACKUPS[$ARRAY_INDEX]}"
        break
    else
        log_error "ERROR: Invalid backup number. Please choose 1-${#BACKUPS[@]}"
    fi
done

echo ""
log_blue "Selected backup: $(basename "$SELECTED_BACKUP")"
echo ""

# 验证选中的备份文件完整性
log_info "Verifying backup file integrity..."
if sqlite3 "$SELECTED_BACKUP" "PRAGMA integrity_check;" 2>/dev/null | grep -q "ok"; then
    log_info "✓ Backup file is valid"
else
    log_error "ERROR: Backup file is corrupted or invalid"
    exit 1
fi
echo ""

# 最终确认
log_warn "⚠️  WARNING: This will OVERWRITE the current database!"
log_warn "   Current database: $DATA_DIR/$DB_FILE"
log_warn "   Restore from: $(basename "$SELECTED_BACKUP")"
echo ""

read -p "Type 'yes' to confirm restore: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log_warn "Restore cancelled"
    exit 0
fi

echo ""

# 备份当前数据库（如果存在）
if [ -f "$DATA_DIR/$DB_FILE" ]; then
    log_info "Backing up current database..."
    CURRENT_BACKUP="$BACKUP_DIR/${DB_FILE%.db}_before_restore_$(date +%Y%m%d_%H%M%S).db"

    if cp "$DATA_DIR/$DB_FILE" "$CURRENT_BACKUP"; then
        log_info "✓ Current database backed up to: $(basename "$CURRENT_BACKUP")"
    else
        log_error "ERROR: Failed to backup current database"
        exit 1
    fi
else
    log_warn "No existing database found, skipping current backup"
fi
echo ""

# 执行恢复
log_info "Restoring database..."
if cp "$SELECTED_BACKUP" "$DATA_DIR/$DB_FILE"; then
    log_info "✓ Database file restored"
else
    log_error "ERROR: Failed to restore database"

    # 尝试恢复备份的当前数据库
    if [ -n "$CURRENT_BACKUP" ] && [ -f "$CURRENT_BACKUP" ]; then
        log_warn "Attempting to rollback..."
        cp "$CURRENT_BACKUP" "$DATA_DIR/$DB_FILE"
    fi

    exit 1
fi
echo ""

# 验证恢复后的数据库
log_info "Verifying restored database..."
if sqlite3 "$DATA_DIR/$DB_FILE" "PRAGMA integrity_check;" 2>/dev/null | grep -q "ok"; then
    log_info "✓ Restored database is valid"
else
    log_error "ERROR: Restored database integrity check failed"

    # 尝试恢复备份的当前数据库
    if [ -n "$CURRENT_BACKUP" ] && [ -f "$CURRENT_BACKUP" ]; then
        log_warn "Rolling back to previous database..."
        cp "$CURRENT_BACKUP" "$DATA_DIR/$DB_FILE"
    fi

    exit 1
fi
echo ""

# 成功
log_info "=== Database restored successfully ==="
log_warn ""
log_warn "⚠️  IMPORTANT: Please restart the application to apply changes"
log_warn ""

exit 0
