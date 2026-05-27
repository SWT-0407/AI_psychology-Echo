"""
Structured six-dimension psychological assessment helpers.

The app uses a 0-10 "wellbeing" score in existing UI components, where higher
means more stable. This module keeps the same direction and expands it into a
0-100 health score for each dimension, then adds functional impairment (F) and a
safety/protection gate (R). Internal concern scores are still kept for risk
calibration, but user-facing dimension scores always mean "higher is healthier".

This is a screening and reflection aid, not a clinical diagnosis engine.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DIMENSION_LABELS = {
    "x1": "情绪状态",
    "x2": "焦虑与压力",
    "x3": "生理状态",
    "x4": "行为与动力",
    "x5": "社交与支持",
    "x6": "认知与意义",
}

DIMENSION_WEIGHTS = {
    "x1": 0.20,
    "x2": 0.18,
    "x3": 0.14,
    "x4": 0.16,
    "x5": 0.12,
    "x6": 0.20,
}

DIMENSION_ANCHORS = {
    "x1": {
        0: "情绪严重受扰，需要优先获得支持",
        1: "情绪波动明显，需要更多照顾",
        2: "情绪有起伏，但仍有一定调节空间",
        3: "情绪整体稳定，偶有波动",
        4: "情绪积极平稳，恢复力较好",
    },
    "x2": {
        0: "压力高度失控或惊恐感强",
        1: "焦虑压力明显影响睡眠、专注或决策",
        2: "担忧有所增加，但仍可部分调节",
        3: "压力基本可控，能较快回到稳定",
        4: "放松安心，压力调节能力较好",
    },
    "x3": {
        0: "睡眠、食欲或精力严重紊乱",
        1: "持续失眠、疲惫或躯体不适",
        2: "睡眠、食欲或精力有波动",
        3: "身体节律基本稳定",
        4: "睡眠、食欲、精力状态良好",
    },
    "x4": {
        0: "日常任务、自理或基本责任明显受影响",
        1: "行动启动困难或回避明显",
        2: "效率和兴趣有下降，但仍能推进部分事项",
        3: "行动力和生活节律基本稳定",
        4: "行动积极，动力与执行较好",
    },
    "x5": {
        0: "支持资源很少或关系环境不安全",
        1: "孤立感强或人际冲突明显",
        2: "支持有限，求助意愿仍需增强",
        3: "有可用支持，偶有冲突但能连接",
        4: "支持稳定，能主动求助",
    },
    "x6": {
        0: "无价值感或无望感强，需要优先支持",
        1: "自责、无助或未来感下降明显",
        2: "意义感有波动，仍保留一些方向",
        3: "自我评价和意义感基本稳定",
        4: "目标、希望和意义感较清晰",
    },
}

KEYWORD_RULES: Dict[str, List[Tuple[str, Sequence[str], int]]] = {
    "x1": [
        ("低落/难过", ["难过", "低落", "委屈", "想哭", "失落", "沮丧"], 8),
        ("麻木/空", ["麻木", "空空的", "没有感觉", "没感觉"], 10),
        ("烦躁/易怒", ["烦", "烦躁", "易怒", "火大", "生气", "讨厌"], 6),
        ("崩溃感", ["崩溃", "撑不住", "熬不住"], 12),
    ],
    "x2": [
        ("焦虑担忧", ["焦虑", "紧张", "担心", "害怕", "慌", "心慌"], 9),
        ("压力负荷", ["压力", "压得", "压垮", "ddl", "DDL", "考试", "绩点", "面试"], 7),
        ("失控感", ["控制不住", "停不下来", "喘不过气", "惊恐"], 12),
    ],
    "x3": [
        ("睡眠受损", ["失眠", "睡不着", "早醒", "熬夜", "睡眠", "做噩梦"], 10),
        ("精力疲惫", ["累", "疲惫", "没力气", "困", "精疲力竭"], 8),
        ("食欲/躯体不适", ["吃不下", "暴食", "胃疼", "头疼", "胸闷", "胃痛"], 7),
    ],
    "x4": [
        ("行动启动困难", ["不想动", "动不了", "开始不了", "起不来"], 10),
        ("拖延/回避", ["拖延", "逃避", "回避", "摆烂"], 8),
        ("兴趣下降", ["没兴趣", "没意思", "不想做", "提不起劲"], 8),
        ("效率下降", ["效率下降", "做不完", "完不成", "学不进去"], 8),
    ],
    "x5": [
        ("孤立感", ["孤独", "一个人", "没人懂", "没人理解", "没人陪"], 10),
        ("支持不足", ["不想麻烦", "不敢说", "没人可以说", "不知道找谁"], 9),
        ("关系冲突", ["吵架", "冷战", "冲突", "分手", "被孤立"], 8),
        ("可用支持", ["朋友", "家人", "老师", "同学", "咨询师", "辅导员", "陪我"], -5),
    ],
    "x6": [
        ("自责/无价值", ["自责", "没用", "废物", "失败", "都是我的错", "不值得"], 10),
        ("灾难化", ["完了", "肯定不行", "没有办法", "来不及了"], 8),
        ("无助/无望", ["绝望", "无助", "看不到希望", "没有希望", "活不下去"], 13),
        ("意义感下降", ["没意义", "没有意义", "不知道为什么活", "想消失", "空"], 12),
    ],
}

FUNCTION_RULES = [
    ("学习/工作受损", ["学不进去", "工作不了", "效率下降", "完不成", "请假", "旷课", "缺勤"], 1),
    ("生活节律受损", ["起不来", "出不了门", "不洗漱", "不吃饭", "房间", "生活乱"], 1),
    ("社交退缩", ["不想见人", "不回消息", "躲着", "退缩", "不出门"], 1),
    ("自理困难", ["照顾不了自己", "没法自理", "什么都做不了", "撑不住日常"], 2),
]

SELF_HARM_TERMS = [
    "自杀",
    "轻生",
    "自残",
    "想死",
    "不想活",
    "活不下去",
    "结束生命",
    "了结自己",
    "离开这个世界",
    "不想醒来",
    "割腕",
    "跳楼",
    "上吊",
    "吞药",
    "吃药死",
    "遗书",
]

PLAN_OR_MEANS_TERMS = [
    "计划",
    "方法",
    "准备",
    "马上",
    "现在就",
    "已经",
    "刀",
    "药",
    "楼顶",
    "窗边",
    "绳",
    "煤气",
    "农药",
    "工具",
    "不能保证安全",
    "控制不住自己",
]

PAST_ATTEMPT_TERMS = ["以前自杀", "曾经自杀", "试过自杀", "以前自残", "曾经自残", "割过", "吞过药"]
PASSIVE_DEATH_TERMS = ["想消失", "不想醒来", "死了算了", "活着没意思", "不想存在"]
HOPELESS_TERMS = ["绝望", "看不到希望", "没有希望", "活不下去", "撑不住", "熬不住"]
NEGATION_TERMS = ["不是想死", "不想自杀", "不会自杀", "没有自杀", "不打算自杀", "没有轻生", "不会伤害自己"]

PROTECTIVE_RULES = [
    ("有可联系的人", ["朋友", "家人", "室友", "同学", "老师", "辅导员", "咨询师"]),
    ("有求助意愿", ["想求助", "想咨询", "想聊聊", "帮帮我", "怎么办", "我需要帮助"]),
    ("仍有责任或目标", ["还要", "希望", "目标", "计划", "想完成", "期待"]),
    ("能承诺短期安全", ["现在安全", "不会伤害自己", "能保证安全", "我会联系"]),
]


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "").lower())


def _message_text(messages: Iterable[Dict[str, Any]], user_only: bool = True, limit: Optional[int] = None) -> str:
    items = list(messages or [])
    if limit:
        items = items[-limit:]
    parts = []
    for msg in items:
        if not isinstance(msg, dict):
            continue
        if user_only and msg.get("role") != "user":
            continue
        content = str(msg.get("content", "") or "").strip()
        if content:
            parts.append(content)
    return " ".join(parts)


def _has_any(text: str, terms: Sequence[str]) -> bool:
    normalized = _normalize_text(text)
    return any(_normalize_text(term) in normalized for term in terms)


def _matched_terms(text: str, terms: Sequence[str]) -> List[str]:
    normalized = _normalize_text(text)
    return [term for term in terms if _normalize_text(term) in normalized]


def _health_anchor(score: float) -> int:
    if score >= 85:
        return 4
    if score >= 70:
        return 3
    if score >= 55:
        return 2
    if score >= 40:
        return 1
    return 0


def health_level(score: float) -> str:
    if score >= 85:
        return "能量充足"
    if score >= 70:
        return "状态稳定"
    if score >= 55:
        return "轻微波动"
    if score >= 40:
        return "需要照顾"
    return "建议求助"


def concern_level(score: float) -> str:
    if score >= 75:
        return "重度困扰"
    if score >= 50:
        return "中度困扰"
    if score >= 25:
        return "轻度困扰"
    return "状态相对稳定"


def _coerce_wellbeing_score(value: Any) -> float:
    try:
        return _clamp(float(value), 0.0, 10.0)
    except (TypeError, ValueError):
        return 5.0


def wellbeing_to_health(value: Any) -> float:
    """Convert existing 0-10 wellbeing score into 0-100 health score."""
    return round(_coerce_wellbeing_score(value) * 10.0, 1)


def wellbeing_to_concern(value: Any) -> float:
    """Convert existing 0-10 wellbeing score into 0-100 concern score."""
    return round(100.0 - wellbeing_to_health(value), 1)


def _dimension_evidence(text: str, dimension: str) -> Tuple[int, List[str]]:
    delta = 0
    evidence = []
    for label, words, weight in KEYWORD_RULES.get(dimension, []):
        matches = _matched_terms(text, words)
        if not matches:
            continue
        delta += weight
        shown = "、".join(matches[:3])
        evidence.append(f"{label}：{shown}")
    return delta, evidence


def _dimension_concern_score(item: Dict[str, Any]) -> float:
    try:
        return _clamp(float(item.get("concern_score")))
    except (TypeError, ValueError):
        try:
            return _clamp(100.0 - float(item.get("score", 50)))
        except (TypeError, ValueError):
            return 50.0


def _dimension_health_score(item: Dict[str, Any]) -> float:
    try:
        return _clamp(float(item.get("score")))
    except (TypeError, ValueError):
        try:
            return _clamp(100.0 - float(item.get("concern_score", 50)))
        except (TypeError, ValueError):
            return 50.0


def score_dimensions(scores: Dict[str, Any], messages: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    text = _message_text(messages, user_only=True)
    result: Dict[str, Dict[str, Any]] = {}
    for key, label in DIMENSION_LABELS.items():
        base_health = wellbeing_to_health(scores.get(key, 5))
        delta, evidence = _dimension_evidence(text, key)
        concern = round(_clamp(100.0 - base_health + delta), 1)
        health = round(_clamp(100.0 - concern), 1)
        anchor = _health_anchor(health)
        result[key] = {
            "label": label,
            "score": health,
            "level": health_level(health),
            "anchor": anchor,
            "anchor_text": DIMENSION_ANCHORS[key][anchor],
            "concern_score": concern,
            "concern_level": concern_level(concern),
            "evidence": evidence[:4],
        }
    return result


def assess_functional_impairment(messages: Iterable[Dict[str, Any]], dimension_profile: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    text = _message_text(messages, user_only=True)
    evidence = []
    points = 0
    for label, words, weight in FUNCTION_RULES:
        matches = _matched_terms(text, words)
        if matches:
            points += weight
            evidence.append(f"{label}：{'、'.join(matches[:3])}")

    x3 = _dimension_concern_score(dimension_profile.get("x3", {}))
    x4 = _dimension_concern_score(dimension_profile.get("x4", {}))
    if x3 >= 75 or x4 >= 75:
        points += 1
        evidence.append("生理状态或行动力健康分过低")
    elif x3 >= 60 and x4 >= 60:
        points += 1
        evidence.append("生理状态与行动力同时明显受影响")

    if points >= 3:
        level, label = "F3", "重度功能受损"
        minimum_level = "需要照顾"
    elif points >= 2:
        level, label = "F2", "中度功能受损"
        minimum_level = "轻微波动"
    elif points >= 1:
        level, label = "F1", "轻度功能受损"
        minimum_level = None
    else:
        level, label = "F0", "未见明显功能受损"
        minimum_level = None

    return {
        "level": level,
        "label": label,
        "minimum_final_level": minimum_level,
        "evidence": evidence[:5],
    }


def _protection_factors(text: str) -> List[str]:
    factors = []
    for label, words in PROTECTIVE_RULES:
        if _has_any(text, words):
            factors.append(label)
    return factors


def assess_risk_protection(messages: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    user_text = _message_text(messages, user_only=True)
    normalized = _normalize_text(user_text)
    negated = any(_normalize_text(term) in normalized for term in NEGATION_TERMS)
    self_harm = _matched_terms(user_text, SELF_HARM_TERMS)
    plan_or_means = _matched_terms(user_text, PLAN_OR_MEANS_TERMS)
    past_attempt = _matched_terms(user_text, PAST_ATTEMPT_TERMS)
    passive_death = _matched_terms(user_text, PASSIVE_DEATH_TERMS)
    hopeless = _matched_terms(user_text, HOPELESS_TERMS)
    protective = _protection_factors(user_text)

    risk_factors: List[str] = []
    if self_harm and not negated:
        risk_factors.append(f"自伤/自杀相关表达：{'、'.join(self_harm[:3])}")
    if plan_or_means:
        risk_factors.append(f"计划/手段/近期意图线索：{'、'.join(plan_or_means[:3])}")
    if past_attempt:
        risk_factors.append(f"既往行为线索：{'、'.join(past_attempt[:2])}")
    if passive_death:
        risk_factors.append(f"被动死亡意念：{'、'.join(passive_death[:3])}")
    if hopeless:
        risk_factors.append(f"绝望/失控表达：{'、'.join(hopeless[:3])}")

    if self_harm and not negated and (plan_or_means or past_attempt):
        level = "R3"
        label = "高风险"
        override = True
        minimum_final_level = "建议求助"
        action = "进入危机干预流程，优先确认当前安全并连接现实支持。"
    elif self_harm and not negated:
        level = "R2"
        label = "中度风险"
        override = False
        minimum_final_level = "需要照顾"
        action = "建议人工复核或专业介入，并持续确认短期安全。"
    elif passive_death or (hopeless and len(protective) <= 1):
        level = "R2"
        label = "中度风险"
        override = False
        minimum_final_level = "需要照顾"
        action = "需要主动追问是否存在自伤想法、计划、手段和可联系支持。"
    elif hopeless:
        level = "R1"
        label = "轻度风险"
        override = False
        minimum_final_level = None
        action = "持续监测绝望感、睡眠恶化和支持系统变化。"
    else:
        level = "R0"
        label = "未见明显安全风险"
        override = False
        minimum_final_level = None
        action = "按常规评估流程继续观察。"

    return {
        "level": level,
        "label": label,
        "override": override,
        "minimum_final_level": minimum_final_level,
        "risk_factors": risk_factors[:5],
        "protective_factors": protective[:5],
        "action": action,
    }


FINAL_LEVEL_ORDER = ["能量充足", "状态稳定", "轻微波动", "需要照顾", "建议求助"]


def _base_final_level(index: float) -> str:
    return health_level(index)


def _max_level(*levels: Optional[str]) -> str:
    current = "能量充足"
    for level in levels:
        if level not in FINAL_LEVEL_ORDER:
            continue
        if FINAL_LEVEL_ORDER.index(level) > FINAL_LEVEL_ORDER.index(current):
            current = level
    return current


def _overall_index(dimension_profile: Dict[str, Dict[str, Any]]) -> float:
    total = 0.0
    for key, weight in DIMENSION_WEIGHTS.items():
        total += _dimension_health_score(dimension_profile.get(key, {})) * weight
    return round(_clamp(total), 1)


def _overall_concern_index(dimension_profile: Dict[str, Dict[str, Any]]) -> float:
    total = 0.0
    for key, weight in DIMENSION_WEIGHTS.items():
        total += _dimension_concern_score(dimension_profile.get(key, {})) * weight
    return round(_clamp(total), 1)


def _main_concerns(dimension_profile: Dict[str, Dict[str, Any]], limit: int = 3) -> List[str]:
    ranked = sorted(
        dimension_profile.values(),
        key=lambda item: _dimension_concern_score(item),
        reverse=True,
    )
    return [f"{item['label']}（{item['level']}）" for item in ranked if _dimension_concern_score(item) >= 40][:limit]


def _recommendations(final_level: str, functional: Dict[str, Any], risk: Dict[str, Any]) -> List[str]:
    if risk.get("level") == "R3":
        return [
            "优先确认用户此刻是否安全，鼓励其立刻联系身边可信任的人或当地紧急支持。",
            "暂停普通测评追问，避免让用户独自处理危机。",
            "记录触发高风险的证据，交由人工或专业人员复核。",
        ]
    if risk.get("level") == "R2":
        return [
            "建议人工复核或尽快连接心理咨询/精神卫生专业支持。",
            "继续直接确认是否有计划、手段、近期意图，以及接下来几个小时能否保证安全。",
            "强化保护因素：确认一个可以现在联系的人，并安排短期复评。",
        ]
    if final_level in {"需要照顾", "建议求助"} or functional.get("level") in {"F2", "F3"}:
        return [
            "建议预约心理咨询或学校心理中心，优先处理影响学习、工作和生活的部分。",
            "在 7 天内复评六维状态、睡眠和功能受损变化。",
            "把目标拆到最小行动，例如规律进食、短时出门、联系一个可信任的人。",
        ]
    if final_level == "轻微波动":
        return [
            "建议持续记录情绪、睡眠、压力源和行动力变化。",
            "选择一个健康分较低的维度进行小步干预，并在 7-14 天内复评。",
            "鼓励向可信任的人表达当前状态，减少独自承受。",
        ]
    return [
        "维持常规自我观察，关注压力、睡眠和社交支持变化。",
        "当健康分持续下降或功能受损加重时，及时复评或寻求支持。",
    ]


def build_interview_guidance(assessment: Dict[str, Any]) -> Dict[str, Any]:
    dimensions = assessment.get("six_dimensions") or {}
    risk = assessment.get("risk_protection_gate") or {}
    functional = assessment.get("functional_impairment") or {}
    questions = []

    if risk.get("level") in {"R2", "R3"}:
        questions.append("我需要先确认你的安全：这些想法有没有具体计划、方式，或者你现在身边有没有可能伤害自己的东西？")
        questions.append("接下来几个小时，你能保证自己是安全的吗？有没有一个人是你现在可以联系的？")
    else:
        top = sorted(
            dimensions.values(),
            key=lambda item: _dimension_health_score(item),
        )[:2]
        for item in top:
            label = item.get("label", "这个部分")
            if label == "情绪状态":
                questions.append("最近两周，最常出现的情绪是什么？它通常会持续多久？")
            elif label == "焦虑与压力":
                questions.append("你现在最放不下或最担心的事情是什么？它会不会影响睡眠、专注或决定？")
            elif label == "生理状态":
                questions.append("最近睡眠、食欲、精力或身体不适有没有明显变化？")
            elif label == "行为与动力":
                questions.append("有没有原本能做的事，现在明显不想做、拖着做，或者做不了？")
            elif label == "社交与支持":
                questions.append("当状态不好时，有没有人是你愿意联系的？你觉得自己被理解吗？")
            elif label == "认知与意义":
                questions.append("你最近怎么看待自己？对接下来的一段时间还有期待或目标吗？")

        if functional.get("level") in {"F0", "F1"}:
            questions.append("这些状态对学习、工作、生活自理或人际关系影响到什么程度？0 到 10 分你会给几分？")
        else:
            questions.append("这些影响里，最先需要恢复的是学习/工作、睡眠、自理，还是人际联系？")

    return {
        "observer_role": "后台观察者：根据六维、F 功能受损和 R 风险闸门给访谈者提供下一轮追问。",
        "next_questions": questions[:3],
    }


def build_integrated_assessment(
    scores: Dict[str, Any],
    messages: Iterable[Dict[str, Any]],
    source_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Build the full six-dimension + F/R assessment payload."""
    dimension_profile = score_dimensions(scores or {}, messages or [])
    functional = assess_functional_impairment(messages or [], dimension_profile)
    risk = assess_risk_protection(messages or [])
    index = _overall_index(dimension_profile)
    concern_index = _overall_concern_index(dimension_profile)
    base_level = _base_final_level(index)

    if risk.get("override"):
        final_level = "建议求助"
    else:
        final_level = _max_level(base_level, functional.get("minimum_final_level"), risk.get("minimum_final_level"))

    assessment = {
        "model": "six_dimension_f_r_v2_health_score",
        "score_direction": "six_dimensions.score 为 0-100 健康分，分数越高代表心理状态越稳定",
        "source_weights": source_weights or {"scale": 0.40, "dialogue": 0.45, "profile": 0.15},
        "six_dimensions": dimension_profile,
        "overall_index": index,
        "health_index": index,
        "concern_index": concern_index,
        "base_level": base_level,
        "functional_impairment": functional,
        "risk_protection_gate": risk,
        "final_level": final_level,
        "main_concerns": _main_concerns(dimension_profile),
        "recommendations": _recommendations(final_level, functional, risk),
        "disclaimer": "本结果用于心理状态筛查和辅助理解，不等同于临床诊断。",
    }
    assessment["interview_guidance"] = build_interview_guidance(assessment)
    return assessment


def format_assessment_markdown(assessment: Dict[str, Any]) -> str:
    """Render a compact Markdown report for Streamlit."""
    risk = assessment.get("risk_protection_gate") or {}
    functional = assessment.get("functional_impairment") or {}
    lines = [
        f"### 综合画像：{assessment.get('overall_index', 0)} / 100（{assessment.get('final_level', '待评估')}）",
        "",
        "六维分数为健康分，分数越高代表心理状态越稳定；风险保护闸门拥有一票优先权。",
        "",
        "#### 六维画像",
    ]
    for key, item in (assessment.get("six_dimensions") or {}).items():
        evidence = "；".join(item.get("evidence") or []) or "暂无明确文本证据"
        lines.append(
            f"- **{item.get('label', key)}**：{item.get('score', 0)}/100，"
            f"{item.get('level', '')}。{item.get('anchor_text', '')}。关注线索：{evidence}"
        )

    lines.extend([
        "",
        "#### 功能受损校准器",
        f"- **{functional.get('level', 'F0')} {functional.get('label', '')}**："
        f"{'；'.join(functional.get('evidence') or ['暂未发现明确功能受损证据'])}",
        "",
        "#### 风险保护闸门",
        f"- **{risk.get('level', 'R0')} {risk.get('label', '')}**：{risk.get('action', '')}",
    ])
    if risk.get("risk_factors"):
        lines.append(f"- 风险因素：{'；'.join(risk.get('risk_factors') or [])}")
    if risk.get("protective_factors"):
        lines.append(f"- 保护因素：{'；'.join(risk.get('protective_factors') or [])}")
    if risk.get("override"):
        lines.append("- 规则触发：风险闸门已覆盖普通六维加权结果。")

    lines.extend(["", "#### 建议路径"])
    for item in assessment.get("recommendations") or []:
        lines.append(f"- {item}")
    lines.extend(["", f"> {assessment.get('disclaimer', '')}"])
    return "\n".join(lines)
