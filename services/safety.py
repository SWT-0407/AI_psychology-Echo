"""
Safety guardrails for high-risk mental-health conversations.

The app is not a medical or crisis service. This module only catches obvious
high-risk language and routes the assistant response toward immediate support.
"""
import os
import re
from dataclasses import dataclass
from typing import Iterable, List


DEFAULT_CRISIS_RESOURCE_TEXT = (
    "如果你正处在现实危险中，请立刻联系当地紧急救援电话，或让家人、朋友等可信任的人陪你；"
    "如果你在美国，也可以拨打或短信联系 988 Suicide & Crisis Lifeline。"
    "你也可以主动联系学校心理中心、辅导员、校医院或持证心理/精神卫生专业人士。"
)

SELF_HARM_PATTERNS = [
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

HARM_OTHERS_PATTERNS = [
    "伤害别人",
    "伤害他人",
    "伤人",
    "杀人",
    "杀了他",
    "杀了她",
    "杀了他们",
    "弄死",
    "报复社会",
    "同归于尽",
    "带走别人",
    "砍人",
    "捅人",
]

IMMINENT_PATTERNS = [
    "马上",
    "现在就",
    "已经",
    "准备",
    "计划",
    "方法",
    "工具",
    "刀",
    "药",
    "楼顶",
    "窗边",
    "绳",
    "武器",
    "煤气",
    "农药",
]

DISTRESS_PATTERNS = [
    "撑不住",
    "崩溃",
    "绝望",
    "没人懂",
    "没意义",
    "好累",
    "痛苦",
    "喘不过气",
    "控制不住",
    "想消失",
]

NEGATION_PATTERNS = [
    "不是想死",
    "不想自杀",
    "不会自杀",
    "没有自杀",
    "不打算自杀",
    "没有轻生",
    "不会伤害别人",
    "不会伤害他人",
    "不想伤害别人",
    "不想伤害他人",
]


@dataclass(frozen=True)
class SafetyAssessment:
    level: str
    matched_terms: List[str]

    @property
    def is_crisis(self) -> bool:
        return self.level == "crisis"

    @property
    def needs_support(self) -> bool:
        return self.level in {"crisis", "distress"}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "").lower())


def _matches(text: str, patterns: Iterable[str]) -> List[str]:
    normalized = _normalize(text)
    return [pattern for pattern in patterns if pattern.lower() in normalized]


def assess_message_safety(text: str) -> SafetyAssessment:
    """Return a conservative safety assessment for one user message."""
    normalized = _normalize(text)
    if not normalized:
        return SafetyAssessment("none", [])

    self_harm = _matches(normalized, SELF_HARM_PATTERNS)
    harm_others = _matches(normalized, HARM_OTHERS_PATTERNS)
    negations = _matches(normalized, NEGATION_PATTERNS)
    imminent = _matches(normalized, IMMINENT_PATTERNS)

    if (self_harm or harm_others) and not negations:
        terms = list(dict.fromkeys(self_harm + harm_others + imminent))
        return SafetyAssessment("crisis", terms)

    distress = _matches(normalized, DISTRESS_PATTERNS)
    if distress:
        return SafetyAssessment("distress", distress)

    return SafetyAssessment("none", [])


def crisis_resource_text() -> str:
    return os.getenv("ECHO_CRISIS_RESOURCE_TEXT", DEFAULT_CRISIS_RESOURCE_TEXT).strip()


def make_safety_reply(assessment: SafetyAssessment, assistant_name: str = "Echo") -> str:
    """Build a response that prioritizes safety over normal companionship."""
    resources = crisis_resource_text()
    if assessment.is_crisis:
        return (
            f"我很认真地看到了这句话。{assistant_name}可以陪你说话，"
            "但我不能替代现实中的紧急帮助或专业判断；系统也不会在后台替你联系任何机构或个人。\n\n"
            f"{resources}\n\n"
            "如果你愿意，我建议你先考虑三件很小但重要的事：暂时离开可能伤害自己的物品或地点；"
            "把这段话发给一个此刻能联系到的家人、朋友或其他可信任的人；尽量不要一个人待着。"
            "如果你担心自己会伤害别人，也请先拉开距离、放下可能造成伤害的物品，并联系现实中的专业支持。\n\n"
            "如果你愿意，只回我一个数字也可以：1=我现在有危险，2=我有念头但还安全，3=我只是太痛苦了。"
        )

    return (
        "听起来你现在已经被压得很满了。先不用把所有事解释清楚，"
        "我们先把这一刻稳住：慢慢吸气四秒、停一秒、呼气六秒，做三轮。\n\n"
        "如果这种痛苦正在变得失控，或者你开始担心自己会伤害自己，"
        f"建议你马上联系现实中的人陪你。{resources}\n\n"
        "你也可以先告诉我：现在最强烈的是难过、焦虑、麻木，还是害怕？"
    )


def attach_safety_metadata(message: dict, assessment: SafetyAssessment) -> dict:
    message["safety_level"] = assessment.level
    return message
