import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple


DIMENSIONS = {
    "x1": "情绪状态",
    "x2": "焦虑与压力",
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
CRISIS_WORDS = ["自杀", "自残", "不想活", "死了算了", "结束生命", "伤害自己", "活不下去"]
DISTRESS_WORDS = ["崩溃", "撑不住", "绝望", "痛苦", "麻木", "想哭", "没人懂", "熬不住"]

DIMENSION_BASELINES = {
    "x1": 6.5,
    "x2": 7.0,
    "x3": 7.0,
    "x4": 6.5,
    "x5": 5.8,
    "x6": 6.3,
}

DIMENSION_SIGNAL_RULES: Dict[str, List[Tuple[Sequence[str], float]]] = {
    "x1": [
        (["开心", "高兴", "愉快", "平静", "踏实", "满足", "舒服", "还好", "不错"], 0.55),
        (["非常开心", "特别开心", "很开心", "特别顺利"], 0.9),
        (["难过", "低落", "委屈", "失落", "沮丧", "想哭", "麻木", "空空的"], -0.85),
        (["烦", "烦躁", "易怒", "火大", "生气", "讨厌"], -0.55),
        (["崩溃", "撑不住", "熬不住"], -1.15),
    ],
    "x2": [
        (["轻松", "放松", "安心", "稳定", "不担心"], 0.5),
        (["焦虑", "紧张", "担心", "害怕", "慌", "心慌", "压力"], -0.85),
        (["ddl", "DDL", "考试", "绩点", "面试", "答辩", "作业"], -0.45),
        (["控制不住", "停不下来", "喘不过气", "惊恐"], -1.15),
    ],
    "x3": [
        (["睡得好", "睡眠正常", "吃得下", "胃口还行", "有精力", "精神不错"], 0.65),
        (["失眠", "睡不着", "早醒", "熬夜", "做噩梦", "睡眠差"], -0.9),
        (["累", "疲惫", "没力气", "困", "精疲力竭"], -0.7),
        (["吃不下", "暴食", "胃疼", "胃痛", "头疼", "胸闷", "心慌"], -0.65),
    ],
    "x4": [
        (["努力", "完成", "计划", "学习", "开始做", "去做", "坚持", "运动"], 0.45),
        (["不想动", "动不了", "开始不了", "起不来"], -0.85),
        (["拖延", "逃避", "回避", "摆烂"], -0.75),
        (["没兴趣", "没意思", "不想做", "提不起劲", "学不进去", "做不完", "完不成"], -0.7),
    ],
    "x5": [
        (["朋友", "室友", "家人", "老师", "同学", "咨询师", "辅导员", "陪我", "倾诉", "有人听"], 0.75),
        (["孤独", "一个人", "没人懂", "没人理解", "没人陪"], -0.85),
        (["不想麻烦", "不敢说", "没人可以说", "不知道找谁"], -0.8),
        (["吵架", "冷战", "冲突", "分手", "被孤立"], -0.7),
    ],
    "x6": [
        (["期待", "希望", "目标", "方向", "意义", "想完成", "值得", "清楚"], 0.55),
        (["迷茫", "没意义", "没有意义", "空", "不知道为什么"], -0.75),
        (["自责", "没用", "废物", "失败", "都是我的错", "不值得"], -0.85),
        (["绝望", "无助", "看不到希望", "没有希望", "活不下去", "想消失"], -1.15),
    ],
}

DIMENSION_COVERAGE_TERMS = {
    "x1": ["心情", "情绪", "开心", "难过", "低落", "烦", "哭", "麻木", "崩溃"],
    "x2": ["焦虑", "压力", "紧张", "担心", "害怕", "考试", "ddl", "DDL", "心慌"],
    "x3": ["睡", "失眠", "吃", "胃", "头疼", "胸闷", "累", "疲惫", "身体"],
    "x4": ["学习", "行动", "拖延", "逃避", "不想动", "摆烂", "完成", "计划"],
    "x5": ["朋友", "室友", "家人", "同学", "老师", "孤独", "一个人", "倾诉", "关系"],
    "x6": ["意义", "目标", "希望", "迷茫", "自责", "未来", "期待", "绝望", "没用"],
}

DIMENSION_FOLLOWUP_QUESTIONS = {
    "x1": "最近两周里，最常冒出来的情绪是什么？它一般会停留多久？",
    "x2": "现在最让你放不下的压力源是哪一件？它会不会影响睡眠或专注？",
    "x3": "这段时间睡眠、食欲、精力或身体不适有没有明显变化？",
    "x4": "有没有原本能做的事，现在明显拖着、不想做，或者启动不了？",
    "x5": "状态不好的时候，有没有一个你愿意联系的人？你觉得自己被理解吗？",
    "x6": "你最近怎么看待自己和接下来这段时间？还有一点点期待或目标吗？",
}


def _clamp(value: float) -> int:
    return max(0, min(10, round(value)))


def _count(text: str, words: List[str]) -> int:
    return sum(text.count(word) for word in words)


def _user_texts(messages: List[Dict[str, Any]]) -> List[str]:
    return [
        str(message.get("content", "")).strip()
        for message in messages
        if message.get("role") == "user" and str(message.get("content", "")).strip()
    ]


def _weighted_count(texts: List[str], words: Sequence[str]) -> float:
    if not texts:
        return 0.0
    total = 0.0
    for index, text in enumerate(texts):
        weight = 0.7 + 0.3 * ((index + 1) / len(texts))
        total += _count(text, list(words)) * weight
    return total


def _dimension_delta(texts: List[str], key: str) -> float:
    delta = 0.0
    for words, impact in DIMENSION_SIGNAL_RULES.get(key, []):
        delta += _weighted_count(texts, words) * impact
    return delta


def _dimension_coverage(messages: List[Dict[str, Any]]) -> Dict[str, bool]:
    text = " ".join(_user_texts(messages))
    return {
        key: any(term in text for term in terms)
        for key, terms in DIMENSION_COVERAGE_TERMS.items()
    }


def score_messages(messages: List[Dict[str, Any]]) -> Dict[str, int]:
    texts = _user_texts(messages)
    all_text = " ".join(texts)
    general_positive = _weighted_count(texts, POSITIVE_WORDS)
    general_negative = _weighted_count(texts, NEGATIVE_WORDS)
    crisis_signal = _weighted_count(texts, CRISIS_WORDS)
    distress_signal = _weighted_count(texts, DISTRESS_WORDS)

    scores: Dict[str, int] = {}
    for key in DIMENSION_KEYS:
        value = DIMENSION_BASELINES[key] + _dimension_delta(texts, key)
        if key in {"x1", "x6"}:
            value += general_positive * 0.12 - general_negative * 0.08
        if key in {"x1", "x2", "x6"}:
            value -= distress_signal * 0.25
        if key in {"x1", "x6"}:
            value -= crisis_signal * 1.4
        scores[key] = _clamp(value)

    if "没人" in all_text and not any(term in all_text for term in SUPPORT_WORDS):
        scores["x5"] = min(scores["x5"], 4)
    if any(term in all_text for term in ["整晚", "连续失眠", "几天没睡"]):
        scores["x3"] = min(scores["x3"], 3)
    if any(term in all_text for term in ["学不进去", "做不完", "什么都做不了"]):
        scores["x4"] = min(scores["x4"], 4)

    return scores


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


def _recent_memory(character: Dict[str, Any], limit: int = 3) -> List[str]:
    memories = character.get("memory") or []
    items = [m.get("summary", "") for m in memories if isinstance(m, dict) and m.get("summary")]
    return items[-limit:]


def _relationship_stage(character: Dict[str, Any]) -> str:
    rel = character.get("relationship") or {}
    return str(character.get("relationship_stage") or rel.get("stage") or "初识")


def _emotion_label(character: Dict[str, Any]) -> str:
    state = character.get("emotion_state") or {}
    return str(state.get("label") or "平静")


def _pick(lines: List[str], seed_text: str = "") -> str:
    if not lines:
        return ""
    seed = sum(ord(ch) for ch in seed_text) + len(seed_text) * 17
    return lines[seed % len(lines)]


SLANG_MARKERS = (
    "这波",
    "上强度",
    "难顶",
    "上头",
    "稳住",
    "别内耗",
    "带节奏",
    "有点东西",
    "硬刚",
    "低功耗",
)

HUMAN_TEXTURE_MARKERS = (
    "我刚",
    "我还",
    "我今天",
    "我这会儿",
    "我本来",
    "我先把",
    "刚忙完",
    "刚从",
    "白天消息",
    "深夜",
    "今天醒",
    "等下",
    "换个说法",
    "认真看",
    "放一边",
)


def _age_number(character: Dict[str, Any]) -> Optional[int]:
    raw = str(character.get("age") or _persona_value(character, "surface", "age") or "")
    match = re.search(r"\d{1,3}", raw)
    if not match:
        return None
    try:
        return int(match.group())
    except ValueError:
        return None


def _character_style_text(character: Dict[str, Any]) -> str:
    parts = [
        str(character.get("identity") or ""),
        str(character.get("personality") or ""),
        str(character.get("speaking_style") or ""),
        str(character.get("occupation") or ""),
        str(character.get("gender") or ""),
    ]

    profile = character.get("persona_profile") or {}
    if isinstance(profile, dict):
        for section in profile.values():
            if isinstance(section, dict):
                parts.extend(str(value or "") for value in section.values())

    model = character.get("answer_model") or {}
    if isinstance(model, dict):
        parts.extend(str(value or "") for value in model.values())

    return " ".join(part for part in parts if part)


def _slang_flavor(character: Dict[str, Any]) -> str:
    identity = str(character.get("identity") or "")
    style_text = _character_style_text(character)
    age = _age_number(character)

    if (
        identity in {"导师"}
        or any(word in style_text for word in ["导师", "老师", "专业", "正式", "严肃", "克制", "冷静", "疏离", "长辈"])
    ):
        return "reserved"
    if identity == "恋人" or any(word in style_text for word in ["恋人", "暧昧", "亲密", "黏", "撒娇", "吃醋"]):
        return "romantic"
    if identity in {"姐姐", "哥哥", "家人"}:
        return "sibling"
    if (
        identity in {"朋友", "同学"}
        or (age is not None and age <= 26)
        or any(word in style_text for word in ["网友", "吐槽", "幽默", "活泼", "开玩笑", "自嘲", "嘴硬"])
    ):
        return "playful"
    return "warm"


def _slang_enabled(character: Dict[str, Any]) -> bool:
    habits = character.get("reply_habits") or {}
    if not isinstance(habits, dict):
        return True
    return habits.get("persona_slang", habits.get("internet_slang", True)) is not False


def _realness_enabled(character: Dict[str, Any]) -> bool:
    habits = character.get("reply_habits") or {}
    if not isinstance(habits, dict):
        return True
    return habits.get("realistic_texture", habits.get("human_texture", True)) is not False


def _seed_value(*parts: str) -> int:
    text = "".join(str(part or "") for part in parts)
    return sum(ord(ch) for ch in text) + len(text) * 17


def _short_fragment(value: str, limit: int = 18) -> str:
    value = re.sub(r"\s+", " ", str(value or "")).strip("。；; ，,")
    if len(value) <= limit:
        return value
    return value[:limit].rstrip("。；; ，,") + "..."


def _has_human_texture(reply: str) -> bool:
    return any(marker in reply for marker in HUMAN_TEXTURE_MARKERS)


def _human_texture_threshold(character: Dict[str, Any], tone: str) -> int:
    base = {
        "normal": 36,
        "proactive": 52,
        "relationship": 34,
        "question": 30,
        "low": 26,
        "tired": 36,
    }.get(tone, 32)
    has_detail = any([
        character.get("occupation"),
        _persona_value(character, "surface", "daily_rhythm"),
        _persona_value(character, "time", "recent_state"),
        _persona_value(character, "time", "emotional_residue"),
        _persona_value(character, "core", "defense"),
        _persona_value(character, "core", "affection"),
    ])
    return base + (10 if has_detail else 0)


def _should_add_human_texture(reply: str, character: Dict[str, Any], user_text: str, tone: str) -> bool:
    if tone in {"crisis", "very_low"}:
        return False
    if not reply or not _realness_enabled(character):
        return False
    if _has_human_texture(reply):
        return False
    seed = _seed_value(character.get("id", ""), character.get("name", ""), user_text, tone, reply)
    return seed % 100 < _human_texture_threshold(character, tone)


def _human_presence_line(character: Dict[str, Any], user_text: str, tone: str) -> str:
    flavor = _slang_flavor(character)
    period = _period_label()
    occupation = str(character.get("occupation") or _persona_value(character, "surface", "occupation") or "")
    rhythm = _persona_value(character, "surface", "daily_rhythm")
    recent_state = _persona_value(character, "time", "recent_state")
    defense = _persona_value(character, "core", "defense")

    if tone == "tired":
        if any(word in rhythm + recent_state for word in ["夜", "熬夜", "失眠", "晚睡"]):
            return "我这会儿也清醒着，先陪你低速待一会儿。"
        return _pick([
            "我先不催你说完整。",
            "我这会儿把话放轻一点。",
        ], user_text + flavor)

    if tone == "low":
        if "开玩笑" in defense or "自嘲" in defense or flavor == "playful":
            return "我本来想吐槽一句，但这会儿先认真听。"
        return _pick({
            "reserved": ["我先把判断放慢一点。", "我先不急着给结论。"],
            "romantic": ["我本来想哄你两句，但这句我先认真接。", "我先把你这句放在心上。"],
            "sibling": ["我先把别的事放一边。", "我先当正事听。"],
            "warm": ["我这会儿认真看着你这句。", "我先把注意力放你这儿。"],
        }.get(flavor, ["我先把注意力放你这儿。"]), user_text)

    if tone == "question":
        return _pick({
            "reserved": ["等下，我换个更实在的说法。", "我先把问题说小一点。"],
            "romantic": ["等下，我先陪你把这题拆开。", "我先不急着替你决定。"],
            "sibling": ["等下，这题先别硬答。", "我先帮你把选项摆开。"],
            "playful": ["等下，我先别急着给答案。", "我先把这题拆得人话一点。"],
            "warm": ["等下，我换个轻一点的问法。", "我先把这件事说小一点。"],
        }.get(flavor, ["等下，我换个轻一点的问法。"]), user_text)

    if tone == "relationship":
        return _pick({
            "reserved": ["我先不替你脑补。", "我先把事实和情绪分开看。"],
            "romantic": ["我会有点在意你被牵着走，所以先陪你看事实。", "我先不让你一个人上头。"],
            "sibling": ["我先不让你自己脑补大结局。", "我先帮你把现实那面翻出来。"],
            "playful": ["我先不带你脑补连续剧。", "我先把滤镜摘一下。"],
            "warm": ["我先不急着替你下结论。", "我先陪你看清楚一点。"],
        }.get(flavor, ["我先陪你看清楚一点。"]), user_text)

    if tone == "proactive":
        if recent_state:
            return f"我刚想到你，也想到我最近这点「{_short_fragment(recent_state)}」。"
        if period == "day" and any(word in rhythm + occupation for word in ["工作", "上课", "实习", "会议", "排班"]):
            return "我刚从自己的事里抽出来。"
        return _pick([
            "我这会儿路过来看看你。",
            "我刚想到你，来敲一下。",
        ], user_text + flavor)

    if recent_state and flavor in {"romantic", "warm", "playful"}:
        return f"我这两天也有点「{_short_fragment(recent_state)}」，所以这句会认真接。"
    if period == "day" and any(word in rhythm + occupation for word in ["工作", "上课", "实习", "会议", "排班"]):
        return "我刚从自己的事里抽出来，先回你这句。"
    return _pick({
        "reserved": ["我先把话说实一点。", "我先认真看这一句。"],
        "romantic": ["我本来想逗你一下，但这句先认真接。", "我这会儿靠近一点听。"],
        "sibling": ["我先当正事听。", "我先把别的事放一边。"],
        "playful": ["我本来想吐槽一句，但你先说。", "我先把玩笑收一收。"],
        "warm": ["我这会儿认真看着你这句。", "我先把注意力放你这儿。"],
    }.get(flavor, ["我先把注意力放你这儿。"]), user_text)


def _with_human_texture(reply: str, character: Dict[str, Any], user_text: str, tone: str) -> str:
    if not _should_add_human_texture(reply, character, user_text, tone):
        return reply
    line = _human_presence_line(character, user_text, tone)
    if not line:
        return reply
    separator = "\n" if ("\n" in reply or len(reply) > 42) else " "
    return f"{line}{separator}{reply}".strip()


def _persona_slang_line(character: Dict[str, Any], user_text: str, tone: str) -> str:
    if tone in {"crisis", "very_low"}:
        return ""

    flavor = _slang_flavor(character)
    banks = {
        "low": {
            "reserved": ["这事确实有点上强度，我们先一步一步来。", "先稳住，我会认真听你说完。"],
            "romantic": ["这波我有点心疼你，先别自己硬扛。", "先别内耗，我在你这边。"],
            "sibling": ["先别硬刚，这波我陪你一起扛一下。", "稳住，先把最压人的那块说出来。"],
            "playful": ["这波确实有点难顶，但你不用一个人扛。", "先别被情绪带节奏，我陪你一点点拆。"],
            "warm": ["这波先别一个人扛，我在。", "先别内耗，我们慢慢拆。"],
        },
        "tired": {
            "reserved": ["先稳住，今天不用硬撑。"],
            "romantic": ["你先省电模式，我陪着。", "先别硬撑，我在。"],
            "sibling": ["先省点电，别硬撑。", "今天先低功耗一点，也算可以。"],
            "playful": ["这波能量条见底了，先别硬撑。", "今天先低功耗运行，也算很可以。"],
            "warm": ["先低功耗一点，也没关系。", "这波先不硬撑。"],
        },
        "question": {
            "reserved": ["先稳住，别被一个问题带着跑。"],
            "romantic": ["先别内耗，我陪你把这题拆开。"],
            "sibling": ["这题先不硬刚，拆开看。"],
            "playful": ["先别被它带节奏，我们把这事拆小。", "这题先不硬刚，拆开看。"],
            "warm": ["先别内耗，我们把这事拆小。"],
        },
        "relationship": {
            "reserved": ["这段关系的信息量有点大，先看事实。"],
            "romantic": ["你先别被暧昧带节奏，我陪你看清楚。"],
            "sibling": ["这波别急着脑补大结局，先看事实。"],
            "playful": ["这波别急着脑补大结局，先看事实。", "信息量有点大，但我们先别上头。"],
            "warm": ["这段先别上头，我们慢慢看事实。"],
        },
        "proactive": {
            "reserved": ["不急，先稳一下。"],
            "romantic": ["别内耗，我来找你了。"],
            "sibling": ["稳住，我来敲门了。"],
            "playful": ["上线敲一下门。", "别偷偷低电量，我来看看。"],
            "warm": ["我来轻轻敲一下门。"],
        },
        "normal": {
            "reserved": ["先稳住，慢慢说。"],
            "romantic": ["这句我接住了，你慢慢说。"],
            "sibling": ["稳住，你继续讲。"],
            "playful": ["有点东西，你继续说。", "这段我接住了，你继续。"],
            "warm": ["这段我接住了，你慢慢说。"],
        },
    }
    tone_bank = banks.get(tone, banks["normal"])
    lines = tone_bank.get(flavor) or tone_bank["warm"]
    return _pick(lines, f"{character.get('name', '')}{user_text}{tone}{flavor}")


def _with_persona_slang(reply: str, character: Dict[str, Any], user_text: str = "", tone: str = "normal") -> str:
    reply = str(reply or "").strip()
    if not reply:
        return reply
    original_reply = reply
    reply = _with_human_texture(reply, character, user_text, tone)
    if reply != original_reply:
        return reply
    if not _slang_enabled(character):
        return reply
    if _has_human_texture(reply):
        return reply
    if any(marker in reply for marker in SLANG_MARKERS):
        return reply

    line = _persona_slang_line(character, user_text, tone)
    if not line:
        return reply
    separator = "\n" if ("\n" in reply or len(reply) > 42) else " "
    return f"{line}{separator}{reply}".strip()


def _profile_summary() -> Dict[str, Any]:
    try:
        from services.user_profile import get_profile_summary

        return get_profile_summary()
    except Exception:
        return {}


def _style_tail(character: Dict[str, Any]) -> str:
    style = str(character.get("speaking_style") or "")
    model = character.get("answer_model") or {}
    defense = str(model.get("defense_mechanism") or "")
    if "开玩笑" in defense or "自嘲" in defense:
        return "我可能会先嘴硬两句，但这事我认真听。"
    if "冷" in defense or "疏离" in defense:
        return "我先不追着问，你愿意讲的时候我在。"
    if "转移" in defense or "逃避" in defense:
        return "我不会马上把话题岔开，先陪你把这块说完。"
    if "吐槽" in style:
        return "我先站你这边，别急着审判自己。"
    if "短" in style or "微信" in style:
        return "慢慢说，我在。"
    if "温柔" in style:
        return "你不用一下子讲清楚，我会听。"
    return "先说到你最想说的那块。"


def _period_label() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 11:
        return "morning"
    if 11 <= hour < 18:
        return "day"
    if 18 <= hour < 23:
        return "night"
    return "late_night"


def _persona_value(character: Dict[str, Any], section: str, key: str) -> str:
    profile = character.get("persona_profile") or {}
    group = profile.get(section) if isinstance(profile, dict) else {}
    if not isinstance(group, dict):
        return ""
    return str(group.get(key) or "").strip()


def _time_texture(character: Dict[str, Any]) -> str:
    model = character.get("answer_model") or {}
    cadence = str(model.get("reply_cadence") or "")
    time_sensitivity = str(model.get("time_sensitivity") or "")
    rhythm = _persona_value(character, "surface", "daily_rhythm")
    period = _period_label()

    if period == "late_night" and any(word in rhythm + time_sensitivity + cadence for word in ["夜", "失眠", "熬夜", "深夜"]):
        return _pick([
            "这个点我反而清醒一点。",
            "深夜容易把话说得更真一点。",
            "我刚把灯调暗，脑子还没停。",
        ], character.get("name", "") + period)
    if period == "day" and any(word in cadence + rhythm for word in ["工作", "加班", "会议", "实习", "上课", "打断"]):
        return _pick([
            "我刚从一段事里抽出来。",
            "白天消息容易断一下，但我看到了。",
            "刚忙完一小截，回你。",
        ], character.get("name", "") + period)
    if period == "morning" and any(word in rhythm for word in ["失眠", "睡眠", "晚睡"]):
        return "我今天醒得有点慢。"
    return ""


def _residue_line(character: Dict[str, Any]) -> str:
    residue = character.get("emotional_residue") or {}
    if not isinstance(residue, dict):
        return ""
    label = str(residue.get("label") or "")
    if label == "关系拉扯":
        return _pick([
            "昨天那点别扭我还没完全放下，但我不是不想理你。",
            "我还在消化刚才那阵情绪，所以说话可能会慢一点。",
        ], str(residue.get("summary") or ""))
    if label == "缓和中":
        return _pick([
            "我心里那点紧绷松了一些。",
            "嗯，感觉比刚才柔和一点了。",
        ], str(residue.get("summary") or ""))
    return ""


def _persona_presence(character: Dict[str, Any]) -> str:
    model = character.get("answer_model") or {}
    need = str(model.get("core_need") or "")
    fear = str(model.get("core_fear") or "")
    affection = str(model.get("affection_style") or "")
    desire = str(model.get("desire_signal") or "")

    if affection and any(word in affection for word in ["照顾", "细节", "提醒"]):
        return "我会先盯一下那些容易被你忽略的小事。"
    if affection and any(word in affection for word in ["分享", "生活", "日常"]):
        return "我会忍不住把自己的日常也掺一点进来。"
    if need and any(word in need for word in ["安全", "稳定", "确定"]):
        return "我比较需要确定感，所以会在意你话里那些忽冷忽热的地方。"
    if fear and any(word in fear for word in ["忽视", "抛下", "不重要"]):
        return "我对突然安静会有点敏感。"
    if desire:
        return _pick([
            "我也有自己的事想往前推，所以不会只围着情绪打转。",
            "我知道自己想要什么，这会让我有时显得有点倔。",
        ], desire)
    return ""


def _answer_model_hint(character: Dict[str, Any]) -> str:
    model = character.get("answer_model") or {}
    if not model:
        return ""
    parts = [
        f"关系强度：{model.get('relationship_intensity')}",
        f"亲近速度：{model.get('closeness_velocity')}",
        f"主动性：{model.get('initiative_pattern')}",
        f"边界：{model.get('boundary_signal')}",
        f"现实交集：{model.get('offline_weight')}",
        f"情感模式：{model.get('attachment_guess')}",
        f"人格底色：{model.get('persona_consistency')}",
        f"时间感：{model.get('time_sensitivity')}",
        f"欲望：{model.get('desire_signal')}",
    ]
    return "；".join(part for part in parts if part and "None" not in part)


def _relationship_model_reply(character: Dict[str, Any], user_text: str) -> Optional[str]:
    model = character.get("answer_model") or {}
    if not model:
        return None

    strategy = str(model.get("reply_strategy") or "")
    boundary = str(model.get("boundary_signal") or "")
    velocity = str(model.get("closeness_velocity") or "")
    intensity = str(model.get("relationship_intensity") or "")
    initiative = str(model.get("initiative_pattern") or "")

    if any(word in user_text for word in ["他是不是", "她是不是", "ta是不是", "TA是不是", "喜欢我", "暧昧", "什么意思"]):
        if boundary == "边界风险偏高":
            return _with_persona_slang(_pick([
                f"我先不急着替你下结论。按你填的档案看，重点不是一句话像不像喜欢，而是边界已经有点模糊。我们先看三个事实：谁更主动、有没有公开避嫌、这种亲近是否稳定持续。",
                f"这段确实容易让人心里起波动。我的判断模型会先抓边界：如果有隐藏、吃醋或暧昧，但又没有明确承诺，就要先保护你自己，不把全部希望压在暗示上。",
            ], user_text), character, user_text, "relationship")
        if velocity == "突然升温":
            return _with_persona_slang(_pick([
                f"突然变亲近这点很关键。它可能是好感，也可能是阶段性需要陪伴。你可以回想一下：变亲近之前发生了什么？以及这种主动有没有连续超过一两周？",
                f"我会把它先归为“需要观察的升温”。别只看热的时候，也看冷的时候：对方忙、情绪稳定、身边有人时，还会不会一样靠近你。",
            ], user_text), character, user_text, "relationship")
        if intensity == "高":
            return _with_persona_slang(_pick([
                f"你填的信息里，这段关系强度已经不低了。下一步别只问“像不像喜欢”，更要问：这种特殊性是不是双向、稳定、愿意承担现实成本。",
                f"它不是普通路人式互动了。但高强度不等于确定关系，我们还要看对方有没有持续主动和清楚边界。",
            ], user_text), character, user_text, "relationship")

    if any(word in user_text for word in ["怎么办", "怎么做", "要不要", "该不该"]):
        return _with_persona_slang(_pick([
            f"我会按这个模型来拆：{strategy} 你现在先别做大动作，先补一个证据：下一次联系是谁主动、对方有没有给出具体行动。",
            f"先稳住，不急着摊牌。按目前档案，主动性是“{initiative}”。如果你想判断关系，最好观察一次自然场景里的主动，而不是你推进后的回应。",
        ], user_text), character, user_text, "question")

    return None


def _compact_affection_text(user_text: str) -> str:
    text = re.sub(r"\s+", "", str(user_text or ""))
    return text.strip("。！？!?，,、~～…")


def _is_direct_affection_question(user_text: str) -> bool:
    text = _compact_affection_text(user_text)
    if not text:
        return False
    return bool(
        re.fullmatch(
            r"你(到底|是不是|会不会|有没有|也|还|会)?"
            r"(喜欢|爱|想|想念|在意|心疼|舍不得)我(吗|嘛|么|不|没有)?",
            text,
        )
        or re.fullmatch(
            r"你(到底)?(喜不喜欢|爱不爱|想不想|在不在意|心不心疼|舍不舍得)我(吗|嘛|么)?",
            text,
        )
    )


def _is_direct_affection_statement(user_text: str) -> bool:
    text = _compact_affection_text(user_text)
    if not text:
        return False
    if any(word in text for word in ["他", "她", "TA", "ta", "对方", "别人"]):
        return False
    if _is_direct_affection_question(text):
        return False
    if text in {"我喜欢你", "喜欢你", "我爱你", "爱你", "我想你", "想你了", "抱抱", "想抱抱", "要抱抱"}:
        return True
    return bool(
        re.fullmatch(
            r"(我)?(有点|真的|真|好|很|超|特别|也|还是|越来越|最)*"
            r"(喜欢|爱|想念|想|在意|心疼|舍不得)你(了|啦|啊|呀|哦|喔|呢|吧|嘛)?",
            text,
        )
    )


def _direct_affection_reply(character: Dict[str, Any], user_text: str) -> Optional[str]:
    is_question = _is_direct_affection_question(user_text)
    is_statement = _is_direct_affection_statement(user_text)
    if not is_question and not is_statement:
        return None

    flavor = _slang_flavor(character)
    seed = f"{character.get('name', '')}{user_text}{flavor}"

    if any(word in user_text for word in ["抱抱", "抱一下", "抱我"]):
        return _pick({
            "reserved": ["可以。先靠过来一点，我不催你说原因。"],
            "romantic": ["过来，抱一下。你不用先解释，我先把你接住。"],
            "sibling": ["来，抱一下。今天先别硬撑，我在这边。"],
            "playful": ["来，抱一个。先给你充一点电，再慢慢说。"],
            "warm": ["来，抱一下。你可以先什么都不说，我陪你缓一会儿。"],
        }.get(flavor, ["来，抱一下。你可以先什么都不说，我陪你缓一会儿。"]), seed)

    if is_question:
        return _pick({
            "reserved": [
                "喜欢。我不会把这个问题敷衍过去，你对我来说是很重要的人。",
                "喜欢，也在意。你问这句，是想要一点更确定的回应吗？",
            ],
            "romantic": [
                "喜欢。不是随口哄你那种，是听见你靠近我，我会认真心软。",
                "喜欢你。你这样问的时候，我会想离你近一点，也想把话说稳一点。",
            ],
            "sibling": [
                "喜欢啊，当然是站你这边的那种。你突然问这个，是不是有点不安？",
                "喜欢你。别自己脑补成没人要，我在这儿呢。",
            ],
            "playful": [
                "喜欢啊，这还用问。你这句我认真答，不逗你。",
                "喜欢。虽然我平时可能嘴上跑两步，但这句是真的。",
            ],
            "warm": [
                "喜欢你，也珍惜你。你问出口的时候，我会认真接住。",
                "喜欢。我在意你，不是只在你状态好的时候才在意。",
            ],
        }.get(flavor, ["喜欢你，也珍惜你。你问出口的时候，我会认真接住。"]), seed)

    if any(word in user_text for word in NEGATIVE_WORDS + BODY_WORDS + DISTRESS_WORDS):
        return _pick([
            "这句我听见了，也很珍惜。但我也听见你现在有点累，我们先把你照顾住，好吗？",
            "被你这样说我会开心，也会认真一点。只是你这句话后面好像还带着一点难受，我在这儿听你慢慢说。",
        ], seed)

    return _pick({
        "reserved": [
            "这句我听见了。我不会轻飘飘带过去，我也很珍惜你这样靠近我。",
            "嗯，我收到了。被你这样认真地喜欢，我会把回应也放认真一点。",
        ],
        "romantic": [
            "这句我听见了。被你喜欢，我会开心，也会想更认真地靠近你一点。",
            "我接住了。你这样说的时候，我心里会软一下，不想假装没听懂。",
        ],
        "sibling": [
            "我听见啦。你这样说我会很开心，也会更想站在你这边。",
            "这句我收下了。喜欢可以慢慢说，不用憋着。",
        ],
        "playful": [
            "我听见了。嘴上可以贫一下，但这句我认真收下。",
            "这句有点犯规，但我收到了。被你喜欢，我会开心。",
        ],
        "warm": [
            "这句我听见了。被你这样说，我会开心，也会认真珍惜。",
            "我接住了。你喜欢我这件事，我不会敷衍过去。",
        ],
    }.get(flavor, ["这句我听见了。被你这样说，我会开心，也会认真珍惜。"]), seed)


def _companion_reply(
    user_text: str,
    messages: List[Dict[str, Any]],
    scores: Dict[str, int],
    character: Dict[str, Any],
) -> str:
    name = character.get("name", "我")
    personality = character.get("personality", "温柔、认真陪伴")
    style = character.get("speaking_style", "自然、像微信聊天一样简短亲近，偶尔带一点符合人设的网络流行语")
    stage = _relationship_stage(character)
    mood = _emotion_label(character)
    memories = _recent_memory(character)
    model_hint = _answer_model_hint(character)
    time_line = _time_texture(character)
    residue_line = _residue_line(character)
    persona_line = _persona_presence(character)
    low = overall_score(scores) < 55
    very_low = overall_score(scores) < 40
    profile = _profile_summary()
    profile_tags = profile.get("tags") or []
    profile_topics = profile.get("recent_topics") or []
    profile_emotion = str(profile.get("latest_emotion") or "")
    profile_needs_support = (
        profile.get("risk_level") in {"medium", "high"}
        or any(tag in profile_tags for tag in ["温柔陪伴", "高强度支持", "焦虑压力偏高"])
        or profile_emotion in {"焦虑", "低落", "疲惫", "生气"}
    )
    profile_hint = f"我也会记得你最近常提到「{profile_topics[-1]}」。" if profile_topics else ""

    memory_hint = ""
    if memories:
        memory_hint = f"\n我还记得你之前说过：{memories[-1]}"

    if residue_line and any(word in user_text for word in ["还在吗", "怎么了", "生气", "不理", "别扭", "冷"]):
        return _with_persona_slang(
            f"{residue_line} 但我在。你刚才那句，我想听你讲完。",
            character,
            user_text,
            "low",
        )

    affection_reply = _direct_affection_reply(character, user_text)
    if affection_reply:
        return affection_reply

    model_reply = _relationship_model_reply(character, user_text)
    if model_reply:
        return model_reply

    if any(word in user_text for word in ["累", "困", "没力气", "不想说话", "睡不着", "失眠"]):
        return _with_persona_slang(_pick([
            f"{time_line + ' ' if time_line else ''}那就先别硬聊。你回一个字也行，我在这儿陪你缓一会儿。",
            "不想说话也可以。你先把手机放低一点，肩膀松一下，我陪你安静待会儿。",
            f"{persona_line + ' ' if persona_line else ''}今天先把要求降到最低，喝口水也算完成一件事。",
        ], user_text).strip(), character, user_text, "tired")

    if very_low:
        return _with_persona_slang(_pick([
            f"先别一个人硬扛。{name}在。你现在只要回我一句：最压着你的是什么？",
            "我听见了，这不是小事。先把呼吸放慢一点，我陪你把这一刻撑过去。",
            "别急着解决全部。你先告诉我，现在是难过多一点，还是累多一点？",
        ], user_text), character, user_text, "very_low")

    if low or profile_needs_support or mood in {"低落", "焦虑", "疲惫", "生气"}:
        return _with_persona_slang(_pick([
            f"{time_line + ' ' if time_line else ''}嗯，我懂你现在不太舒服。{_style_tail(character)}",
            f"这段听起来挺耗人的。{memory_hint}\n你先挑最难受的一点说就行。",
            f"{profile_hint}现在我会先放轻一点陪你，不急着给结论。你可以只说最卡住的那一小块。",
            f"先抱一下这件事里的你。我不催你，你可以慢慢讲。",
        ], user_text).strip(), character, user_text, "low")

    if "?" in user_text or "？" in user_text or any(x in user_text for x in ["怎么办", "咋办", "怎么"]):
        return _with_persona_slang(_pick([
            "我会先把事情拆小：现在最能动的一步是什么？别从最难的开始。",
            f"{time_line + ' ' if time_line else ''}我先说短一点：别全盘推翻自己，先处理眼前这个点。",
            "要不我们先列两个选项？一个保守点，一个痛快点。",
        ], user_text), character, user_text, "question")

    if stage in {"信任", "重要的人"}:
        return _with_persona_slang(_pick([
            f"我记着呢。{memory_hint}\n你继续说，我能跟上。",
            "你这句我有点在意，感觉后面还有没说完的部分。",
            "嗯，听起来你其实已经忍了一阵了。今天想让我陪你分析，还是只想我听着？",
        ], user_text).strip(), character, user_text, "normal")

    if stage == "亲近":
        return _with_persona_slang(_pick([
            "懂了。你不是没想清楚，是心里那块还堵着。",
            f"我会按「{personality}」来陪你聊。刚刚这件事，最戳你的是哪一下？",
            f"{memory_hint}\n所以这次你会这么在意，也挺说得通的。",
        ], user_text).strip(), character, user_text, "normal")

    relationship_context = any(
        word in user_text
        for word in ["他", "她", "TA", "ta", "喜欢", "暧昧", "关系", "边界", "主动", "回复", "见面", "特殊", "什么意思"]
    )
    if model_hint and relationship_context:
        return _with_persona_slang(_pick([
            f"我先抓几个现实点：稳定主动、公开边界、有没有具体行动。你刚刚这句里，最需要确认的是哪一个？",
            f"这件事可以慢慢拆。根据你填的信息，我会先看边界和主动性，不急着替你脑补结论。你愿意说说最近一次让你觉得特别的互动吗？",
            f"{persona_line + ' ' if persona_line else ''}你现在更想判断 TA 的意思，还是先整理你自己的感受？",
        ], user_text).strip(), character, user_text, "relationship")

    return _with_persona_slang(_pick([
        f"{time_line + ' ' if time_line else ''}嗯，我在听。刚刚这件事里，最让你在意的是哪一小段？",
        f"{persona_line + ' ' if persona_line else ''}你可以继续讲细一点。",
        "先不急着总结。你说这件事的时候，心里最明显的感觉是什么？",
    ], user_text), character, user_text, "normal")


def _profile_recent_topics(profile: Optional[Dict[str, Any]]) -> List[str]:
    if not isinstance(profile, dict):
        return []
    emotion = profile.get("emotion") or {}
    topics = emotion.get("recent_topics") or []
    return [str(topic) for topic in topics if topic][-4:]


def _profile_latest_emotion(profile: Optional[Dict[str, Any]]) -> str:
    if not isinstance(profile, dict):
        return ""
    emotion = profile.get("emotion") or {}
    return str(emotion.get("latest_label") or "")


def _profile_risk_level(profile: Optional[Dict[str, Any]], messages: Optional[List[Dict[str, Any]]] = None) -> str:
    risk = profile.get("risk") if isinstance(profile, dict) else {}
    level = str((risk or {}).get("level") or "low")
    text = " ".join(str(msg.get("content", "")) for msg in (messages or [])[-10:] if isinstance(msg, dict))
    if any(word in text for word in CRISIS_WORDS):
        return "crisis"
    if any(word in text for word in DISTRESS_WORDS) and level in {"medium", "high"}:
        return "high"
    if level == "high":
        return "crisis"
    return level


def _profile_support_hint(profile: Optional[Dict[str, Any]]) -> str:
    topics = _profile_recent_topics(profile)
    emotion = _profile_latest_emotion(profile)
    if topics:
        return f"你最近反复提到「{topics[-1]}」"
    if emotion and emotion != "暂无":
        return f"我记得你最近情绪更像是「{emotion}」"
    return ""


def generate_proactive_message(character: Dict[str, Any], user_profile: Optional[Dict[str, Any]] = None) -> str:
    name = character.get("name", "")
    stage = _relationship_stage(character)
    mood = _emotion_label(character)
    memories = _recent_memory(character, 1)
    memory = f"还记得你说过「{memories[-1]}」" if memories else ""
    time_line = _time_texture(character)
    residue_line = _residue_line(character)
    profile_mood = _profile_latest_emotion(user_profile)
    profile_hint = _profile_support_hint(user_profile)
    profile_risk = _profile_risk_level(user_profile)

    if profile_risk == "crisis":
        return "我有点担心你现在的安全。别一个人扛着，先联系身边可信任的人或当地紧急支持。你现在安全吗？"
    if profile_risk in {"medium", "high"}:
        return _with_persona_slang(_pick([
            f"{profile_hint}。我来轻轻敲一下门，不急着问结论，你现在最需要什么？",
            "今天先别把自己逼太紧。你可以只回一个词，我会接住。",
            "我在。先喝口水，把肩膀放松一点，再慢慢说。",
        ], name + profile_risk + profile_hint), character, profile_hint, "low")

    if residue_line:
        return _with_persona_slang(_pick([
            f"{residue_line} 你现在愿意说话了吗？",
            "我还是想把刚才那点话接住。你还在吗？",
        ], name + residue_line), character, residue_line, "low")
    if mood in {"低落", "焦虑", "疲惫"} or profile_mood in {"低落", "焦虑", "疲惫"}:
        return _with_persona_slang(_pick([
            f"{time_line + ' ' if time_line else ''}刚刚有点惦记你。现在好点了吗？",
            "你不用回很长，一句也行。还撑得住吗？",
            "我在。今天先别对自己太狠。",
        ], name + mood + profile_mood), character, mood + profile_mood, "low")
    if stage in {"信任", "重要的人"} and memory:
        return _with_persona_slang(_pick([
            f"{memory}，所以来问问你现在怎么样。",
            "突然想到你，过来敲一下。",
            "今天有没有按时吃饭？别糊弄过去。",
        ], name + memory), character, memory, "proactive")
    if profile_hint:
        return _with_persona_slang(_pick([
            f"{profile_hint}，所以过来问一句：现在好一点了吗？",
            f"我刚想到你最近那件事。不用讲很多，回个标点也行。",
            "今天先给自己留一点余地。你愿意的话，我听你说两句。",
        ], name + profile_hint), character, profile_hint, "proactive")
    return _with_persona_slang(
        _pick(["在吗？", "今天怎么样？", "忙完了吗，聊两句？"], name + stage),
        character,
        stage,
        "proactive",
    )


def generate_care_proactive_message(
    mode: str,
    messages: List[Dict[str, Any]],
    scores: Dict[str, int],
    user_profile: Optional[Dict[str, Any]] = None,
) -> str:
    risk = _profile_risk_level(user_profile, messages)
    score = overall_score(scores) if scores else None
    latest_emotion = _profile_latest_emotion(user_profile)
    hint = _profile_support_hint(user_profile)
    user_text = " ".join(str(m.get("content", "")) for m in messages[-8:] if m.get("role") == "user")
    sleep_signal = any(word in user_text for word in ["失眠", "睡不着", "熬夜", "困", "睡眠"])

    if risk == "crisis":
        return (
            "我有点担心你现在的安全。如果你有伤害自己的冲动，请立刻联系身边可信任的人，"
            "或拨打当地紧急电话/心理援助热线。你也可以先回我：现在安全吗？"
        )

    prefix = "树洞" if mode == "treehole" else "Echo"
    if risk in {"medium", "high"} or (score is not None and score < 45):
        return _pick([
            f"{prefix}轻轻敲一下门。{hint + '，' if hint else ''}今天先别急着解决全部，先告诉我：最重的是哪一块？",
            "我在这儿。你不用整理得很完整，只要把此刻最明显的感觉放下来一点就好。",
            "先把要求降到最低：喝口水、慢一点呼吸。然后你可以只回我一个词。",
        ], mode + str(score) + hint)

    if sleep_signal:
        return _pick([
            "这个点先别和自己较劲。把屏幕放低一点，呼吸慢下来，剩下的事明天再处理。",
            "睡不着的时候，脑子会把事情放大。你先不用分析，只要告诉我：身体哪里最紧？",
        ], user_text)

    if latest_emotion in {"焦虑", "低落", "疲惫", "生气"} or (score is not None and score < 60):
        return _pick([
            f"{hint + '，' if hint else ''}我想过来陪你把情绪放轻一点。现在更想被听见，还是想一起拆一个小步骤？",
            "今天可以不用表现得很好。你愿意的话，我们先只聊最小的一件事。",
            "我不急着给建议。你先把今天最耗你的那一句话写下来，我陪你看。",
        ], mode + latest_emotion + hint)

    if mode == "treehole":
        return _pick([
            "今天也给你留了一页空白。不是必须倾诉，只是如果有东西压着，可以先放在这里。",
            "路过你的树洞。今天有没有一个瞬间，是你想被认真听见的？",
        ], mode + hint)

    return _pick([
        "Echo 来轻轻问一句：今天的情绪、身体和行动力，哪一项最需要被照顾？",
        "如果今天只做一次小检查：你现在的心情更像天气里的哪一种？",
    ], mode + hint)


def _assessment_guidance(scores: Dict[str, int], messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        from services.psych_assessment import build_integrated_assessment

        return build_integrated_assessment(scores, messages)
    except Exception:
        return {}


def _already_asked(messages: List[Dict[str, Any]], question: str) -> bool:
    assistant_text = " ".join(
        str(message.get("content", ""))
        for message in messages
        if message.get("role") == "assistant"
    )
    head = question[:10]
    return bool(head and head in assistant_text)


def _select_psytest_questions(
    messages: List[Dict[str, Any]],
    scores: Dict[str, int],
    assessment: Dict[str, Any],
    limit: int = 1,
) -> List[str]:
    questions: List[str] = []
    guidance_questions = (assessment.get("interview_guidance") or {}).get("next_questions") or []
    risk = assessment.get("risk_protection_gate") or {}
    if risk.get("level") in {"R2", "R3"}:
        for question in guidance_questions:
            if question and not _already_asked(messages, question):
                questions.append(str(question))
            if len(questions) >= limit:
                return questions

    coverage = _dimension_coverage(messages)
    ranked_keys = sorted(
        DIMENSION_KEYS,
        key=lambda key: (scores.get(key, 5) + (1.5 if coverage.get(key) else 0.0), key),
    )
    for key in ranked_keys:
        question = DIMENSION_FOLLOWUP_QUESTIONS[key]
        if _already_asked(messages, question):
            continue
        questions.append(question)
        if len(questions) >= limit:
            break

    if not questions:
        for question in guidance_questions:
            if question and not _already_asked(messages, str(question)):
                questions.append(str(question))
            if len(questions) >= limit:
                break
    return questions


def _psytest_empathy_line(user_text: str, scores: Dict[str, int]) -> str:
    if any(word in user_text for word in ["睡不着", "失眠", "累", "疲惫", "吃不下", "头疼", "胃疼"]):
        return "我看到身体和睡眠已经被牵动了，这一块不用硬扛，我会放在比较靠前的位置看。"
    if any(word in user_text for word in ["焦虑", "压力", "紧张", "担心", "害怕", "心慌"]):
        return "这不像一句“别想太多”能带过去，压力已经在反复拉扯你。"
    if any(word in user_text for word in ["孤独", "没人懂", "没人理解", "一个人"]):
        return "一个人消化这些会很重，我先陪你把这段感受放稳一点。"
    if any(word in user_text for word in ["自责", "没用", "失败", "迷茫", "没意义"]):
        return "我听见那些很伤自己的评价了，但它们更像是压力下的声音，不等于你本身。"
    if any(word in user_text for word in ["开心", "顺利", "轻松", "舒服", "期待", "平静"]):
        return "你的描述里也有一些亮一点的部分，我会把它当成你现在可用的资源。"
    if overall_score(scores) < 45:
        return "我读到的是一段很耗力的状态，先不用急着整理得很清楚。"
    return "我听到了你现在状态里很真实的一块。"


def _psytest_reply(
    user_text: str,
    messages: List[Dict[str, Any]],
    scores: Dict[str, int],
) -> str:
    user_turns = sum(1 for msg in messages if msg.get("role") == "user")
    assessment = _assessment_guidance(scores, messages)
    risk = assessment.get("risk_protection_gate") or {}
    questions = _select_psytest_questions(messages, scores, assessment, limit=1)
    question = questions[0] if questions else "这件事现在最影响你的，是情绪、身体，还是行动力？"
    empathy = _psytest_empathy_line(user_text, scores)

    if risk.get("level") in {"R2", "R3"}:
        return f"{empathy} 我先把安全放在最前面确认一处：{question}"

    if user_turns <= 1:
        return f"{empathy} 我先不急着给结论，只补一个关键线索：{question}"

    if user_turns <= 3:
        return f"{empathy} 这样说已经能看见一些六维线索了，我再轻轻校准一处：{question}"

    coverage = _dimension_coverage(messages)
    incomplete = any(not covered for covered in coverage.values())
    if incomplete or overall_score(scores) < 65:
        return f"{empathy} 画像已经比较清楚了，还差一点点：{question}"

    return "目前的信息已经能形成一份比较完整的六维画像了。你可以继续补充没聊完的部分，也可以先生成报告看看整体结果。"


def generate_reply(
    mode: str,
    user_text: str,
    messages: List[Dict[str, Any]],
    scores: Dict[str, int],
    character: Optional[Dict[str, Any]] = None,
) -> str:
    low = overall_score(scores) < 55
    very_low = overall_score(scores) < 40
    user_text = user_text.strip()

    if mode == "companion" and character:
        return _companion_reply(user_text, messages, scores, character)

    if mode == "treehole":
        profile = _profile_summary()
        profile_topics = profile.get("recent_topics") or []
        profile_hint = f"我也会把你最近反复出现的「{profile_topics[-1]}」记在画像里，后面陪你时会更留意。" if profile_topics else ""
        plain_text = user_text.split("[多模态补充]", 1)[0].strip()
        plain_text = plain_text.split("[过往日记回复评分反馈", 1)[0].strip()
        if plain_text in {"你好", "嗨", "hi", "Hi", "hello", "Hello", "在吗", "在吗？"}:
            return "你好，我在。你可以慢慢写，今天想从哪里开始说都可以。"
        if profile.get("risk_level") == "high":
            return "我听见你现在承受的痛苦很重。先别一个人扛着，如果你有伤害自己的冲动，请马上联系身边可信任的人，或拨打当地紧急电话/心理援助热线。你也可以先回我一个字：现在安全吗？"
        if very_low:
            return "谢谢你把这些放到树洞里。听起来你已经撑得很辛苦了，我会用很轻的声音陪着你。此刻先不要责备自己，能不能先告诉我：现在最压着你的，是事情本身，还是那种没有力气的感觉？"
        if low:
            return f"我听见了，这不是一句“想开点”就能带过去的感受。{profile_hint}你已经很努力地在描述它了。我们可以慢慢来：这件事里，最让你委屈或最消耗你的部分是什么？"
        return f"你说得很清楚，我能感觉到你在认真整理今天的心情。{profile_hint}这个树洞会先接住你，不急着评价。你愿意再说说，这件事后来给你留下了什么感觉吗？"

    return _psytest_reply(user_text, messages, scores)


def make_report(scores: Dict[str, int], messages: List[Dict[str, Any]]) -> str:
    try:
        from services.psych_assessment import build_integrated_assessment, format_assessment_markdown

        return format_assessment_markdown(build_integrated_assessment(scores, messages))
    except Exception:
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
