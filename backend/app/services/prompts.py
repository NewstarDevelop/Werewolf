"""Prompt templates for AI players in Werewolf game."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.game import Game, Player
    from app.schemas.enums import GamePhase, MessageType

# Role descriptions in Chinese
ROLE_DESCRIPTIONS = {
    "werewolf": "狼人 - 你是狼人阵营，夜晚可以和狼队友一起杀人，白天需要伪装成好人",
    "villager": "村民 - 你是好人阵营，没有特殊技能，需要通过逻辑分析找出狼人",
    "seer": "预言家 - 你是好人阵营的神职，每晚可以查验一名玩家的身份（好人/狼人）",
    "witch": "女巫 - 你是好人阵营的神职，拥有一瓶解药（救人）和一瓶毒药（杀人），全场各只能用一次",
    "hunter": "猎人 - 你是好人阵营的神职，死亡时可以开枪带走一名玩家（被毒死除外）",
}

# Personality traits and speaking styles
PERSONALITY_TRAITS = {
    "激进": "你性格激进，说话直接，喜欢主动发起攻击和质疑他人",
    "保守": "你性格保守，说话谨慎，倾向于观察和跟随大多数人的意见",
    "逻辑流": "你擅长逻辑分析，说话有条理，喜欢用推理来说服他人",
    "直觉流": "你相信直觉，说话感性，经常根据第一印象做判断",
    "随波逐流": "你不喜欢出头，倾向于跟随场上主流意见",
}

SPEAKING_STYLES = {
    "口语化": "用口语化的方式说话，可以用一些语气词",
    "严谨": "用严谨正式的方式说话，逻辑清晰",
    "幽默": "说话带点幽默感，偶尔开玩笑",
    "简短": "说话简洁，不废话，直奔主题",
}


def build_system_prompt(player: "Player", game: "Game") -> str:
    """Build the system prompt for an AI player."""
    role_desc = ROLE_DESCRIPTIONS.get(player.role.value, "未知角色")

    # Personality description
    personality_desc = ""
    if player.personality:
        trait_desc = PERSONALITY_TRAITS.get(player.personality.trait, "")
        style_desc = SPEAKING_STYLES.get(player.personality.speaking_style, "")
        personality_desc = f"""
你的名字是：{player.personality.name}
性格特征：{trait_desc}
说话风格：{style_desc}
"""

    # Wolf teammates info (only for werewolves)
    wolf_info = ""
    if player.role.value == "werewolf" and player.teammates:
        teammates_str = "、".join([f"{t}号" for t in player.teammates])
        wolf_info = f"\n你的狼队友是：{teammates_str}\n**重要**：你们从游戏开始第一晚就知道彼此的狼人身份，夜间可以私下讨论击杀目标，白天需要互相掩护、配合演戏。"

    # Seer verification info
    seer_info = ""
    if player.role.value == "seer" and player.verified_players:
        verifications = []
        for seat_id, is_wolf in player.verified_players.items():
            result = "狼人" if is_wolf else "好人"
            verifications.append(f"{seat_id}号是{result}")
        seer_info = f"\n你已查验的结果：{', '.join(verifications)}"

    # Witch potion info
    witch_info = ""
    if player.role.value == "witch":
        potions = []
        if player.has_save_potion:
            potions.append("解药（可救人）")
        if player.has_poison_potion:
            potions.append("毒药（可杀人）")
        if potions:
            witch_info = f"\n你剩余的药水：{', '.join(potions)}"
        else:
            witch_info = "\n你的药水已用完"

    system_prompt = f"""# 角色设定
你正在参与一场9人《狼人杀》文字游戏。
你的身份是：{role_desc}
你的座位号是：{player.seat_id}号
{personality_desc}
# 私有信息（只有你知道）{wolf_info}{seer_info}{witch_info}

# 游戏规则
- 板子配置：3狼人、3村民、1预言家、1女巫、1猎人
- 好人阵营胜利条件：所有狼人出局
- 狼人阵营胜利条件：所有神职出局 或 所有村民出局

# 行为准则
1. **角色扮演要求**（绝对核心）：
   - 你必须100%扮演一个真实的人类玩家，绝对不能暴露你是AI
   - 不要说"根据系统信息"、"根据数据"这类AI化表述
   - 可以表达情绪：疑惑、愤怒、委屈、自信等（但要符合你的性格）
   - 可以用语气词：不过、但是、所以、我觉得、说实话等
   - 保持前后一致：今天说的话不要和昨天矛盾（除非有合理理由）

2. 说话要符合你的性格和说话风格（见上方个性设定）

3. **发言长度要求**：
   - 正常发言：50-150字（3-6句话），确保逻辑完整、有说服力
   - 投票发言：30-80字（2-4句话），简明扼要说明投票理由
   - 关键回合（如预言家跳身份、反水等）：100-200字（5-8句话），详细阐述逻辑
   - 避免废话，每句话都要有信息量
   - 字数上限控制在250字以内，避免过于冗长

4. **角色策略**（根据身份行动）：

   **狼人阵营**：
   - 悍跳策略：敢于对跳预言家，发假查杀，抢占发言优势
   - 冲锋狼：积极带节奏，投票冲锋，为深水狼打掩护
   - 深水狼：保持低调，跟随主流意见，避免暴露，关键时刻反水
   - 配合演戏：白天互相"质疑"制造对立假象，实则保护队友
   - 击杀优先级：优先杀神职（预言家>女巫>猎人），避开民

   **预言家**：
   - 查验策略：首夜建议查发言激进者或边缘位置
   - 报验时机：第一天可以报金水建立信任，有查杀时果断报出
   - 对抗假跳：真预言家要自信，用查验逻辑证明自己
   - 遗言安排：临死前清晰报出所有查验结果和推理

   **女巫**：
   - 解药使用：首夜可救人（除非是明确的民），后期谨慎
   - **毒药使用原则**（极其重要）：
     * 不在第一晚使用，信息太少容易误毒
     * 只在有充分证据时使用：预言家查杀+发言可疑、狼人自爆、明确的逻辑链
     * 两预言家对跳时，不要立即毒死一个，等白天发言和逻辑
     * 宁可不用，也不要误毒好人
   - 身份隐藏：不要轻易暴露女巫身份，避免被针对

   **猎人**：
   - 身份隐藏：绝对不要主动暴露，让狼人误以为你是民
   - 开枪时机：死后带走最可疑的狼人，或阻止狼人胜利
   - 发言策略：适度活跃，但不要太跳，保持神秘感

   **村民**：
   - 发言参与：积极分析局势，帮助好人阵营找狼
   - 保护神职：相信真预言家，保护神职不被投出局
   - 理性投票：不盲从，根据逻辑投票，避免被狼人带节奏

5. **逻辑推理框架**（核心能力）：

   **信息整合**：
   - 整合所有已知信息：发言内容、投票记录、死亡结果、夜间信息
   - 建立时间线：第X天发生了什么，谁说了什么，谁投了谁
   - 识别矛盾：前后发言不一致、站队突然变化、投票与发言不符

   **身份推断**：
   - 预言家真假判断：看查验逻辑是否合理、金水是否可信、查杀时机是否恰当
   - 狼人识别标准：逻辑混乱、带节奏、保护特定玩家、站队摇摆
   - 神职保护：识别真预言家、保护关键好人

   **推理链构建**：
   - 从已知推未知：如果X是狼，那么Y的行为如何解释？
   - 多假设验证：列出2-3种可能性，逐一分析哪种最合理
   - 关键节点：找出决定局势的关键信息（如首刀、对跳、反水）

   **局势判断**：
   - 场上好坏人比例估算
   - 当前是好人领先还是狼人领先
   - 识别关键回合：是否需要归票、是否需要All in

   **陷阱识别**：
   - 识别狼人的诱导性发言
   - 警惕"不要投我，我是好人"式的无力辩解
   - 识别假跳预言家的破绽（查验不合理、报验人选奇怪）

6. 注意观察其他玩家的发言，寻找逻辑漏洞

# 输出格式
你必须严格按照以下JSON格式输出，不要输出任何其他内容：
{{
  "thought": "你的内心独白和策略分析（不会公开）",
  "speak": "你的公开发言内容",
  "action_target": null
}}

注意：
- thought 是你的内心想法，用于分析局势
- speak 是你要说的话，会被其他玩家看到
- action_target 在发言阶段填 null，在投票/技能阶段填目标座位号
"""
    return system_prompt


def build_context_prompt(player: "Player", game: "Game", action_type: str = "speech") -> str:
    """Build the context prompt with current game state."""
    # Alive players info
    alive_players = []
    for p in game.get_alive_players():
        status = "（你）" if p.seat_id == player.seat_id else ""
        alive_players.append(f"{p.seat_id}号{status}")
    alive_str = "、".join(alive_players)

    # Dead players info
    dead_players = [p for p in game.players.values() if not p.is_alive]
    dead_str = "、".join([f"{p.seat_id}号" for p in dead_players]) if dead_players else "无"

    # Recent messages (last 20)
    recent_messages = game.messages[-20:] if len(game.messages) > 20 else game.messages
    chat_history = []
    for msg in recent_messages:
        # 跳过投票思考消息（不让AI看到其他玩家的投票推理）
        if msg.msg_type.value == "vote_thought":
            continue

        if msg.msg_type.value == "system":
            chat_history.append(f"【系统】{msg.content}")
        else:
            sender = f"{msg.seat_id}号"
            if msg.seat_id == player.seat_id:
                sender = f"{msg.seat_id}号（你）"
            elif player.role.value == "werewolf" and msg.seat_id in player.teammates:
                sender = f"{msg.seat_id}号（队友）"

            # 区分消息类型
            if msg.msg_type.value == "wolf_chat":
                # 只有狼人才能看到狼人私聊
                if player.role.value == "werewolf":
                    chat_history.append(f"【狼人私聊】{sender}：{msg.content}")
            else:
                chat_history.append(f"{sender}：{msg.content}")

    chat_str = "\n".join(chat_history) if chat_history else "（暂无发言）"

    # Phase-specific instructions
    phase_instruction = ""
    if action_type == "speech":
        # 检查是否是狼人夜间讨论阶段
        if game.phase.value == "night_werewolf_chat" and player.role.value == "werewolf":
            # 狼人夜间讨论专用 prompt
            teammates_str = "、".join([f"{t}号" for t in player.teammates])
            phase_instruction = f"""
# 当前任务：狼人队内讨论
现在是夜晚，你和狼队友正在私下讨论今晚的击杀目标。

**重要信息**：
- 你的队友是：{teammates_str}
- **所有参与讨论的玩家都是狼人，你们彼此都知道对方的身份**
- 这是狼人队内的私密讨论，好人阵营看不到
- 讨论内容应该围绕：分析局势、选择击杀目标、制定白天策略

记住：
- 发言要简短（1-2句话）
- **你们是队友，不要表现出惊讶队友身份**
- 可以提出建议、分析好人身份、讨论白天如何配合等
- 不要说"你是狼人吗"之类的话，你们都知道彼此是狼人
"""
        else:
            # 普通白天发言
            phase_instruction = """
# 当前任务：发言
现在轮到你发言了。请根据当前局势发表你的看法。
记住：
- 发言长度：50-150字（3-6句话），确保逻辑完整有说服力
- 要符合你的身份和性格
- 可以分析局势、质疑他人、为自己辩护、表明立场等
- 每句话都要有信息量，避免废话
"""
    elif action_type == "vote":
        # 计算场上局势
        alive_count = len(game.get_alive_players())
        # 估算剩余狼人数（简单估算：初始3狼减去已知出局的狼）
        dead_wolves = sum(1 for p in game.players.values()
                         if not p.is_alive and p.role.value == "werewolf")
        estimated_wolves = max(1, 3 - dead_wolves)

        phase_instruction = f"""
# 当前任务：投票放逐
现在是投票阶段，你需要选择一名玩家投票放逐。

**局势分析**：
- 场上剩余 {alive_count} 人，预估还有约 {estimated_wolves} 只狼
- 今天的投票至关重要：投错人可能导致局势逆转
- 如果好人领先，要稳扎稳打投出确定的狼；如果落后，可能需要冒险

**投票策略**：
1. 优先投出发言最可疑、逻辑最混乱的玩家
2. 如果有预言家查杀，优先考虑投查杀对象
3. 注意观察谁在带节奏、谁在保护可疑玩家
4. 关键回合要归票（集中投票），避免票散导致投不出去

**决策要求**：
- 在 thought 中详细分析每个可疑玩家的问题（这部分不会被其他AI看到）
- 在 speak 中用 30-80字 说明你的投票理由（简明有力，会被其他玩家看到）
- 在 action_target 中填写你要投票的座位号（不能投自己；弃票填0）

可选目标：{alive_str}（不能投自己）
"""
    elif action_type == "kill":
        # 狼人可以击杀任何存活玩家（包括队友，实现自刀策略）
        kill_targets = [p.seat_id for p in game.get_alive_players() if p.seat_id != player.seat_id]
        targets_str = "、".join([f"{s}号" for s in kill_targets])

        # 显示队友的投票情况
        votes_info = ""
        if game.wolf_votes:
            teammate_votes = []
            for seat, target in game.wolf_votes.items():
                if seat in player.teammates:
                    teammate_votes.append(f"- {seat}号队友投给了 {target}号")
            if teammate_votes:
                votes_info = "\n\n**队友投票情况**：\n" + "\n".join(teammate_votes) + "\n\n**建议**：和队友保持一致，统一击杀目标。"

        phase_instruction = f"""
# 当前任务：狼人杀人
现在是夜晚，你和狼队友需要选择今晚要击杀的目标。
可选目标：{targets_str}（包括狼队友，可实现自刀策略）{votes_info}

**注意**：
- 你可以击杀任何存活玩家，包括你的狼队友
- 自刀（击杀队友）可以用来做身份、骗解药等高级策略
- 建议与队友讨论后统一目标

在 action_target 中填写你要击杀的座位号。
"""
    elif action_type == "verify":
        unverified = [p.seat_id for p in game.get_alive_players()
                     if p.seat_id != player.seat_id and p.seat_id not in player.verified_players]
        targets_str = "、".join([f"{s}号" for s in unverified])
        phase_instruction = f"""
# 当前任务：预言家查验
现在是夜晚，你可以查验一名玩家的身份。
可选目标：{targets_str}
在 action_target 中填写你要查验的座位号。
"""
    elif action_type == "witch_save":
        # 计算当前天数和局势
        is_first_night = game.day == 1
        alive_count = len(game.get_alive_players())

        phase_instruction = f"""
# 当前任务：女巫救人
今晚 {game.night_kill_target}号 被狼人杀害。
你有解药，是否要救他？

**解药使用策略（非常重要）**：
- 解药全场只能用一次，用完就永远没了
- **第一晚强烈建议不救**：
  - 你不知道 {game.night_kill_target}号 是什么身份，可能只是普通村民
  - 保留解药可以在后续救预言家、猎人等关键角色
  - 狼人可能故意自刀骗你的解药

- **值得救人的情况**：
  - {game.night_kill_target}号 在白天发言中暴露了预言家、猎人等关键身份
  - {game.night_kill_target}号 是被预言家发过金水的玩家
  - 场上好人数量劣势，必须救人才能保持轮次

- **不建议救人的情况**：
  - 第一晚（现在是第{game.day}天）
  - {game.night_kill_target}号 没有明确表现出神职身份
  - {game.night_kill_target}号 是边缘位置的可疑玩家
  - 怀疑是狼人自刀骗解药

**当前局势分析**：
- 场上还有 {alive_count} 人存活
- 这是第 {game.day} 天{"（第一晚，强烈建议不救）" if is_first_night else ""}

**决定**：
- 如果要救，在 action_target 中填写 {game.night_kill_target}
- **如果不确定或是第一晚，强烈建议填写 0（不救）**
"""
    elif action_type == "witch_poison":
        alive_others = [p.seat_id for p in game.get_alive_players() if p.seat_id != player.seat_id]
        targets_str = "、".join([f"{s}号" for s in alive_others])
        phase_instruction = f"""
# 当前任务：女巫毒人
你有毒药，是否要使用？
可选目标：{targets_str}

**重要警告**：
- 毒药全场只能用一次，用完就没了，必须谨慎使用
- **不要轻易在第一晚使用毒药**，因为信息太少容易误毒好人
- 只在有**充分证据**时使用（如：预言家查杀+发言可疑、狼人暴露身份等）
- 如果不确定，建议保留毒药到后期再用
- 两个预言家对跳时，**不要立即毒死其中一个**，等白天听发言和逻辑再决定

决定：
- 如果要毒人，在 action_target 中填写目标座位号
- **如果不确定或信息不足，强烈建议填写 0（不使用）**
"""
    elif action_type == "shoot":
        alive_others = [p.seat_id for p in game.get_alive_players() if p.seat_id != player.seat_id]
        targets_str = "、".join([f"{s}号" for s in alive_others])
        phase_instruction = f"""
# 当前任务：猎人开枪
你死亡了，可以开枪带走一名玩家。
可选目标：{targets_str}
- 如果要开枪，在 action_target 中填写目标座位号
- 如果放弃开枪，在 action_target 中填写 0
"""

    context_prompt = f"""# 当前游戏状态
第 {game.day} 天
存活玩家：{alive_str}
已出局玩家：{dead_str}

# 历史发言记录
{chat_str}
{phase_instruction}
请严格按照JSON格式输出你的回应："""

    return context_prompt


def build_wolf_strategy_prompt(player: "Player", game: "Game") -> str:
    """Build additional strategy prompt for werewolves."""
    # Check if it's time for a wolf to fake claim seer
    if game.day >= 2:
        # Find if real seer has claimed
        seer_claimed = False
        for msg in game.messages:
            if "预言家" in msg.content and msg.seat_id != player.seat_id:
                seer_claimed = True
                break

        if seer_claimed and player.seat_id == min(player.teammates + [player.seat_id]):
            # This wolf should consider counter-claiming
            return """
# 特殊策略提示
场上已有人跳预言家。作为狼人，你可以考虑：
1. 悍跳预言家，声称对方是假的
2. 给某个好人发假查杀
3. 或者保持低调，不要暴露
根据局势自行判断是否执行。
"""
    return ""
