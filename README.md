# 🌙 月夜狼人杀 AI Game

一个基于 AI 的在线狼人杀游戏，支持人类玩家与多个 AI 玩家共同游戏。采用 FastAPI + React + Docker 架构，提供流畅的游戏体验和智能的 AI 对手。

![Game Screenshot](https://img.shields.io/badge/Game-Werewolf-red)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![React](https://img.shields.io/badge/React-18.3-61dafb)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ed)

## ✨ 特性

- 🎮 **完整游戏流程**：支持狼人、预言家、女巫、猎人等经典角色
- 🤖 **AI 玩家**：基于 OpenAI GPT 的智能 AI 玩家，支持 Mock 模式测试
- 💬 **实时聊天**：游戏内实时聊天系统，记录所有玩家发言
- 🎨 **现代化 UI**：基于 shadcn/ui 的精美界面设计
- 🐳 **Docker 部署**：一键启动，开箱即用
- 📱 **响应式设计**：支持桌面和移动端访问

## 🎯 游戏角色

| 角色 | 阵营 | 能力 |
|------|------|------|
| 🐺 狼人 | 狼人阵营 | 每晚可以杀死一名玩家 |
| 🔮 预言家 | 好人阵营 | 每晚可以查验一名玩家的身份 |
| 💊 女巫 | 好人阵营 | 拥有解药和毒药各一瓶，同一晚使用解药后无法使用毒药 |
| 🏹 猎人 | 好人阵营 | 被淘汰时可以开枪带走一名玩家 |
| 👤 村民 | 好人阵营 | 普通村民，无特殊能力 |

## 🚀 快速开始

### 前置要求

- Docker 和 Docker Compose
- （可选）OpenAI API Key（用于真实 AI 对手）

### 使用 Docker 启动（推荐）

```bash
git clone https://github.com/NewstarDevelop/Werewolf.git
cd Werewolf
cp .env.example .env
nano .env
```
**填入真实模型商、密钥、模型之后**
```bash
docker compose up
```

 **访问游戏**
- 前端页面：http://localhost:8081
- 后端 API：http://localhost:8082
- API 文档：http://localhost:8082/docs

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

## 📁 项目结构

```
Werewolf/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模式
│   │   └── services/       # 业务逻辑
│   │       ├── game_engine.py  # 游戏引擎
│   │       ├── llm.py          # AI 服务
│   │       └── prompts.py      # AI 提示词
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # React 前端
│   ├── src/
│   │   ├── components/     # React 组件
│   │   │   ├── game/      # 游戏相关组件
│   │   │   └── ui/        # UI 基础组件
│   │   ├── hooks/         # 自定义 Hooks
│   │   ├── services/      # API 服务
│   │   └── pages/         # 页面组件
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🎮 游戏玩法

### 游戏流程

1. **游戏开始**：点击"开始游戏"创建 9 人局（1 人类 + 8 AI）
2. **角色分配**：系统自动分配角色（3 狼人、3 村民、预言家、女巫、猎人）
3. **夜晚阶段**：
   - 狼人选择击杀目标
   - 预言家查验玩家身份
   - 女巫先决策是否使用解药，再决策是否使用毒药（同一晚使用解药后无法使用毒药）
4. **白天阶段**：
   - 所有玩家依次发言
   - 投票淘汰可疑玩家
5. **胜利条件**：
   - 好人阵营：淘汰所有狼人
   - 狼人阵营：狼人数量 ≥ 好人数量

### 操作指南

- **发言**：在白天阶段，在输入框中输入发言内容，点击"确认"
- **投票**：在投票阶段，点击玩家头像选择投票目标
- **使用技能**：在夜晚阶段，点击"技能"按钮使用角色技能

## 🛠️ 技术栈

### 后端
- **FastAPI**：现代化的 Python Web 框架
- **Pydantic**：数据验证和序列化
- **OpenAI API**：AI 玩家决策引擎
- **Uvicorn**：ASGI 服务器

### 前端
- **React 18**：用户界面框架
- **TypeScript**：类型安全
- **Vite**：构建工具
- **TanStack Query**：数据获取和状态管理
- **shadcn/ui**：UI 组件库
- **Tailwind CSS**：样式框架
- **React Router**：路由管理

### 基础设施
- **Docker & Docker Compose**：容器化部署
- **Nginx**：前端静态文件服务

## 🔧 配置说明

### 环境变量

在项目根目录创建 `.env` 文件进行配置：

```env
# OpenAI API 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini

# 应用配置
DEBUG=false
CORS_ORIGINS=http://localhost:8081,http://127.0.0.1:8081
```

### 玩家级别的 LLM 配置

你可以为每个 AI 玩家（座位 2-9）配置独立的 LLM 提供商和参数。在 `.env` 文件中添加：

```env
# 为玩家 2 配置专属 LLM
AI_PLAYER_2_NAME=player2
AI_PLAYER_2_API_KEY=your_api_key
AI_PLAYER_2_BASE_URL=https://api.openai.com/v1
AI_PLAYER_2_MODEL=gpt-4o-mini
AI_PLAYER_2_TEMPERATURE=0.7
AI_PLAYER_2_MAX_TOKENS=500

# 为玩家 3 配置不同的模型
AI_PLAYER_3_NAME=player3
AI_PLAYER_3_API_KEY=your_api_key
AI_PLAYER_3_MODEL=gpt-4o
# ... 其他配置
```

**支持的配置项**：
- `AI_PLAYER_X_NAME`：玩家名称（可选）
- `AI_PLAYER_X_API_KEY`：API 密钥
- `AI_PLAYER_X_BASE_URL`：API 基础 URL（可选，默认使用 OpenAI）
- `AI_PLAYER_X_MODEL`：模型名称（默认：gpt-4o-mini）
- `AI_PLAYER_X_TEMPERATURE`：温度参数（默认：0.7）
- `AI_PLAYER_X_MAX_TOKENS`：最大 token 数（默认：500）
- `AI_PLAYER_X_MAX_RETRIES`：最大重试次数（默认：2）

其中 `X` 为玩家座位号（2-9，座位 1 为人类玩家）。

### Mock 模式

如果不配置 `OPENAI_API_KEY`，系统会自动进入 Mock 模式，AI 玩家将使用预设的随机策略进行游戏。

## 📊 API 文档

启动服务后访问 http://localhost:8082/docs 查看完整的 API 文档（Swagger UI）。

### 主要 API 端点

- `POST /api/game/start` - 开始新游戏
- `GET /api/game/{game_id}/state` - 获取游戏状态
- `POST /api/game/{game_id}/action` - 玩家行动
- `POST /api/game/{game_id}/step` - 推进游戏进程

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

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 开发计划

- [ ] 添加更多游戏角色（守卫、猎魔人等）
- [ ] 实现多房间系统
- [ ] 添加游戏回放功能
- [ ] 优化 AI 策略
- [ ] 添加语音聊天功能
- [ ] 实现排行榜系统

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 👥 作者

- **Newstar Develop Team**

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [React](https://react.dev/) - 用户界面库
- [shadcn/ui](https://ui.shadcn.com/) - 精美的 UI 组件
- [OpenAI](https://openai.com/) - AI 能力支持

---

⭐ 如果这个项目对你有帮助，请给我们一个 Star！
