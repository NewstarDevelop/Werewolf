# 🐺 狼人杀

[English](./README.en.md) | [简体中文](./README.md)

一个基于 AI 的在线狼人杀游戏，支持人类玩家与多个 AI 玩家共同游戏。采用 FastAPI + React + Docker 架构，提供流畅的游戏体验和智能的 AI 对手。

**在线预览**：https://werewolf.newstardev.de （Mock 模式，未配置真实密钥）

![Game](https://img.shields.io/badge/Game-Werewolf-red)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![React](https://img.shields.io/badge/React-18.3-61dafb)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ed)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ 特性

### 核心功能
- **完整游戏流程**：支持狼人、预言家、女巫、猎人、守卫、狼王、白狼王等角色
- **AI 玩家**：基于 OpenAI GPT 的智能 AI 玩家，支持 Mock 模式测试
- **多房间系统**：支持多个房间同时进行游戏，玩家可自由创建和加入房间
- **混合对战**：支持纯真人、纯 AI、真人 + AI 混合等多种游戏模式
- **实时聊天**：游戏内实时聊天系统，记录所有玩家发言
- **AI 对局分析**：游戏结束后可查看 AI 生成的对局分析报告

### 用户系统
- **用户注册登录**：支持邮箱密码注册和登录
- **OAuth 认证**：支持 linux.do OAuth2 第三方登录
- **JWT 认证**：安全的 Token 认证体系，HttpOnly Cookie
- **个人资料**：用户头像、昵称、个人简介管理

### 技术特性
- **WebSocket 实时通信**：游戏状态实时推送，无需刷新页面
- **状态版本控制**：防止竞态条件，确保数据一致性
- **现代化 UI**：基于 shadcn/ui 的精美界面设计，纯黑主题
- **Docker 部署**：一键启动，开箱即用
- **响应式设计**：支持桌面和移动端访问
- **数据持久化**：SQLite 数据库存储用户和房间信息
- **国际化支持**：支持中英文切换

---

## 🎭 游戏角色

### 经典9人局
| 角色 | 阵营 | 能力 |
|------|------|------|
| 🐺 狼人 (×3) | 狼人阵营 | 每晚可以杀死一名玩家 |
| 👁️ 预言家 | 好人阵营 | 每晚可以查验一名玩家的身份 |
| 🧪 女巫 | 好人阵营 | 拥有解药和毒药各一瓶，同一晚使用解药后无法使用毒药 |
| 🔫 猎人 | 好人阵营 | 被淘汰时可以开枪带走一名玩家（被毒杀除外） |
| 👨‍🌾 村民 (×3) | 好人阵营 | 普通村民，无特殊能力 |

### 扩展12人局
| 角色 | 阵营 | 能力 |
|------|------|------|
| 🛡️ 守卫 | 好人阵营 | 每晚可以保护一名玩家免受狼人攻击 |
| 👑 狼王 | 狼人阵营 | 被淘汰时可以带走一名玩家 |
| ⚪ 白狼王 | 狼人阵营 | 白天可以自爆带走一名玩家 |

---

## 🚀 快速开始

### 前置要求

- Docker 和 Docker Compose
- （可选）OpenAI API Key（用于真实 AI 对手）
- （可选）linux.do OAuth 配置（用于第三方登录）

### 使用 Docker 启动

```bash
# 克隆仓库
git clone https://github.com/NewstarDevelop/Werewolf.git
cd Werewolf

# 复制环境变量模板
cp .env.example .env

# 编辑配置文件（填入API密钥等）
nano .env

# 启动服务
docker compose up
```

**访问游戏**
- 🎮 前端页面：http://localhost:8081
- 📡 后端 API：http://localhost:8082
- 📚 API 文档：http://localhost:8082/docs

### 本地开发

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

---

## 🎮 游戏玩法

### 游戏模式

#### 混合模式（真人 + AI）
1. 创建房间，等待部分玩家加入
2. 房主点击"填充AI并开始"
3. 系统自动填充剩余座位为AI
4. 例如：3个真人 + 6个AI

### 游戏流程

1. **游戏开始**：通过房间系统创建或加入游戏
2. **角色分配**：系统自动分配角色
3. **夜晚阶段**：
   - 守卫选择保护对象
   - 狼人讨论并选择击杀目标
   - 预言家查验玩家身份
   - 女巫先决策是否使用解药，再决策是否使用毒药
4. **白天阶段**：
   - 公布夜晚死亡信息
   - 死亡玩家遗言
   - 所有玩家依次发言
   - 投票淘汰可疑玩家
5. **胜利条件**：
   - 好人阵营：淘汰所有狼人
   - 狼人阵营：狼人数量 ≥ 好人数量，或屠民（所有村民死亡），或屠神（所有神职死亡）

### 操作指南

- **发言**：在白天阶段，在输入框中输入发言内容，点击"确认"
- **投票**：在投票阶段，点击玩家头像选择投票目标
- **使用技能**：在夜晚阶段，点击"技能"按钮使用角色技能

---

## 📁 项目结构

```
Werewolf/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── api/                # API 路由
│   │   │   ├── dependencies.py # 依赖注入
│   │   │   └── endpoints/
│   │   │       ├── auth.py     # 认证API
│   │   │       ├── game.py     # 游戏API
│   │   │       ├── room.py     # 房间API
│   │   │       └── users.py    # 用户API
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py       # 配置管理
│   │   │   ├── database.py     # 数据库配置
│   │   │   └── security.py     # 安全工具
│   │   ├── i18n/               # 国际化
│   │   │   ├── en.json         # 英文翻译
│   │   │   └── zh.json         # 中文翻译
│   │   ├── models/             # 数据模型
│   │   │   ├── game.py         # 游戏模型
│   │   │   ├── room.py         # 房间模型
│   │   │   └── user.py         # 用户模型
│   │   ├── schemas/            # Pydantic 模式
│   │   │   ├── auth.py         # 认证模式
│   │   │   ├── enums.py        # 枚举定义
│   │   │   └── game.py         # 游戏模式
│   │   └── services/           # 业务逻辑
│   │       ├── game_engine.py  # 游戏引擎
│   │       ├── game_analyzer.py# 对局分析
│   │       ├── llm.py          # AI 服务
│   │       ├── oauth.py        # OAuth 服务
│   │       ├── prompts.py      # AI 提示词
│   │       └── room_manager.py # 房间管理
│   ├── data/                   # 数据存储
│   ├── migrations/             # 数据库迁移
│   ├── tests/                  # 测试文件
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/        # React 组件
│   │   │   ├── game/          # 游戏相关组件
│   │   │   │   ├── ChatLog.tsx
│   │   │   │   ├── DebugPanel.tsx
│   │   │   │   ├── GameActions.tsx
│   │   │   │   ├── GameAnalysisDialog.tsx
│   │   │   │   ├── GameStatusBar.tsx
│   │   │   │   ├── PlayerCard.tsx
│   │   │   │   └── PlayerGrid.tsx
│   │   │   └── ui/            # UI 基础组件
│   │   ├── hooks/             # 自定义 Hooks
│   │   ├── pages/             # 页面组件
│   │   │   ├── auth/          # 认证页面
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   ├── RegisterPage.tsx
│   │   │   │   └── OAuthCallback.tsx
│   │   │   ├── GamePage.tsx   # 游戏页面
│   │   │   ├── ProfilePage.tsx# 个人资料
│   │   │   ├── RoomLobby.tsx  # 房间大厅
│   │   │   └── RoomWaiting.tsx# 房间等待室
│   │   ├── services/          # API 服务
│   │   │   ├── api.ts         # 游戏API
│   │   │   ├── authService.ts # 认证服务
│   │   │   └── roomApi.ts     # 房间API
│   │   └── utils/             # 工具函数
│   ├── public/
│   │   └── locales/           # 翻译文件 (zh/en)
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 🛠️ 技术栈

### 后端
- **FastAPI**：现代化的 Python Web 框架
- **SQLAlchemy**：ORM 数据库操作
- **Pydantic**：数据验证和序列化
- **OpenAI API**：AI 玩家决策引擎
- **JWT + HttpOnly Cookie**：安全认证
- **Uvicorn**：ASGI 服务器

### 前端
- **React 18**：用户界面框架
- **TypeScript**：类型安全
- **Vite**：构建工具
- **TanStack Query**：数据获取和状态管理
- **shadcn/ui**：UI 组件库
- **Tailwind CSS**：样式框架
- **React Router**：路由管理
- **i18next**：国际化
- **Recharts**：图表组件

### 基础设施
- **Docker & Docker Compose**：容器化部署
- **Nginx**：前端静态文件服务
- **SQLite**：数据持久化

---

## ⚙️ 配置说明

### 环境变量

在项目根目录创建 `.env` 文件进行配置：

```env
# OpenAI API 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# 应用配置
DEBUG=false
DEBUG_MODE=false
CORS_ORIGINS=http://localhost:8081,http://127.0.0.1:8081

# JWT 配置
JWT_SECRET_KEY=your-very-long-random-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth 配置 (linux.do)
LINUXDO_CLIENT_ID=your_client_id
LINUXDO_CLIENT_SECRET=your_client_secret
LINUXDO_REDIRECT_URI=http://localhost:8082/api/auth/callback/linuxdo
```

### 生产环境安全配置

```env
# 必须指定具体的前端域名，禁止使用通配符 "*"
CORS_ORIGINS=https://your-domain.com

# 确保使用强随机密钥（至少 32 字符）
JWT_SECRET_KEY=your-very-long-random-secret-key-here

# 建议禁用调试模式
DEBUG=false
DEBUG_MODE=false
```

⚠️ **安全警告**：使用 HttpOnly Cookie 认证时，`CORS_ORIGINS` 必须配置为具体域名，**禁止使用 `*`**，否则存在 CSRF 攻击风险。

### 玩家级别的 LLM 配置

你可以为每个 AI 玩家（座位 2-9）配置独立的 LLM 提供商和参数：

```env
# 为玩家 2 配置专属 LLM
AI_PLAYER_2_NAME=player2
AI_PLAYER_2_API_KEY=your_api_key
AI_PLAYER_2_BASE_URL=https://api.openai.com/v1
AI_PLAYER_2_MODEL=gpt-4o-mini
AI_PLAYER_2_TEMPERATURE=0.7
AI_PLAYER_2_MAX_TOKENS=500
AI_PLAYER_2_MAX_RETRIES=2
```

### AI 对局分析配置

```env
# AI分析配置（可选，未配置则使用默认OpenAI配置）
ANALYSIS_PROVIDER=openai
ANALYSIS_MODEL=gpt-4o
ANALYSIS_MODE=comprehensive
ANALYSIS_LANGUAGE=auto
ANALYSIS_CACHE_ENABLED=true
ANALYSIS_MAX_TOKENS=4000
ANALYSIS_TEMPERATURE=0.7
```

### Mock 模式

如果不配置 `OPENAI_API_KEY`，系统会自动进入 Mock 模式，AI 玩家将使用预设的随机策略进行游戏。

### AI 调试面板

只有在 `.env` 中配置 `DEBUG_MODE=true` 时，游戏界面才会显示 AI 心理活动调试面板。

---

## 📡 API 文档

启动服务后访问 http://localhost:8082/docs 查看完整的 API 文档（Swagger UI）。

### 主要 API 端点

#### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `POST /api/auth/refresh` - 刷新 Token
- `GET /api/auth/oauth/linuxdo` - OAuth 登录
- `GET /api/auth/callback/linuxdo` - OAuth 回调

#### 用户
- `GET /api/users/me` - 获取当前用户信息
- `PUT /api/users/me` - 更新用户资料

#### 房间管理
- `POST /api/rooms` - 创建房间
- `GET /api/rooms` - 获取房间列表
- `GET /api/rooms/{room_id}` - 获取房间详情
- `POST /api/rooms/{room_id}/join` - 加入房间
- `POST /api/rooms/{room_id}/ready` - 切换准备状态
- `POST /api/rooms/{room_id}/start` - 开始游戏
- `DELETE /api/rooms/{room_id}` - 删除房间

#### 游戏进行
- `GET /api/game/{game_id}/state` - 获取游戏状态
- `POST /api/game/{game_id}/action` - 玩家行动
- `POST /api/game/{game_id}/step` - 推进游戏进程
- `GET /api/game/{game_id}/analysis` - 获取对局分析

---

## 🐛 故障排除

### Docker 相关问题

**问题：容器启动失败**
```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart
```

**问题：端口被占用**
```bash
# 修改 docker-compose.yml 中的端口映射
# 例如：将 8081:80 改为 8082:80
```

### 前端开发问题

**问题：npm install 失败**
```bash
# 清除缓存后重试
npm cache clean --force
npm install
```

### WebSocket 连接问题

**问题：WebSocket 连接失败（错误码 1006）**

这通常是因为生产服务器还在运行旧代码。请参考详细排查指南：

📖 **[WebSocket 故障排查指南](./WEBSOCKET_TROUBLESHOOTING.md)**

**快速修复**：
```bash
# 在生产服务器上执行
chmod +x deploy.sh
./deploy.sh

# 或手动部署
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**诊断工具**：
```bash
# 运行自动诊断
chmod +x diagnose-websocket.sh
./diagnose-websocket.sh
```

---

## 📝 开发计划

### 当前版本 (v1.5 - 2025-01-02)

#### WebSocket 实时通信
- ✅ WebSocket 实时游戏状态推送
- ✅ 按玩家路由的连接管理
- ✅ 状态版本控制防止竞态条件
- ✅ 智能状态合并与消息去重
- ✅ 自适应轮询策略优化

#### 用户系统
- ✅ 用户注册/登录（邮箱+密码）
- ✅ linux.do OAuth2 第三方登录
- ✅ JWT + HttpOnly Cookie 认证
- ✅ Refresh Token 轮换机制
- ✅ 用户资料管理（头像、昵称、简介）

#### 游戏功能
- ✅ 12人扩展局支持（守卫、狼王、白狼王）
- ✅ 狼人自刀策略
- ✅ 完善的胜负判定逻辑
- ✅ AI 对局分析与缓存

#### 安全与稳定性
- ✅ 异步 LLM 调用
- ✅ 游戏状态锁防止并发竞态
- ✅ 输入净化防止 Prompt 注入
- ✅ CSRF 防护（OAuth State 验证）

### 版本历史

| 版本 | 日期 | 主要功能 |
|------|------|----------|
| v1.5 | 2025-01-02 | WebSocket 实时通信、状态版本控制 |
| v1.4 | 2025-01-01 | 用户系统、OAuth登录、12人局 |
| v1.3 | 2024-12-30 | 安全修复、稳定性增强、狼人自刀 |
| v1.2 | 2024-12-30 | 多房间系统、AI填充、混合对战 |
| v1.1 | 2024-12-28 | AI对局分析、分析缓存 |
| v1.0 | 2024-12-27 | 初始版本、国际化支持 |

### 计划中功能
- [ ] 添加游戏回放功能
- [ ] 优化 AI 策略与个性化
- [ ] 游戏统计与排行榜
- [ ] 更多游戏配置选项（模式、角色组合）
- [ ] 语音聊天支持

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证。

---

**如果这个项目对你有帮助，请给一个 ⭐ Star！**
