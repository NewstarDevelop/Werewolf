## 1. 技术架构 (System Architecture)

### 1.1 架构图示

采用经典的前后端分离架构，通过 RESTful API 进行通信。

codeMermaid

```
graph TD
    Client[Next.js Client] <-->|HTTP REST| API[FastAPI Backend]
    API <-->|SQL| DB[(SQLite)]
    API <-->|API Call| LLM[LLM Service (OpenAI/Claude)]
    
    subgraph "Backend Logic"
        API --> GameManager[Game State Machine]
        GameManager --> PromptEng[Prompt Engine]
        PromptEng --> LLM
    end
```

### 1.2 技术栈选型

- **前端**: Next.js 14+ (App Router), TailwindCSS, Zustand (状态管理), Axios/TanStack Query.
- **后端**: Python 3.10+, FastAPI, Pydantic (数据验证), SQLAlchemy (ORM).
- **数据库**: SQLite (本地文件存储，易于部署和迁移).
- **AI 模型**: 建议使用 GPT-4o-mini 或 Claude 3.5 Haiku (兼顾速度与智商)。

------



## 2. 数据库设计 (Database Schema)

使用 SQLite，主要包含 4 张表。

### 2.1 games (对局表)

















| 字段名     | 类型          | 说明                                                         |
| ---------- | ------------- | ------------------------------------------------------------ |
| id         | STRING (UUID) | 主键                                                         |
| status     | ENUM          | waiting, playing, finished                                   |
| day        | INT           | 当前天数 (1, 2, ...)                                         |
| phase      | ENUM          | night_werewolf, night_seer, night_witch, day_speech, day_vote ... |
| winner     | ENUM          | null, werewolf, villager                                     |
| created_at | DATETIME      | 创建时间                                                     |

### 2.2 players (玩家表)





















| 字段名      | 类型   | 说明                                    |
| ----------- | ------ | --------------------------------------- |
| id          | INT    | 自增ID                                  |
| game_id     | STRING | 外键 -> games.id                        |
| seat_id     | INT    | 座位号 (1-9)                            |
| is_human    | BOOL   | 是否真人                                |
| role        | ENUM   | werewolf, villager, seer, witch, hunter |
| is_alive    | BOOL   | 存活状态                                |
| personality | JSON   | 存放AI人设 (性格, 说话风格)             |
| memory      | TEXT   | (可选) 简单的短期记忆缓存               |

### 2.3 actions (动作记录表 - 用于复盘和逻辑判断)



















| 字段名      | 类型   | 说明                             |
| ----------- | ------ | -------------------------------- |
| id          | INT    | 主键                             |
| game_id     | STRING | 外键                             |
| day         | INT    | 第几天                           |
| phase       | STRING | 发生阶段                         |
| player_id   | INT    | 发起者座次                       |
| target_id   | INT    | 目标座次 (如被杀、被验、被投)    |
| action_type | ENUM   | kill, verify, save, poison, vote |

### 2.4 messages (聊天记录表)

















| 字段名    | 类型   | 说明                                   |
| --------- | ------ | -------------------------------------- |
| id        | INT    | 主键                                   |
| game_id   | STRING | 外键                                   |
| day       | INT    | 天数                                   |
| player_id | INT    | 发言者 (0代表系统公告)                 |
| content   | TEXT   | 发言内容                               |
| type      | ENUM   | speech, system, thought (仅AI复盘可见) |

------



## 3. API 接口定义 (RESTful)

### 3.1 游戏控制

- **POST /api/game/start**
  - 功能：创建新游戏，分配身份，生成AI人设。
  - Request: { "human_seat": 1 (optional) }
  - Response: { "game_id": "uuid", "player_role": "seer", "players": [...] }
- **GET /api/game/{game_id}/state**
  - 功能：轮询获取当前游戏状态（前端每秒或操作后调用）。
  - Response: GameState (见下方JSON结构)。

### 3.2 流程推进 (The "Engine")

由于是单人游戏，我们需要显式触发AI的行动。

- **POST /api/game/{game_id}/step**
  - 功能：尝试推进游戏状态。
  - 逻辑：如果当前是AI的回合（如AI发言、AI投票），后端执行LLM调用并更新数据库，然后返回结果。如果需要真人操作，则返回等待信号。
  - Response: { "status": "updated", "new_phase": "day_vote" } 或 { "status": "waiting_for_human" }

### 3.3 玩家操作

- **POST /api/game/{game_id}/action**

  - 功能：真人玩家提交动作。

  - Request:

    codeJSON

    ```
    {
      "seat_id": 1,
      "action_type": "vote", // 或 kill, verify, poison, save
      "target_id": 3,
      "content": "我是预言家，3号是查杀！" // 用于发言阶段
    }
    ```

  - Response: { "success": true }

------



## 4. 数据结构 (JSON Definitions)

### 4.1 GameState Response (/api/game_state)

前端根据此数据渲染界面。

codeJSON

```
{
  "game_id": "123-abc",
  "day": 1,
  "phase": "day_speech", 
  "phase_deadline": 30, // 倒计时(秒)
  "current_actor": 2,   // 当前轮到谁行动/发言
  "my_seat": 1,
  "my_role": "seer",
  "players": [
    { "seat": 1, "is_alive": true, "is_human": true },
    { "seat": 2, "is_alive": true, "avatar": "old_man.png" },
    ...
  ],
  "message_log": [
    { "seat": 0, "text": "天亮了，昨晚是平安夜。", "type": "system" },
    { "seat": 2, "text": "我是好人，过。", "type": "speech" }
  ],
  "pending_action": null // 或 { "type": "vote", "choices": [2,3,4...] }
}
```

------



## 5. AI 系统设计 (AI System & Prompt Engineering)

### 5.1 AI 处理流程

1. **构建 Context**：从数据库拉取最近的聊天记录 (History) 和当前存活情况。
2. **注入 System Prompt**：包含身份、规则、性格。
3. **调用 LLM**：要求返回 JSON 格式（思考 + 行动/发言）。
4. **解析与执行**：将 JSON 转换为游戏内的 Action 或 Message。

### 5.2 System Prompt 模板

这是核心 Prompt 的设计逻辑。

codeMarkdown

```
# Role
你正在参与一场《狼人杀》文字游戏。
你的身份是：{ROLE} (如：狼人)。
你的座位号是：{SEAT_ID}。
你的性格特征：{PERSONALITY} (如：暴躁、喜欢攻击别人)。

# Game Context
当前是第 {DAY} 天，阶段：{PHASE}。
存活玩家：{ALIVE_PLAYERS}。
你的狼同伴：{WOLF_PARTNERS} (如果是好人则无此项)。

# Objective
根据你的身份和当前局势进行行动。
- 如果是狼人：伪装成平民或神职，误导好人，白天尽量把好人投出去。
- 如果是好人：寻找狼人蛛丝马迹，通过逻辑分析找出真凶。

# Rules
1. 说话要符合你的性格。
2. 简短有力，不要长篇大论。
3. 严禁暴露你是AI，必须扮演人类玩家。

# Output Format (JSON Only)
{
  "thought": "你的内心独白（策略分析），不会发给其他玩家。",
  "speak": "公开发言的内容（如果是投票阶段，可以留空）。",
  "action_target": 3 (仅在需要技能目标或投票目标时填写座位号，否则为null)
}
```

### 5.3 AI 伪装策略 (Advanced)

- **狼人AI**：
  - Backend 会随机指定一个狼人 AI 在第二天白天 "悍跳" (Claim) 预言家。
  - 在 Prompt 中增加指令："Secret Mission: 今天你需要假装自己是预言家，并给玩家{TARGET}发查杀。"

------



## 6. 核心逻辑伪代码 (Game Logic)

### 6.1 状态机流转 (State Transition)

codePython

```
def process_turn(game):
    if game.phase == "night_werewolf":
        # 收集狼人意见，若意见一致或超时，进入下一阶段
        # 如果真人是狼人，等待真人提交
        pass
    
    elif game.phase == "day_speech":
        current_speaker = get_next_speaker(game)
        if not current_speaker:
            game.phase = "day_vote"
            return
        
        if current_speaker.is_ai:
            # 调用LLM生成发言
            response = llm_service.generate_speech(current_speaker)
            save_message(response)
        else:
            # 等待前端提交发言
            return "waiting_for_human"
            
    elif game.phase == "day_vote":
        # 检查所有存活玩家是否已投票
        if all_voted(game):
            result = calculate_votes(game)
            eliminate_player(result)
            check_win_condition(game)
            game.phase = "night_start"
```

------



## 7. 前端实现细节 (Frontend Implementation)

### 7.1 轮询与渲染

由于 LLM 生成需要时间（2-5秒），前端需要优化体验：

1. **AI 思考中**：当轮到 AI 发言时，前端显示 "Player X 正在输入..." 动画。
2. **流式打字机**：后端虽是一次性返回文本，但前端可以使用 TypewriterEffect 组件，以每秒 5-10 个字的速度逐字显示，增加真实感。

### 7.2 页面路由

- / : 首页
- /game/[id] : 游戏主战场