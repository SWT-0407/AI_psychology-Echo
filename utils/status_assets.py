"""
状态资源管理模块
根据心理评分返回对应的 Emoji、评级、颜色和 AI 创作人设方向。
"""
import random


def get_status_assets(score, vals):
    """
    根据分数返回对应的 Emoji、评级、颜色和 AI 创作人设方向

    Args:
        score: float, 综合心理指数（0~100）
        vals: list, 六维评分 [x1, x2, x3, x4, x5, x6]

    Returns:
        tuple: (icon, level, color, direction)
            - icon: str, Emoji 图标
            - level: str, 状态评级名称
            - color: str, 主题颜色（十六进制）
            - direction: str, AI 创作人设方向描述
    """
    x3_physic = vals[2]  # 生理状态维度

    if score >= 85:
        icon = random.choice(["🌈", "✨", "🌟", "🌸", "🌻"])
        level, color = "能量迸发", "#81c784"
        direction = "人设：热血领路学长。方向：极致肯定，鼓励能量传承，文风燃且利落。"
    elif score >= 70:
        icon = random.choice(["☀️", "🌿", "😊", "🌼", "🦋"])
        level, color = "稳健前行", "#64b5f6"
        direction = "人设：温和治愈系好友。方向：认可现状，提供平衡生活的智慧，文风温暖。"
    elif score >= 55:
        icon = random.choice(["🍃", "☕", "🌤️", "📚", "🎵"])
        level, color = "微风荡漾", "#ffb74d"
        direction = "人设：懂生活的疗愈博主。方向：引导去内耗，建议'精神断舍离'，文风细腻。"
    elif score >= 40:
        icon = "🕯️" if x3_physic < 4.5 else random.choice(["🌧️", "🍵", "🩹", "🌫️", "🧸"])
        level, color = "蓄势待发", "#e57373"
        direction = "人设：深夜电台主播。方向：允许停顿与崩溃，深度共情疲惫，文风极其温柔。"
    else:
        icon = random.choice(["🤝", "🕊️", "☔", "💚", "🌱"])
        level, color = "静候天晴", "#ba68c8"
        direction = "人设：专业的心理守护者。方向：无条件接纳，紧急安抚，强调保护核心自我，文风坚定有力。"

    return icon, level, color, direction
