## 1. 项目结构 (Project Structure)

本项目采用 **Monorepo** 风格的目录结构（虽然不一定用 Turbo/Nx，但代码放在一个仓库方便管理），根目录下分为 backend 和 frontend。

codeText

```
werewolf-ai/
├── backend/                  # Python FastAPI
│   ├── app/
│   │   ├── api/              # 路由定义 (Routers)
│   │   │   ├── endpoints/
│   │   │   └── api.py
│   │   ├── core/             # 核心配置 (Config, Security)
│   │   ├── db/               # 数据库模型与Session
│   │   ├── models/           # SQLAlchemy Models (ORM)
│   │   ├── schemas/          # Pydantic Schemas (Data Transfer)
│   │   ├── services/         # 业务逻辑层 (Game Logic, LLM Service)
│   │   │   ├── game_engine.py # 核心状态机
│   │   │   └── llm.py         # LLM 调用封装
│   │   └── main.py           # 入口文件
│   ├── .env                  # 环境变量 (API Key, DB Path)
│   ├── requirements.txt
│   └── alembic/              # 数据库迁移脚本
│
├── frontend/                 # Next.js 14+ (App Router)
│   ├── src/
│   │   ├── app/              # 页面路由 (page.tsx, layout.tsx)
│   │   ├── components/       # UI 组件 (Atom/Molecule/Organism)
│   │   │   ├── game/         # 游戏专用组件 (Board, Chat, Card)
│   │   │   └── ui/           # 通用组件 (Button, Input)
│   │   ├── hooks/            # 自定义 Hooks
│   │   ├── lib/              # 工具函数 (API Client, Utils)
│   │   ├── store/            # 状态管理 (Zustand)
│   │   └── types/            # TypeScript 类型定义
│   ├── .env.local
│   ├── tailwind.config.ts
│   └── package.json
│
└── README.md
```

------



## 2. 后端规范 (Python / FastAPI)

### 2.1 代码风格

- **格式化**：强制使用 **Ruff** 或 **Black** 进行代码格式化。

- **类型提示**：所有函数参数和返回值必须包含 Type Hints (typing 或 Python 3.10+ 原生类型)。

  codePython

  ```
  # Good
  def calculate_votes(votes: list[Vote]) -> dict[int, int]:
      ...
  
  # Bad
  def calculate_votes(votes):
      ...
  ```

- **命名规范**：

  - 变量/函数：snake_case (e.g., process_night_turn)
  - 类名：PascalCase (e.g., GameEngine)
  - 常量：UPPER_CASE (e.g., MAX_PLAYERS = 9)

### 2.2 架构分层

- **Router 层**：仅处理 HTTP 请求/响应，不做业务逻辑。
- **Service 层**：处理具体业务（如“验人”、“生成发言”）。LLM 的调用逻辑必须封装在 Service 层，严禁在 Router 中直接调用 OpenAI。
- **Schema 层**：使用 Pydantic 模型严格定义输入输出，禁止返回裸字典 dict。

### 2.3 LLM 工程规范

- **Prompt 管理**：Prompt 模板不应硬编码在逻辑代码中，建议放入单独的 prompts.py 或 .yaml 配置文件中。
- **异常处理**：调用 LLM 必须包裹在 try-except 中。如果 LLM 解析 JSON 失败，需实现 **Retry** 机制（重试1次）或 **Fallback** 机制（返回默认的基础发言）。
- **日志**：必须记录每次发给 LLM 的 Prompt 和 LLM 返回的 Raw Text，便于后续 Debug 和优化模型。

------



## 3. 前端规范 (Next.js / TypeScript)

### 3.1 代码风格

- **组件定义**：统一使用 Functional Components。

- **类型定义**：严禁使用 any。对于后端返回的复杂数据，在 src/types/api.ts 中定义对应的 Interface。

- **样式**：使用 **Tailwind CSS**。避免写 .css 文件（全局样式除外）。

  codeTsx

  ```
  // Good
  <div className="flex flex-col items-center p-4 bg-gray-900 text-white">
  
  // Bad (Inline styles)
  <div style={{ display: 'flex', padding: '10px' }}>
  ```

### 3.2 状态管理

- **服务端状态**：使用 TanStack Query (React Query) 处理 /api/game_state 的轮询和缓存。
- **客户端状态**：使用 Zustand 处理 UI 交互状态（如：当前选中的玩家、弹窗开关）。

### 3.3 交互优化

- **防抖**：用户点击“投票”或“技能”按钮后，立即禁用按钮并显示 Loading 状态，防止重复提交。
- **流式模拟**：后端返回整段文本后，前端组件需实现“打字机效果”（Typewriter Effect），每 50ms 渲染一个字，增强沉浸感。

------



## 4. 接口与数据协议 (API Protocol)

### 4.1 JSON 命名

- **Request/Response**：统一使用 snake_case（下划线命名），以匹配 Python 后端习惯。前端在 TypeScript Interface 中定义时也使用下划线，避免转换带来的性能开销和混淆。

  codeTypeScript

  ```
  // frontend/src/types/game.ts
  interface Player {
    seat_id: number;  // Keep snake_case
    is_alive: boolean;
    role: string;
  }
  ```

### 4.2 HTTP 状态码

- 200 OK：操作成功。
- 400 Bad Request：逻辑错误（如：平民试图验人，或已经投过票了）。
- 401 Unauthorized：未登录（MVP可能暂不需要）。
- 404 Not Found：游戏ID不存在。
- 500 Internal Server Error：代码崩溃或 LLM 服务不可用。

------



## 5. 版本控制 (Git Workflow)

遵循 **Conventional Commits** 规范：

- feat: ... : 新功能 (e.g., feat: implement seer verification logic)
- fix: ... : 修复 Bug (e.g., fix: AI voting for self)
- docs: ... : 文档修改
- style: ... : 代码格式化（不影响逻辑）
- refactor: ... : 代码重构

------



## 6. 核心代码示例 (Scaffolding)

为了让你快速上手，这里提供了核心模块的脚手架代码。

### 6.1 后端：LLM Service 封装 (backend/app/services/llm.py)

codePython

```
import json
import openai
from app.core.config import settings

class LLMService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini" # or claude-3-5-sonnet

    def generate_player_action(self, system_prompt: str, context: str) -> dict:
        """
        生成玩家的行动和发言，强制返回 JSON
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                response_format={"type": "json_object"}, # 强制 JSON 模式
                temperature=0.7
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"LLM Error: {e}")
            # Fallback 策略
            return {
                "thought": "我脑子有点乱...",
                "speak": "过。",
                "action_target": None
            }
```

### 6.2 后端：核心状态机 (backend/app/services/game_engine.py)

codePython

```
from app.models.game import Game, Player
from app.services.llm import LLMService

class GameEngine:
    def __init__(self, db_session):
        self.db = db_session
        self.llm = LLMService()

    async def step(self, game_id: str):
        game = self.db.get_game(game_id)
        
        # 1. 检查是否真人回合
        if self._is_human_turn(game):
            return {"status": "waiting_for_human"}

        # 2. 获取当前AI玩家
        current_seat = game.current_actor_seat
        ai_player = game.get_player(current_seat)

        # 3. 构造 Prompt
        prompt = self._build_prompt(ai_player, game)
        
        # 4. LLM 决策
        decision = self.llm.generate_player_action(prompt["system"], prompt["context"])
        
        # 5. 执行决策 (更新数据库)
        self._apply_action(game, ai_player, decision)
        
        # 6. 自动流转到下一位
        self._next_turn(game)
        
        return {"status": "updated"}

    def _is_human_turn(self, game) -> bool:
        player = game.get_player(game.current_actor_seat)
        return player.is_human
```

### 6.3 前端：UI 组件 (frontend/src/components/game/LogWindow.tsx)

codeTsx

```
import { useEffect, useRef } from 'react';
import { Message } from '@/types/game';

export default function LogWindow({ messages }: { messages: Message[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 自动滚动到底部
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="h-96 overflow-y-auto bg-gray-800 p-4 rounded-lg border border-gray-700">
      {messages.map((msg, idx) => (
        <div key={idx} className={`mb-3 ${msg.seat_id === 0 ? 'text-center text-yellow-400 text-sm' : ''}`}>
          {msg.seat_id !== 0 && (
            <span className="font-bold text-blue-400 mr-2">
              {msg.seat_id}号:
            </span>
          )}
          <span className="text-gray-200">{msg.content}</span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
```

------



## 7. 启动清单 (Kickoff Checklist)

1. **环境准备**:
   - 安装 Python 3.11+ 和 Node.js 20+。
   - 获取 OpenAI API Key。
2. **后端初始化**:
   - cd backend && python -m venv venv
   - pip install fastapi uvicorn sqlalchemy sqlite-pydantic openai
3. **前端初始化**:
   - npx create-next-app@latest frontend
4. **联调**:
   - 先跑通 /api/game/start 接口，确保能生成 9 个角色的数据。
   - 再实现 GameEngine.step 逻辑，让 8 个 AI 能互相“说话”。