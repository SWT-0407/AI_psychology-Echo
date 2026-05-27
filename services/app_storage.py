import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
HISTORY_DIR = DATA_ROOT / "history"
TREEHOLE_DIR = DATA_ROOT / "treehole"
COMPANION_DIR = DATA_ROOT / "companion"
DIARY_DIR = DATA_ROOT / "diary_ui"

PROFILE_PATH = DIARY_DIR / "profile.json"
MOOD_PATH = DIARY_DIR / "moods.json"
TREEHOLE_PATH = TREEHOLE_DIR / "messages.json"
COMPANION_INDEX = COMPANION_DIR / "characters.json"
COMPANION_MEMORY_LIMIT = 30


def ensure_dirs() -> None:
    for path in [HISTORY_DIR, TREEHOLE_DIR, COMPANION_DIR, DIARY_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def make_id(prefix: str = "rec") -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{stamp}_{uuid.uuid4().hex[:6]}"


def current_user_id() -> str:
    return st.session_state.get("user_id") or st.session_state.get("user_email") or "local_user"


def read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def write_json(path: Path, data: Any) -> None:
    ensure_dirs()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def short_text(text: str, length: int = 36) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= length:
        return text
    return text[:length].rstrip() + "..."


def make_message(role: str, content: str) -> Dict[str, str]:
    return {"role": role, "content": str(content), "time": now_iso()}


def message_time(msg: Dict[str, Any]) -> str:
    raw = msg.get("time") or msg.get("created_at") or msg.get("timestamp") or ""
    try:
        return datetime.fromisoformat(str(raw)).strftime("%H:%M")
    except Exception:
        return str(raw)[11:16] if len(str(raw)) >= 16 else ""


def message_date(msg: Dict[str, Any]) -> str:
    raw = msg.get("time") or msg.get("created_at") or msg.get("timestamp") or ""
    try:
        return datetime.fromisoformat(str(raw)).strftime("%Y.%m.%d")
    except Exception:
        return datetime.now().strftime("%Y.%m.%d")


def summarize_messages(messages: List[Dict[str, Any]]) -> str:
    for msg in messages:
        if msg.get("role") == "user" and msg.get("content"):
            return short_text(str(msg["content"]), 44)
    for msg in messages:
        if msg.get("content"):
            return short_text(str(msg["content"]), 44)
    return "还没有写下内容"


def _last_assistant(messages: List[Dict[str, Any]]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            return str(msg.get("content", ""))
    return ""


def _generate_session_id() -> str:
    try:
        from services.storage_local import generate_session_id
        return generate_session_id()
    except Exception:
        return make_id("session")


def _score_meta(scores: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from services.local_ai import level_name, overall_score
        composite_score = overall_score(scores)
        level = level_name(scores)
    except Exception:
        composite_score = 0
        level = ""
    return {
        "composite_score": composite_score,
        "level_name": level,
        "label": level,
        "icon": "📝",
    }


def load_profile() -> Optional[Dict[str, Any]]:
    data = read_json(PROFILE_PATH, None)
    return data if isinstance(data, dict) else None


def save_profile(profile: Dict[str, Any]) -> None:
    data = dict(profile)
    data["user_id"] = current_user_id()
    data["user_email"] = st.session_state.get("user_email")
    data["updated_at"] = now_iso()
    data.setdefault("created_at", data["updated_at"])
    write_json(PROFILE_PATH, data)
    st.session_state.diary_profile = data
    try:
        from services.user_profile import update_profile_from_basic_info

        update_profile_from_basic_info(data)
    except Exception:
        pass


def load_moods() -> Dict[str, Any]:
    data = read_json(MOOD_PATH, {})
    return data if isinstance(data, dict) else {}


def save_mood(date_key: str, emoji: str, event: str = "") -> None:
    moods = load_moods()
    event = str(event or "").strip()[:30]
    if emoji or event:
        moods[date_key] = {"emoji": emoji, "event": event}
    else:
        moods.pop(date_key, None)
    write_json(MOOD_PATH, moods)
    st.session_state.diary_moods = moods


def _save_complete_session(session_id: str, payload: Dict[str, Any]) -> None:
    try:
        from services.storage_local import save_complete_session
        save_complete_session(session_id, payload)
    except Exception:
        write_json(HISTORY_DIR / f"{session_id}.json", payload)


def _maybe_upload_session(session_id: str, payload: Dict[str, Any]) -> None:
    if not st.session_state.get("cloud_consent", False):
        return
    try:
        from services.storage_cloud import upload_session_to_cloud
        upload_full = st.session_state.get("upload_full_content", True)
        upload_session_to_cloud(session_id, payload, upload_full)
    except Exception:
        pass


def build_session_payload(
    mode: str,
    messages: List[Dict[str, Any]],
    scores: Dict[str, Any],
    session_id: str,
    old: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
    mood: str = "",
) -> Dict[str, Any]:
    old = old or {}
    timestamp = old.get("timestamp") or old.get("created_at") or now_iso()
    summary = summarize_messages(messages)
    profile = st.session_state.get("diary_profile") or load_profile() or {}
    moods = st.session_state.get("diary_moods") or load_moods()
    meta = _score_meta(scores)
    try:
        from services.user_profile import get_profile_summary

        user_profile_summary = get_profile_summary()
    except Exception:
        user_profile_summary = {}

    payload = {
        "session_id": session_id,
        "id": session_id,
        "user_id": current_user_id(),
        "mode": mode,
        "title": title or old.get("title") or summary,
        "timestamp": timestamp,
        "created_at": timestamp,
        "updated_at": now_iso(),
        "display_messages": messages,
        "messages": messages,
        "scores": scores,
        "summary": summary,
        "mood": mood or old.get("mood", ""),
        "ai_suggestion": _last_assistant(messages),
        "ai_direction": old.get("ai_direction", ""),
        "diary_profile": profile,
        "diary_moods": moods,
        "user_profile_summary": user_profile_summary,
        "storage_version": "diary_v2_original_schema",
    }
    payload.update(meta)
    return payload


def save_history_record(
    mode: str,
    messages: List[Dict[str, Any]],
    scores: Dict[str, Any],
    record_id: Optional[str] = None,
    title: Optional[str] = None,
    mood: str = "",
) -> str:
    ensure_dirs()
    session_id = record_id or _generate_session_id()
    old = read_json(HISTORY_DIR / f"{session_id}.json", {})
    payload = build_session_payload(mode, messages, scores, session_id, old, title, mood)
    _save_complete_session(session_id, payload)
    _maybe_upload_session(session_id, payload)
    try:
        from services.user_profile import update_profile_from_session

        update_profile_from_session(mode, messages, scores, session_id, title or payload.get("title", ""))
    except Exception:
        pass
    return session_id


def load_history_record(record_id: str) -> Optional[Dict[str, Any]]:
    data = read_json(HISTORY_DIR / f"{record_id}.json", None)
    return data if isinstance(data, dict) else None


def update_history_messages(record_id: str, messages: List[Dict[str, Any]], scores: Dict[str, Any]) -> None:
    old = load_history_record(record_id)
    if not old:
        return
    payload = build_session_payload(
        old.get("mode", "psytest"),
        messages,
        scores,
        record_id,
        old,
        old.get("title"),
        old.get("mood", ""),
    )
    _save_complete_session(record_id, payload)
    _maybe_upload_session(record_id, payload)
    try:
        from services.user_profile import update_profile_from_session

        update_profile_from_session(
            payload.get("mode", "psytest"),
            messages,
            scores,
            record_id,
            payload.get("title", ""),
        )
    except Exception:
        pass


def list_history_records(mode: Optional[str] = None) -> List[Dict[str, Any]]:
    ensure_dirs()
    records: List[Dict[str, Any]] = []
    for path in HISTORY_DIR.glob("*.json"):
        data = read_json(path, None)
        if not isinstance(data, dict):
            continue
        if mode and data.get("mode") not in (mode, None, ""):
            continue
        messages = data.get("messages") or data.get("display_messages") or []
        data.setdefault("id", path.stem)
        data.setdefault("session_id", path.stem)
        data.setdefault("messages", messages)
        data.setdefault("summary", summarize_messages(messages))
        data.setdefault("updated_at", data.get("updated_at") or data.get("timestamp") or data.get("created_at", ""))
        records.append(data)
    records.sort(key=lambda item: item.get("updated_at") or item.get("timestamp") or item.get("created_at") or "", reverse=True)
    return records


def load_treehole_messages() -> List[Dict[str, Any]]:
    data = read_json(TREEHOLE_PATH, [])
    return data if isinstance(data, list) else []


def save_treehole_messages(messages: List[Dict[str, Any]]) -> None:
    write_json(TREEHOLE_PATH, messages)


def _safe_name(name: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", str(name or "")).strip("_")
    return cleaned or uuid.uuid4().hex[:8]


def load_characters() -> List[Dict[str, Any]]:
    data = read_json(COMPANION_INDEX, [])
    return data if isinstance(data, list) else []


def save_characters(characters: List[Dict[str, Any]]) -> None:
    write_json(COMPANION_INDEX, characters)


def relationship_stage(intimacy: int) -> str:
    if intimacy >= 80:
        return "重要的人"
    if intimacy >= 40:
        return "信任"
    if intimacy >= 18:
        return "亲近"
    if intimacy >= 6:
        return "熟悉"
    return "初识"


def _has_any(text: str, words: List[str]) -> bool:
    return any(word in text for word in words)


def _persona_sections(char: Dict[str, Any]) -> Dict[str, Any]:
    profile = char.get("persona_profile") or {}
    return profile if isinstance(profile, dict) else {}


def _profile_value(profile: Dict[str, Any], section: str, key: str) -> str:
    value = (profile.get(section) or {}).get(key) if isinstance(profile.get(section), dict) else ""
    return str(value or "").strip()


def _compact_parts(parts: List[str], limit: int = 6) -> str:
    clean = [part.strip("；; \n") for part in parts if str(part or "").strip()]
    return "；".join(clean[:limit])


def build_answer_model(char: Dict[str, Any]) -> Dict[str, Any]:
    """Turn the filled relationship profile into a compact model for replies."""
    profile = char.get("relationship_profile") or {}
    persona = _persona_sections(char)
    joined = " ".join(str(value or "") for value in profile.values())
    contact = str(profile.get("contact_frequency") or "")
    content = str(profile.get("interaction_content") or "")
    offline = str(profile.get("offline_interaction") or "")
    special = str(profile.get("specialness") or "")
    boundaries = str(profile.get("boundaries") or "")
    pattern = str(profile.get("emotional_pattern") or "")
    duration = str(profile.get("acquaintance_duration") or "")

    intensity_score = 0
    if _has_any(contact, ["每天", "经常", "频繁", "秒回", "主动", "深夜"]):
        intensity_score += 2
    if _has_any(content, ["情绪", "生活", "秘密", "未来", "暧昧", "心事"]):
        intensity_score += 2
    if _has_any(offline, ["单独", "经常", "陪", "送", "照顾", "见面"]):
        intensity_score += 2
    if _has_any(special, ["特殊", "优先", "区别", "只对", "重要", "偏爱"]):
        intensity_score += 2
    if _has_any(boundaries, ["隐藏", "暧昧", "吃醋", "不避嫌", "越界"]):
        intensity_score += 1

    if intensity_score >= 7:
        intensity = "高"
    elif intensity_score >= 4:
        intensity = "中"
    else:
        intensity = "低"

    closeness_velocity = "突然升温" if _has_any(duration + joined, ["突然", "最近", "一下", "忽然", "变亲近"]) else "自然推进"
    initiative_pattern = "对方更主动" if _has_any(contact, ["他主动", "她主动", "对方主动", "对方更主动", "ta主动", "TA主动", "TA更主动"]) else "用户更主动" if _has_any(contact, ["我主动", "我更主动", "我找", "我发"]) else "主动性不明"
    boundary_signal = "边界风险偏高" if _has_any(boundaries, ["隐藏", "暧昧", "吃醋", "不避嫌", "越界", "背着"]) else "边界感较清楚" if _has_any(boundaries, ["避嫌", "清楚", "坦荡", "公开"]) else "边界信息不足"
    offline_weight = "现实交集强" if _has_any(offline, ["单独", "经常", "陪", "送", "照顾", "见面"]) else "主要在线/低现实交集"

    if _has_any(pattern, ["依赖", "粘", "缺安全感"]):
        attachment_guess = "偏依赖型"
    elif _has_any(pattern, ["外向", "会撩", "暧昧", "边界弱"]):
        attachment_guess = "外向暧昧倾向"
    elif _has_any(pattern, ["冷淡", "回避", "忽冷忽热"]):
        attachment_guess = "偏回避/不稳定"
    else:
        attachment_guess = "信息不足，暂不定型"

    occupation = str(char.get("occupation") or _profile_value(persona, "surface", "occupation"))
    city = str(char.get("city") or _profile_value(persona, "surface", "city"))
    daily_rhythm = _profile_value(persona, "surface", "daily_rhythm")
    core_need = _profile_value(persona, "core", "need")
    core_fear = _profile_value(persona, "core", "fear")
    defense = _profile_value(persona, "core", "defense")
    affection = _profile_value(persona, "core", "affection")
    family = _profile_value(persona, "life", "family")
    key_events = _profile_value(persona, "life", "key_events")
    unfinished = _profile_value(persona, "life", "unfinished")
    desire = _profile_value(persona, "desire", "personal_desire")
    day_night = _profile_value(persona, "time", "day_night")
    recent_state = _profile_value(persona, "time", "recent_state")
    residue = _profile_value(persona, "time", "emotional_residue")

    if _has_any(daily_rhythm + day_night + occupation, ["夜", "熬夜", "加班", "失眠", "倒时差"]):
        reply_cadence = "回复节奏不稳定，深夜更容易感性"
    elif _has_any(daily_rhythm + occupation, ["上课", "排班", "实习", "工作", "会议"]):
        reply_cadence = "白天会被现实事务打断，回复不总是秒回"
    else:
        reply_cadence = "回复节奏自然，亲近后主动性提升"

    persona_consistency = _compact_parts([
        f"{occupation}" if occupation else "",
        f"在{city}" if city else "",
        daily_rhythm,
        f"需要{core_need}" if core_need else "",
        f"怕{core_fear}" if core_fear else "",
        f"防御方式是{defense}" if defense else "",
        f"表达亲近时{affection}" if affection else "",
    ])
    inner_trace = _compact_parts([family, key_events, unfinished], limit=3)
    time_sensitivity = _compact_parts([day_night, recent_state, residue], limit=3)
    desire_signal = _compact_parts([desire], limit=1)

    if boundary_signal == "边界风险偏高":
        reply_strategy = "先帮用户辨认事实和边界，不急着下恋爱结论。"
    elif intensity == "高":
        reply_strategy = "承认这段关系对用户的重要性，同时追问对方是否也有稳定投入。"
    elif closeness_velocity == "突然升温":
        reply_strategy = "重点观察突然变亲近的触发点、持续性和对方动机。"
    else:
        reply_strategy = "用温和追问补齐联系频率、主动性和现实互动证据。"

    return {
        "relationship_intensity": intensity,
        "intensity_score": intensity_score,
        "closeness_velocity": closeness_velocity,
        "initiative_pattern": initiative_pattern,
        "boundary_signal": boundary_signal,
        "offline_weight": offline_weight,
        "attachment_guess": attachment_guess,
        "persona_consistency": persona_consistency,
        "inner_trace": inner_trace,
        "reply_cadence": reply_cadence,
        "time_sensitivity": time_sensitivity,
        "desire_signal": desire_signal,
        "defense_mechanism": defense,
        "affection_style": affection,
        "core_need": core_need,
        "core_fear": core_fear,
        "reply_strategy": reply_strategy,
        "follow_up_focus": [
            "对方是否持续主动",
            "互动是否只发生在特定场景",
            "边界是否公开且稳定",
            "用户在这段关系里最被牵动的感受",
        ],
        "updated_at": now_iso(),
    }


def _detect_emotion_state(user_text: str, emotion: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if emotion:
        vector = emotion.get("vector") or {}
        return {
            "label": emotion.get("emotion_cn") or emotion.get("emotion") or "平静",
            "source": "multimodal",
            "valence": vector.get("valence", emotion.get("valence", 0.5)),
            "arousal": vector.get("arousal", emotion.get("arousal", 0.5)),
            "updated_at": now_iso(),
        }

    text = str(user_text or "")
    rules = [
        ("低落", ["难过", "委屈", "崩溃", "想哭", "失落", "孤独", "撑不住"]),
        ("焦虑", ["焦虑", "紧张", "压力", "害怕", "慌", "担心", "烦"]),
        ("疲惫", ["累", "困", "失眠", "没力气", "疲惫", "睡不着"]),
        ("生气", ["生气", "火大", "烦死", "讨厌", "气死"]),
        ("开心", ["开心", "高兴", "顺利", "喜欢", "期待", "舒服"]),
    ]
    for label, words in rules:
        if any(word in text for word in words):
            return {"label": label, "source": "text", "updated_at": now_iso()}
    return {"label": "平静", "source": "text", "updated_at": now_iso()}


def _memory_summary(user_text: str) -> Optional[str]:
    text = re.sub(r"\s+", " ", str(user_text or "")).strip()
    if len(text) < 6:
        return None
    memory_markers = [
        "我叫", "我是", "我在", "我喜欢", "我讨厌", "我不喜欢", "我害怕", "我希望",
        "我想", "我要", "记住", "以后", "最近", "今天", "室友", "朋友", "家里", "课程",
    ]
    if not any(marker in text for marker in memory_markers):
        return None
    return short_text(text, 72)


def _detect_emotional_residue(user_text: str, assistant_text: str = "") -> Optional[Dict[str, Any]]:
    text = str(user_text or "") + " " + str(assistant_text or "")
    if _has_any(text, ["吵架", "冷战", "别理我", "不想聊", "失望", "生气", "吃醋", "拉黑"]):
        return {
            "label": "关系拉扯",
            "summary": short_text(str(user_text or ""), 56),
            "strength": 2,
            "updated_at": now_iso(),
        }
    if _has_any(text, ["对不起", "抱歉", "谢谢你", "好多了", "没事了", "和好了"]):
        return {
            "label": "缓和中",
            "summary": short_text(str(user_text or ""), 56),
            "strength": 1,
            "updated_at": now_iso(),
        }
    return None


def update_companion_state(
    char: Dict[str, Any],
    user_text: str,
    assistant_text: str = "",
    emotion: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    char.setdefault("memory", [])
    char.setdefault("relationship", {})
    char.setdefault("emotion_state", {})
    char.setdefault("reply_habits", {"short_text": True, "avoid_ai_tone": True})
    char.setdefault("persona_profile", {})

    intimacy_gain = 1
    if len(str(user_text or "")) >= 40:
        intimacy_gain += 1
    if any(word in str(user_text or "") for word in ["谢谢", "想你", "陪我", "记住", "喜欢"]):
        intimacy_gain += 1
    char["intimacy"] = max(0, int(char.get("intimacy") or 0) + intimacy_gain)

    stage = relationship_stage(int(char.get("intimacy") or 0))
    char["relationship"] = {
        **(char.get("relationship") or {}),
        "stage": stage,
        "intimacy": int(char.get("intimacy") or 0),
        "updated_at": now_iso(),
    }
    char["relationship_stage"] = stage
    char["emotion_state"] = _detect_emotion_state(user_text, emotion)
    if char.get("relationship_profile"):
        char["answer_model"] = build_answer_model(char)

    residue = _detect_emotional_residue(user_text, assistant_text)
    if residue:
        char["emotional_residue"] = residue

    summary = _memory_summary(user_text)
    if summary:
        memories = [m for m in char.get("memory", []) if isinstance(m, dict)]
        if not any(m.get("summary") == summary for m in memories):
            memories.append({
                "summary": summary,
                "created_at": now_iso(),
                "last_seen_at": now_iso(),
                "importance": 2 if any(x in summary for x in ["记住", "我叫", "我喜欢", "我害怕"]) else 1,
            })
        char["memory"] = memories[-COMPANION_MEMORY_LIMIT:]

    if assistant_text:
        char["last_reply"] = short_text(assistant_text, 80)
    update_character(char)
    try:
        from services.user_profile import update_profile_from_companion

        update_profile_from_companion(char, user_text, assistant_text, emotion)
    except Exception:
        pass
    return char


def create_character(
    name: str,
    emoji: str,
    personality: str,
    identity: str = "朋友",
    age: str = "",
    speaking_style: str = "",
) -> Dict[str, Any]:
    characters = load_characters()
    char = {
        "id": f"char_{_safe_name(name)}_{uuid.uuid4().hex[:5]}",
        "name": name.strip() or "新朋友",
        "emoji": emoji.strip() or "😊",
        "identity": identity.strip() or "朋友",
        "age": age.strip(),
        "personality": personality.strip() or "温柔、耐心、愿意认真陪伴聊天。",
        "speaking_style": speaking_style.strip() or "自然、像微信聊天一样简短亲近。",
        "pinned": False,
        "unread": 1,
        "intimacy": 0,
        "relationship_stage": "初识",
        "relationship": {"stage": "初识", "intimacy": 0, "updated_at": now_iso()},
        "emotion_state": {"label": "平静", "source": "init", "updated_at": now_iso()},
        "persona_profile": {},
        "emotional_residue": {},
        "memory": [],
        "reply_habits": {"short_text": True, "avoid_ai_tone": True},
        "last_active": now_iso(),
        "last_read_at": "",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "user_id": current_user_id(),
    }
    characters.append(char)
    save_characters(characters)
    save_companion_messages(
        char["id"],
        [make_message("assistant", f"嗨，我是{char['name']}。我刚加上你。")],
    )
    return char


def update_character(char: Dict[str, Any]) -> None:
    characters = load_characters()
    for idx, item in enumerate(characters):
        if item.get("id") == char.get("id"):
            char["updated_at"] = now_iso()
            characters[idx] = char
            save_characters(characters)
            return


def companion_chat_path(character_id: str) -> Path:
    return COMPANION_DIR / f"{_safe_name(character_id)}.json"


def load_companion_messages(character_id: str) -> List[Dict[str, Any]]:
    data = read_json(companion_chat_path(character_id), [])
    return data if isinstance(data, list) else []


def save_companion_messages(character_id: str, messages: List[Dict[str, Any]]) -> None:
    write_json(companion_chat_path(character_id), messages)


def init_runtime_state() -> None:
    ensure_dirs()
    st.session_state.setdefault("is_logged_in", False)
    st.session_state.setdefault("skipped_login", False)
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("user_email", None)
    st.session_state.setdefault("user_nickname", "")
    st.session_state.setdefault("cloud_consent", False)
    st.session_state.setdefault("upload_full_content", True)
    st.session_state.setdefault("page", "home")
    st.session_state.setdefault("diary_stage", "cover")
    st.session_state.setdefault("diary_profile", load_profile())
    st.session_state.setdefault("diary_moods", load_moods())
    st.session_state.setdefault("diary_history_page", 0)
    st.session_state.setdefault("selected_history_id", None)
    st.session_state.setdefault("psy_messages", [
        make_message("assistant", "你好，我是 Echo。你可以像写日记一样告诉我今天发生了什么，我会慢慢陪你梳理。")
    ])
    st.session_state.setdefault("psy_scores", {})
    st.session_state.setdefault("psy_record_id", None)
    st.session_state.setdefault("treehole_messages", load_treehole_messages() or [
        make_message("assistant", "这里是你的 AI 树洞。今天有什么想悄悄说给我听的吗？")
    ])
    st.session_state.setdefault("selected_character_id", None)
    try:
        from services.user_profile import load_user_profile

        st.session_state.setdefault("user_profile", load_user_profile())
    except Exception:
        st.session_state.setdefault("user_profile", {})
