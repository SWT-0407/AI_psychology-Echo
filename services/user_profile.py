import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import streamlit as st


DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
USER_PROFILE_DIR = DATA_ROOT / "user_profile"
USER_PROFILE_PATH = USER_PROFILE_DIR / "profile.json"
EVENT_LIMIT = 80
HISTORY_LIMIT = 40

DIMENSION_WEIGHTS = {
    "x1": 0.15,
    "x2": 0.15,
    "x3": 0.10,
    "x4": 0.15,
    "x5": 0.20,
    "x6": 0.25,
}

DIMENSION_TAGS = {
    "x1": "情绪需要照顾",
    "x2": "焦虑压力偏高",
    "x3": "身心疲惫",
    "x4": "行动动力不足",
    "x5": "社交支持不足",
    "x6": "意义感波动",
}

TOPIC_RULES = {
    "学业压力": ["学习", "考试", "作业", "论文", "课程", "绩点", "考研", "ddl", "DDL"],
    "工作压力": ["工作", "实习", "加班", "同事", "领导", "面试", "绩效"],
    "人际关系": ["朋友", "室友", "同学", "关系", "吵架", "误会", "社交"],
    "亲密关系": ["喜欢", "恋爱", "男朋友", "女朋友", "暧昧", "分手", "前任"],
    "家庭": ["家里", "父母", "妈妈", "爸爸", "亲人", "家庭"],
    "睡眠": ["失眠", "睡不着", "熬夜", "困", "睡眠", "做梦"],
    "自我价值": ["没用", "失败", "自责", "内耗", "迷茫", "意义", "价值"],
}

EMOTION_RULES = {
    "焦虑": ["焦虑", "紧张", "担心", "害怕", "慌", "压力"],
    "低落": ["难过", "委屈", "崩溃", "想哭", "失落", "孤独", "撑不住"],
    "疲惫": ["累", "困", "失眠", "没力气", "疲惫", "睡不着"],
    "生气": ["生气", "火大", "烦死", "讨厌", "气死"],
    "平稳": ["开心", "高兴", "顺利", "喜欢", "期待", "舒服", "平静"],
}

HIGH_RISK_WORDS = [
    "自杀",
    "自残",
    "不想活",
    "死了算了",
    "结束生命",
    "伤害自己",
    "活不下去",
]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _current_user_id() -> str:
    return st.session_state.get("user_id") or st.session_state.get("user_email") or "local_user"


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def _write_json(path: Path, data: Any) -> None:
    USER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _short_text(text: str, length: int = 56) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= length:
        return text
    return text[:length].rstrip() + "..."


def _default_profile() -> Dict[str, Any]:
    now = _now_iso()
    return {
        "profile_version": "user_profile_v1",
        "user_id": _current_user_id(),
        "created_at": now,
        "updated_at": now,
        "basic": {},
        "assessment": {
            "initial_scores": {},
            "latest_scores": {},
            "overall_score": None,
            "level": "暂无评估",
            "history": [],
        },
        "emotion": {
            "latest_label": "暂无",
            "recent_keywords": [],
            "recent_topics": [],
            "negative_signal_count": 0,
        },
        "behavior": {
            "source_counts": {"psytest": 0, "treehole": 0, "companion": 0, "basic": 0},
            "last_active_mode": "",
            "total_events": 0,
        },
        "companion": {
            "last_character": "",
            "last_character_id": "",
            "preferred_identities": [],
            "relationship_stage": "",
            "intimacy": 0,
        },
        "tags": [],
        "risk": {"level": "low", "reasons": [], "updated_at": now},
        "events": [],
    }


def load_user_profile() -> Dict[str, Any]:
    data = _read_json(USER_PROFILE_PATH, {})
    if not isinstance(data, dict):
        data = {}
    profile = _default_profile()
    profile.update(data)
    for key, value in _default_profile().items():
        if isinstance(value, dict):
            merged = dict(value)
            merged.update(profile.get(key) if isinstance(profile.get(key), dict) else {})
            profile[key] = merged
    profile["user_id"] = _current_user_id()
    return profile


def save_user_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    profile["user_id"] = _current_user_id()
    profile["updated_at"] = _now_iso()
    profile.setdefault("created_at", profile["updated_at"])
    _write_json(USER_PROFILE_PATH, profile)
    st.session_state.user_profile = profile
    return profile


def _overall_score(scores: Dict[str, Any]) -> Optional[float]:
    if not scores:
        return None
    total = 0.0
    for key, weight in DIMENSION_WEIGHTS.items():
        try:
            total += float(scores.get(key, 5)) * weight
        except (TypeError, ValueError):
            total += 5 * weight
    return round(total * 10, 1)


def _level_name(score: Optional[float]) -> str:
    if score is None:
        return "暂无评估"
    if score >= 85:
        return "能量充足"
    if score >= 70:
        return "状态稳定"
    if score >= 55:
        return "轻微波动"
    if score >= 40:
        return "需要照顾"
    return "建议求助引导"


def _message_text(messages: List[Dict[str, Any]], limit: int = 12) -> str:
    user_parts = [
        str(msg.get("content", ""))
        for msg in messages[-limit:]
        if msg.get("role") == "user" and msg.get("content")
    ]
    return " ".join(user_parts)


def _find_matches(text: str, rules: Dict[str, List[str]]) -> List[str]:
    matches = []
    for label, words in rules.items():
        if any(word in text for word in words):
            matches.append(label)
    return matches


def _unique_recent(existing: Iterable[str], new_items: Iterable[str], limit: int = 10) -> List[str]:
    items = [str(item) for item in existing if item]
    for item in new_items:
        item = str(item or "").strip()
        if not item:
            continue
        if item in items:
            items.remove(item)
        items.append(item)
    return items[-limit:]


def _tags_from_scores(scores: Dict[str, Any], score: Optional[float]) -> List[str]:
    tags: List[str] = []
    for key, label in DIMENSION_TAGS.items():
        try:
            if int(scores.get(key, 10)) <= 4:
                tags.append(label)
        except (TypeError, ValueError):
            continue
    if score is not None:
        if score <= 40:
            tags.append("高强度支持")
        elif score <= 55:
            tags.append("温柔陪伴")
        elif score >= 75:
            tags.append("状态较稳定")
    return tags


def _detect_risk(text: str, score: Optional[float]) -> Dict[str, Any]:
    reasons = [word for word in HIGH_RISK_WORDS if word in text]
    if reasons:
        level = "high"
    elif score is not None and score <= 40:
        level = "medium"
        reasons = ["综合评分偏低"]
    else:
        level = "low"
    return {"level": level, "reasons": reasons, "updated_at": _now_iso()}


def _add_event(
    profile: Dict[str, Any],
    mode: str,
    event_type: str,
    summary: str = "",
    scores: Optional[Dict[str, Any]] = None,
    source_id: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    events = [event for event in profile.get("events", []) if isinstance(event, dict)]
    score = _overall_score(scores or {})
    events.append(
        {
            "time": _now_iso(),
            "mode": mode,
            "event_type": event_type,
            "source_id": source_id,
            "summary": _short_text(summary, 80),
            "overall_score": score,
            "extra": extra or {},
        }
    )
    profile["events"] = events[-EVENT_LIMIT:]
    behavior = profile.setdefault("behavior", {})
    counts = behavior.setdefault("source_counts", {})
    counts[mode] = int(counts.get(mode, 0) or 0) + 1
    behavior["last_active_mode"] = mode
    behavior["total_events"] = int(behavior.get("total_events", 0) or 0) + 1


def update_profile_from_basic_info(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    profile = load_user_profile()
    basic = {
        key: value
        for key, value in dict(profile_data or {}).items()
        if key not in {"created_at", "updated_at", "user_id", "user_email"}
    }
    profile["basic"] = {**(profile.get("basic") or {}), **basic}
    _add_event(profile, "basic", "basic_profile_saved", "用户完善了基础信息")
    return save_user_profile(profile)


def update_profile_from_session(
    mode: str,
    messages: List[Dict[str, Any]],
    scores: Dict[str, Any],
    source_id: str = "",
    title: str = "",
) -> Dict[str, Any]:
    profile = load_user_profile()
    text = _message_text(messages)
    score = _overall_score(scores)
    level = _level_name(score)
    topics = _find_matches(text, TOPIC_RULES)
    emotions = _find_matches(text, EMOTION_RULES)
    tags = _tags_from_scores(scores, score) + topics + emotions

    assessment = profile.setdefault("assessment", {})
    if mode == "psytest" and not assessment.get("initial_scores"):
        assessment["initial_scores"] = dict(scores or {})
    assessment["latest_scores"] = dict(scores or {})
    assessment["overall_score"] = score
    assessment["level"] = level

    history = [item for item in assessment.get("history", []) if isinstance(item, dict)]
    snapshot = {
        "time": _now_iso(),
        "mode": mode,
        "source_id": source_id,
        "overall_score": score,
        "level": level,
        "scores": dict(scores or {}),
    }
    if history and source_id and history[-1].get("source_id") == source_id:
        history[-1] = snapshot
    else:
        history.append(snapshot)
    assessment["history"] = history[-HISTORY_LIMIT:]

    emotion = profile.setdefault("emotion", {})
    if emotions:
        emotion["latest_label"] = emotions[-1]
    emotion["recent_keywords"] = _unique_recent(emotion.get("recent_keywords", []), emotions)
    emotion["recent_topics"] = _unique_recent(emotion.get("recent_topics", []), topics)
    if any(item in {"焦虑", "低落", "疲惫", "生气"} for item in emotions):
        emotion["negative_signal_count"] = int(emotion.get("negative_signal_count", 0) or 0) + 1

    profile["tags"] = _unique_recent(profile.get("tags", []), tags, limit=14)
    risk = _detect_risk(text, score)
    if risk["level"] != "low" or profile.get("risk", {}).get("level") != "high":
        profile["risk"] = risk

    _add_event(
        profile,
        mode,
        "session_updated",
        summary=title or text,
        scores=scores,
        source_id=source_id,
        extra={"topics": topics, "emotions": emotions, "level": level},
    )
    return save_user_profile(profile)


def update_profile_from_companion(
    character: Dict[str, Any],
    user_text: str = "",
    assistant_text: str = "",
    emotion: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    profile = load_user_profile()
    companion = profile.setdefault("companion", {})
    identity = str(character.get("identity") or "")
    companion["last_character"] = str(character.get("name") or "")
    companion["last_character_id"] = str(character.get("id") or "")
    companion["relationship_stage"] = str(character.get("relationship_stage") or "")
    companion["intimacy"] = int(character.get("intimacy") or 0)
    companion["preferred_identities"] = _unique_recent(
        companion.get("preferred_identities", []),
        [identity] if identity else [],
        limit=6,
    )

    text = str(user_text or "")
    emotions = _find_matches(text, EMOTION_RULES)
    if emotion:
        label = emotion.get("emotion_cn") or emotion.get("emotion")
        if label:
            emotions.append(str(label))
    emotion_state = profile.setdefault("emotion", {})
    if emotions:
        emotion_state["latest_label"] = emotions[-1]
        emotion_state["recent_keywords"] = _unique_recent(emotion_state.get("recent_keywords", []), emotions)

    profile["tags"] = _unique_recent(profile.get("tags", []), ["偏好虚拟陪伴", identity] + emotions, limit=14)
    _add_event(
        profile,
        "companion",
        "companion_interaction",
        summary=user_text or assistant_text,
        source_id=str(character.get("id") or ""),
        extra={"character": companion["last_character"], "identity": identity},
    )
    return save_user_profile(profile)


def get_profile_summary() -> Dict[str, Any]:
    profile = load_user_profile()
    assessment = profile.get("assessment") or {}
    emotion = profile.get("emotion") or {}
    behavior = profile.get("behavior") or {}
    companion = profile.get("companion") or {}
    risk = profile.get("risk") or {}
    return {
        "level": assessment.get("level") or "暂无评估",
        "overall_score": assessment.get("overall_score"),
        "latest_emotion": emotion.get("latest_label") or "暂无",
        "recent_topics": list(emotion.get("recent_topics") or [])[-4:],
        "tags": list(profile.get("tags") or [])[-6:],
        "total_events": behavior.get("total_events", 0),
        "last_active_mode": behavior.get("last_active_mode", ""),
        "last_character": companion.get("last_character", ""),
        "risk_level": risk.get("level", "low"),
    }


def build_profile_context(max_chars: int = 240) -> str:
    summary = get_profile_summary()
    parts = [
        f"综合状态：{summary['level']}",
        f"最近情绪：{summary['latest_emotion']}",
        f"关注主题：{'、'.join(summary['recent_topics']) or '暂无'}",
        f"画像标签：{'、'.join(summary['tags']) or '暂无'}",
    ]
    if summary.get("last_character"):
        parts.append(f"最近陪伴角色：{summary['last_character']}")
    return _short_text("；".join(parts), max_chars)
