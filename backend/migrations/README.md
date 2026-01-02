# 数据库迁移历史

本目录包含手动SQL迁移文件，用于数据库schema变更。

## 迁移清单

| 版本 | 文件名 | 描述 | 创建日期 | 状态 |
|-----|--------|------|---------|------|
| 001 | `001_add_game_mode_fields.sql` | 添加游戏模式字段 (game_mode, wolf_king_variant) | 2025-XX-XX | ✅ 已执行 |
| 002 | `002_add_room_indexes.sql` | 优化房间查询索引 (status, created_at) | 2026-01-02 | ⏳ 待执行 |

## 手动迁移执行

### 执行步骤

1. **备份数据库**
   ```bash
   ./scripts/backup_db.sh
   ```

2. **执行迁移SQL**
   ```bash
   sqlite3 data/werewolf.db < migrations/XXX_description.sql
   ```

3. **验证迁移**
   ```bash
   # 检查索引是否创建
   sqlite3 data/werewolf.db "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='rooms';"

   # 验证数据库完整性
   sqlite3 data/werewolf.db "PRAGMA integrity_check;"
   ```

4. **更新本README**
   - 标记迁移状态为 ✅ 已执行
   - 记录执行日期

### 生产环境执行

**⚠️ 警告**: 在生产环境执行迁移前：

1. **选择低峰期时间窗口** (建议凌晨2:00-3:00)
2. **提前通知用户维护时间**
3. **完整备份数据库**
4. **在测试环境验证迁移**
5. **准备回滚方案**

### 执行示例

```bash
# 1. 备份
cd /path/to/werewolf/backend
./scripts/backup_db.sh

# 2. 执行迁移 002
sqlite3 data/werewolf.db < migrations/002_add_room_indexes.sql

# 3. 验证
sqlite3 data/werewolf.db "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='rooms';"

# 预期输出:
# idx_rooms_status
# idx_rooms_created_at

# 4. 重启服务 (如需要)
# docker-compose restart backend
```

## 迁移回滚

每个迁移文件顶部注释中包含回滚SQL语句。

### 回滚示例 (002)

```bash
sqlite3 data/werewolf.db <<EOF
DROP INDEX IF EXISTS idx_rooms_status;
DROP INDEX IF EXISTS idx_rooms_created_at;
EOF
```

## Alembic 自动迁移

对于新的schema变更，推荐使用Alembic自动迁移工具:

```bash
# 创建迁移
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

Alembic迁移文件位于: `alembic/versions/`

## 迁移命名规范

格式: `{version}_{description}.sql`

- **version**: 三位数字，递增 (001, 002, 003, ...)
- **description**: 简短描述，使用下划线分隔单词

示例:
- `001_add_game_mode_fields.sql`
- `002_add_room_indexes.sql`
- `003_create_statistics_table.sql`

## 迁移文件模板

```sql
-- Migration XXX: Brief description
-- Database: SQLite
-- Created: YYYY-MM-DD
-- Purpose: Detailed explanation of what this migration does
--
-- Background:
--   Context and reason for this migration
--
-- Expected Impact:
--   - Performance improvement: XX%
--   - Storage overhead: XX%
--
-- Rollback:
--   SQL commands to rollback this migration

-- Migration SQL here
CREATE INDEX ...

-- Verification query
SELECT ...
```

## 注意事项

1. **幂等性**: 使用 `IF NOT EXISTS` / `IF EXISTS` 确保可重复执行
2. **向后兼容**: 避免删除字段，使用deprecation策略
3. **数据迁移**: 大数据量迁移需分批处理
4. **索引创建**: 大表索引创建可能耗时，选择低峰期
5. **文档**: 每个迁移必须包含详细注释和回滚方案

## 迁移检查清单

执行迁移前确认:

- [ ] 已阅读迁移SQL文件
- [ ] 已在测试环境验证
- [ ] 已备份生产数据库
- [ ] 已准备回滚方案
- [ ] 已通知相关人员
- [ ] 已选择合适的维护窗口
- [ ] 已测试应用重启

## 常见问题

### Q: 如何查看已执行的迁移？

A: 手动SQL迁移需要在本README中手动记录。Alembic迁移可通过 `alembic current` 查看。

### Q: 迁移执行失败怎么办？

A:
1. 检查错误信息
2. 使用备份恢复数据库: `./scripts/restore_db.sh`
3. 修复迁移SQL
4. 重新执行

### Q: 能否跳过某个迁移？

A: 不建议。如必须跳过，需确保:
- 了解跳过的影响
- 手动应用必要的schema变更
- 更新迁移记录

### Q: 如何处理迁移冲突？

A:
- 手动SQL迁移: 协调版本号，避免冲突
- Alembic迁移: `alembic merge heads -m "merge heads"`

## 相关资源

- [SQLite ALTER TABLE文档](https://www.sqlite.org/lang_altertable.html)
- [Alembic使用指南](../alembic/README)
- [数据库管理文档](../README.md#数据库管理)
