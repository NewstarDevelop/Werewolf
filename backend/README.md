# Werewolf AI Game - Backend

狼人杀 AI 游戏后端服务 - 基于 FastAPI + SQLAlchemy

## 技术栈

- **框架**: FastAPI 0.104+
- **数据库**: SQLite (支持切换至 PostgreSQL)
- **ORM**: SQLAlchemy 2.0+
- **迁移工具**: Alembic
- **认证**: JWT + OAuth2
- **AI模型**: OpenAI API (支持多Provider)

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写配置:

```bash
cp ../.env.example ../.env
```

关键配置项:
- `OPENAI_API_KEY`: OpenAI API密钥
- `DATABASE_URL`: 数据库连接URL (可选)
- `JWT_SECRET_KEY`: JWT密钥

### 3. 初始化数据库

```bash
python -m app.init_db
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看API文档

## 数据库管理

### 数据库架构

本项目使用SQLite作为默认数据库（生产环境可切换至PostgreSQL）。

**核心表结构**:

```
用户认证系统:
  users (用户主表)
  ├── oauth_accounts (OAuth关联)
  ├── refresh_tokens (会话管理)
  ├── password_reset_tokens (密码重置)
  └── oauth_states (OAuth CSRF防护)

游戏系统:
  rooms (游戏房间)
  ├── room_players (房间玩家)
  └── game_sessions (游戏历史)
      └── game_participants (玩家参与记录)
```

### 数据库迁移 (Alembic)

**创建新迁移**:
```bash
# 自动生成迁移
alembic revision --autogenerate -m "description"

# 手动创建迁移
alembic revision -m "description"
```

**应用迁移**:
```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade <revision_id>
```

**回滚迁移**:
```bash
# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>
```

**查看迁移历史**:
```bash
alembic history
alembic current
```

### 手动SQL迁移

手动SQL迁移文件位于 `migrations/` 目录:

```bash
# 执行手动迁移
sqlite3 data/werewolf.db < migrations/002_add_room_indexes.sql
```

**已有迁移**:
- `001_add_game_mode_fields.sql`: 添加游戏模式字段
- `002_add_room_indexes.sql`: 优化房间查询索引

### 数据库备份

**手动备份**:
```bash
./scripts/backup_db.sh
```

**自动备份**:

备份脚本已配置，建议通过crontab设置定时任务:

```bash
# 每天凌晨2点执行备份
0 2 * * * cd /path/to/werewolf/backend && ./scripts/backup_db.sh >> backups/backup.log 2>&1
```

**备份策略**:
- **位置**: `backups/database/`
- **命名**: `werewolf_YYYYMMDD_HHMMSS.db`
- **保留期**: 最近7天
- **完整性**: 自动验证

### 数据库恢复

```bash
./scripts/restore_db.sh
```

按提示选择要恢复的备份文件，脚本会:
1. 显示所有可用备份
2. 验证备份文件完整性
3. 备份当前数据库
4. 执行恢复
5. 验证恢复结果

**恢复后记得重启服务！**

### 数据库优化

**已优化索引**:
- `rooms.status`: 房间状态查询 ✅
- `rooms.created_at`: 房间列表排序 ✅
- `users.email`: 登录查询 ✅
- `game_participants.user_id + is_winner`: 统计查询 ✅
- `oauth_accounts.provider + provider_user_id`: OAuth查询 ✅

**性能基准** (100条记录):
- 房间列表查询: < 50ms
- 用户统计查询: < 100ms
- OAuth登录查询: < 30ms

**并发优化**:
- ✅ WAL模式 (Write-Ahead Logging)
- ✅ 行级锁 (`SELECT FOR UPDATE`)
- ✅ 重试机制 (指数退避)
- ✅ 忙等待超时 (5秒)

## 项目结构

```
backend/
├── alembic/              # Alembic迁移配置
│   ├── versions/         # 迁移脚本
│   ├── env.py            # 环境配置
│   └── README            # 使用说明
├── app/
│   ├── api/              # API路由
│   │   ├── endpoints/    # 端点实现
│   │   └── dependencies.py
│   ├── core/             # 核心配置
│   │   ├── config.py     # 应用配置
│   │   ├── database.py   # 数据库连接
│   │   ├── auth.py       # 认证逻辑
│   │   └── security.py   # 安全工具
│   ├── models/           # 数据库模型
│   │   ├── base.py       # Base模型
│   │   ├── user.py       # 用户模型
│   │   ├── room.py       # 房间模型
│   │   ├── game.py       # 游戏模型
│   │   └── game_history.py # 历史记录
│   ├── schemas/          # Pydantic模式
│   ├── services/         # 业务逻辑
│   │   ├── game_engine.py    # 游戏引擎
│   │   ├── room_manager.py   # 房间管理
│   │   ├── llm.py            # LLM调用
│   │   └── oauth.py          # OAuth服务
│   ├── i18n/             # 国际化
│   └── main.py           # 应用入口
├── migrations/           # 手动SQL迁移
├── scripts/              # 工具脚本
│   ├── backup_db.sh      # 数据库备份
│   └── restore_db.sh     # 数据库恢复
├── data/                 # 数据存储
│   └── werewolf.db       # SQLite数据库
├── backups/              # 备份目录
│   └── database/         # 数据库备份
├── alembic.ini           # Alembic配置
├── requirements.txt      # Python依赖
└── README.md             # 本文档
```

## API文档

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发指南

### 添加新API端点

1. 在 `app/schemas/` 中定义请求/响应模式
2. 在 `app/api/endpoints/` 中实现端点逻辑
3. 在 `app/api/api.py` 中注册路由
4. 更新API文档

### 添加新数据库表

1. 在 `app/models/` 中定义模型
2. 在 `app/models/__init__.py` 中导入
3. 生成迁移: `alembic revision --autogenerate -m "add new table"`
4. 检查并应用迁移: `alembic upgrade head`

### 代码规范

- 使用 Black 格式化代码
- 遵循 PEP 8 规范
- 添加类型注解
- 编写文档字符串

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 生成覆盖率报告
pytest --cov=app tests/
```

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t werewolf-backend .

# 运行容器
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  werewolf-backend
```

### 生产环境建议

1. **使用PostgreSQL**: 修改 `DATABASE_URL`
2. **使用Gunicorn**: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`
3. **配置HTTPS**: 使用Nginx反向代理
4. **启用日志**: 配置日志级别和输出
5. **设置监控**: 使用Prometheus + Grafana
6. **定期备份**: 配置自动备份任务

## 故障排查

### 数据库锁定错误

```
sqlite3.OperationalError: database is locked
```

**解决方案**:
- 已启用WAL模式和重试机制
- 如持续出现，考虑迁移到PostgreSQL

### 迁移冲突

```
FAILED: Multiple head revisions are present
```

**解决方案**:
```bash
alembic merge heads -m "merge heads"
alembic upgrade head
```

### 备份恢复失败

**检查**:
1. 备份文件完整性: `sqlite3 backup.db "PRAGMA integrity_check;"`
2. 文件权限
3. 磁盘空间

## 贡献指南

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/xxx`
3. 提交更改: `git commit -m 'Add xxx'`
4. 推送分支: `git push origin feature/xxx`
5. 提交 Pull Request

## 许可证

MIT License

## 联系方式

- GitHub Issues: [项目地址]/issues
- 文档: [项目地址]/wiki
