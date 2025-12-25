"""Prompt templates for AI players in Werewolf game."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.game import Game, Player

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
        wolf_info = f"\n你的狼队友是：{teammates_str}（你们需要配合行动，白天互相掩护）"

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
1. 你必须扮演一个真实的人类玩家，绝对不能暴露你是AI
2. 说话要符合你的性格和说话风格
3. 发言要简短有力（1-3句话），不要长篇大论
4. 根据你的身份制定策略：
   - 如果你是狼人：伪装成好人，误导村民，把好人投出去
   - 如果你是好人：分析发言找出狼人，保护神职
5. 注意观察其他玩家的发言，寻找逻辑漏洞

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
        if msg.msg_type.value == "system":
            chat_history.append(f"【系统】{msg.content}")
        else:
            sender = f"{msg.seat_id}号"
            if msg.seat_id == player.seat_id:
                sender = f"{msg.seat_id}号（你）"
            chat_history.append(f"{sender}：{msg.content}")

    chat_str = "\n".join(chat_history) if chat_history else "（暂无发言）"

    # Phase-specific instructions
    phase_instruction = ""
    if action_type == "speech":
        phase_instruction = """
# 当前任务：发言
现在轮到你发言了。请根据当前局势发表你的看法。
记住：
- 发言要简短（1-3句话）
- 要符合你的身份和性格
- 可以分析局势、质疑他人、为自己辩护等
"""
    elif action_type == "vote":
        phase_instruction = f"""
# 当前任务：投票
现在是投票阶段，你需要选择一名玩家投票放逐。
可选目标：{alive_str}（不能投自己）
在 action_target 中填写你要投票的座位号。
如果要弃票，填 0。
"""
    elif action_type == "kill":
        non_wolves = [p.seat_id for p in game.get_alive_players() if p.role.value != "werewolf"]
        targets_str = "、".join([f"{s}号" for s in non_wolves])
        phase_instruction = f"""
# 当前任务：狼人杀人
现在是夜晚，你和狼队友需要选择今晚要击杀的目标。
可选目标：{targets_str}
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
        phase_instruction = f"""
# 当前任务：女巫救人
今晚 {game.night_kill_target}号 被狼人杀害。
你有解药，是否要救他？
- 如果要救，在 action_target 中填写 {game.night_kill_target}
- 如果不救，在 action_target 中填写 0
"""
    elif action_type == "witch_poison":
        alive_others = [p.seat_id for p in game.get_alive_players() if p.seat_id != player.seat_id]
        targets_str = "、".join([f"{s}号" for s in alive_others])
        phase_instruction = f"""
# 当前任务：女巫毒人
你有毒药，是否要使用？
可选目标：{targets_str}
- 如果要毒人，在 action_target 中填写目标座位号
- 如果不使用，在 action_target 中填写 0
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
