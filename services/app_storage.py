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


def load_moods() -> Dict[str, str]:
    data = read_json(MOOD_PATH, {})
    return data if isinstance(data, dict) else {}


def save_mood(date_key: str, emoji: str) -> None:
    moods = load_moods()
    if emoji:
        moods[date_key] = emoji
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
