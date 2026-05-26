from typing import Any, Dict, List, Optional


DIMENSIONS = {
    "x1": "情绪状态",
    "x2": "焦虑控制力",
    "x3": "生理状态",
    "x4": "行为与动力",
    "x5": "社交与支持",
    "x6": "认知与意义",
}

DIMENSION_KEYS = list(DIMENSIONS.keys())

POSITIVE_WORDS = ["开心", "轻松", "期待", "顺利", "喜欢", "舒服", "充实", "感谢", "还好", "不错", "平静"]
NEGATIVE_WORDS = ["难受", "焦虑", "压力", "崩溃", "失眠", "累", "痛苦", "烦", "害怕", "孤独", "自责", "没意义"]
BODY_WORDS = ["失眠", "睡不着", "头疼", "胃疼", "疲惫", "累", "吃不下", "心慌"]
SUPPORT_WORDS = ["朋友", "室友", "家人", "老师", "同学", "陪", "倾诉"]
MOTIVATION_WORDS = ["不想动", "拖延", "摆烂", "努力", "完成", "计划", "学习"]


def _clamp(value: float) -> int:
    return max(0, min(10, round(value)))


def _count(text: str, words: List[str]) -> int:
    return sum(text.count(word) for word in words)


def score_messages(messages: List[Dict[str, Any]]) -> Dict[str, int]:
    user_text = " ".join(str(m.get("content", "")) for m in messages if m.get("role") == "user")
    pos = _count(user_text, POSITIVE_WORDS)
    neg = _count(user_text, NEGATIVE_WORDS)
    body = _count(user_text, BODY_WORDS)
    support = _count(user_text, SUPPORT_WORDS)
    motivation = _count(user_text, MOTIVATION_WORDS)

    base = 6.5 + pos * 0.6 - neg * 0.55
    return {
        "x1": _clamp(base),
        "x2": _clamp(7.0 + pos * 0.3 - _count(user_text, ["焦虑", "害怕", "心慌", "崩溃"]) * 0.9),
        "x3": _clamp(7.0 - body * 0.8 + pos * 0.2),
        "x4": _clamp(6.5 + _count(user_text, ["努力", "完成", "计划", "学习"]) * 0.5 - _count(user_text, ["不想动", "拖延", "摆烂"]) * 0.7),
        "x5": _clamp(5.8 + support * 0.75 - _count(user_text, ["孤独", "没人", "一个人"]) * 0.7),
        "x6": _clamp(6.3 + motivation * 0.25 + pos * 0.25 - _count(user_text, ["没意义", "空", "迷茫"]) * 0.8),
    }


def overall_score(scores: Dict[str, int]) -> float:
    weights = {"x1": 0.15, "x2": 0.15, "x3": 0.1, "x4": 0.15, "x5": 0.2, "x6": 0.25}
    total = sum(scores.get(k, 5) * weights[k] for k in weights)
    return round(total * 10, 1)


def level_name(scores: Dict[str, int]) -> str:
    score = overall_score(scores)
    if score >= 85:
        return "能量充足"
    if score >= 70:
        return "状态稳定"
    if score >= 55:
        return "轻微波动"
    if score >= 40:
        return "需要照顾"
    return "建议求助"


def generate_reply(
    mode: str,
    user_text: str,
    messages: List[Dict[str, Any]],
    scores: Dict[str, int],
    character: Optional[Dict[str, str]] = None,
) -> str:
    low = overall_score(scores) < 55
    very_low = overall_score(scores) < 40
    user_text = user_text.strip()

    if mode == "companion" and character:
        name = character.get("name", "我")
        personality = character.get("personality", "温柔、认真陪伴")
        if very_low:
            return f"我是{name}，我会先陪你把这一刻撑过去。你刚刚说的我听见了，我们先不急着解决全部问题，先一起做一次很慢的呼吸，好吗？"
        if low:
            return f"我是{name}。按我的性格设定：{personality}，我会更想靠近你一点。你可以继续说，我会帮你把最乱的那一团慢慢拆开。"
        return f"我是{name}。听起来你心里有不少具体的感受，我会按“{personality}”的方式陪你聊。刚刚这件事里，最让你在意的是哪一小段？"

    if mode == "treehole":
        if very_low:
            return "谢谢你把这些放到树洞里。听起来你已经撑得很辛苦了，我会用很轻的声音陪着你。此刻先不要责备自己，能不能先告诉我：现在最压着你的，是事情本身，还是那种没有力气的感觉？"
        if low:
            return "我听见了，这不是一句“想开点”就能带过去的感受。你已经很努力地在描述它了。我们可以慢慢来：这件事里，最让你委屈或最消耗你的部分是什么？"
        return "你说得很清楚，我能感觉到你在认真整理今天的心情。这个树洞会先接住你，不急着评价。你愿意再说说，这件事后来给你留下了什么感觉吗？"

    user_turns = sum(1 for msg in messages if msg.get("role") == "user")
    if user_turns <= 1:
        return "我读到了今天的开头。为了更准确地做六维评估，我想再了解一点：这件事对你的情绪、身体状态和行动力分别有什么影响？"
    if user_turns <= 3:
        return "谢谢你继续补充。你的描述里已经能看到情绪、压力和支持系统的线索了。再问一个小问题：当这些感受出现时，你通常会怎么安抚自己，或者会找谁说一说？"
    return "信息已经比较完整了。我可以继续陪你聊，也可以根据目前的内容生成一份六维心理评估报告。"


def make_report(scores: Dict[str, int], messages: List[Dict[str, Any]]) -> str:
    score = overall_score(scores)
    level = level_name(scores)
    lines = [
        f"### 综合结果：{score} / 100（{level}）",
        "",
        "这份报告基于你在对话中表达的情绪、身体感受、压力线索、行动状态、支持系统和意义感做出轻量评估。",
        "",
    ]
    for key, name in DIMENSIONS.items():
        value = scores.get(key, 5)
        if value >= 8:
            comment = "表现较稳，是你现在可以依靠的资源。"
        elif value >= 5:
            comment = "有一些波动，但仍然保留着调节空间。"
        else:
            comment = "需要更多照顾，建议降低自我要求并寻求支持。"
        lines.append(f"- **{name}**：{value}/10，{comment}")

    lines.extend([
        "",
        "#### 温柔建议",
        "先挑一件最小、最容易完成的事做完，例如喝水、洗脸、出门走三分钟。等身体先回到比较安全的位置，再处理复杂问题。",
    ])
    return "\n".join(lines)
