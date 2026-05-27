import json
from datetime import datetime, time
from typing import Any, Dict, List, Optional, Tuple

from services.app_storage import DATA_ROOT, make_message, now_iso, read_json
from services.local_ai import generate_care_proactive_message, generate_proactive_message
from services.user_profile import load_user_profile, save_user_profile


PROACTIVE_DIR = DATA_ROOT / "proactive"
PROACTIVE_STATE_PATH = PROACTIVE_DIR / "state.json"

DEFAULT_SETTINGS = {
    "enabled": True,
    "channels": {
        "companion": True,
        "treehole": True,
        "psytest": True,
    },
    "frequency": "normal",
    "quiet_start": "23:30",
    "quiet_end": "08:00",
}

CHANNEL_COOLDOWN_HOURS = {
    "companion": 6,
    "treehole": 8,
    "psytest": 12,
}


def _merge_settings(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    settings = dict(DEFAULT_SETTINGS)
    if isinstance(raw, dict):
        settings.update({k: v for k, v in raw.items() if k != "channels"})
        channels = dict(DEFAULT_SETTINGS["channels"])
        if isinstance(raw.get("channels"), dict):
            channels.update(raw["channels"])
        settings["channels"] = channels
    return settings


def get_proactive_settings(profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    profile = profile if isinstance(profile, dict) else load_user_profile()
    return _merge_settings(profile.get("proactive") if isinstance(profile, dict) else None)


def set_proactive_enabled(enabled: bool) -> Dict[str, Any]:
    profile = load_user_profile()
    profile["proactive"] = get_proactive_settings(profile)
    profile["proactive"]["enabled"] = bool(enabled)
    return save_user_profile(profile)


def _read_state() -> Dict[str, Any]:
    data = read_json(PROACTIVE_STATE_PATH, {})
    return data if isinstance(data, dict) else {}


def _write_state(data: Dict[str, Any]) -> None:
    PROACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    PROACTIVE_STATE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _parse_datetime(raw: Any) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(raw))
    except Exception:
        return None


def _parse_clock(raw: str, fallback: time) -> time:
    try:
        hour, minute = str(raw).split(":", 1)
        return time(int(hour), int(minute))
    except Exception:
        return fallback


def _in_quiet_hours(settings: Dict[str, Any]) -> bool:
    now_clock = datetime.now().time()
    start = _parse_clock(str(settings.get("quiet_start") or ""), time(23, 30))
    end = _parse_clock(str(settings.get("quiet_end") or ""), time(8, 0))
    if start <= end:
        return start <= now_clock < end
    return now_clock >= start or now_clock < end


def _channel_enabled(channel: str, settings: Dict[str, Any]) -> bool:
    return bool(settings.get("enabled", True)) and bool((settings.get("channels") or {}).get(channel, True))


def _state_key(channel: str, target_id: str = "") -> str:
    return f"{channel}:{target_id or 'default'}"


def _last_message_time(messages: List[Dict[str, Any]]) -> Optional[datetime]:
    for msg in reversed(messages or []):
        if not isinstance(msg, dict):
            continue
        dt = _parse_datetime(msg.get("time") or msg.get("created_at") or msg.get("timestamp"))
        if dt:
            return dt
    return None


def _hours_since(dt: Optional[datetime]) -> Optional[float]:
    if not dt:
        return None
    return (datetime.now() - dt).total_seconds() / 3600


def _has_user_context(channel: str, messages: List[Dict[str, Any]]) -> bool:
    if channel == "companion":
        return True
    return any(msg.get("role") == "user" and str(msg.get("content", "")).strip() for msg in messages or [])


def should_send_proactive(
    channel: str,
    messages: List[Dict[str, Any]],
    target_id: str = "",
    force: bool = False,
) -> Tuple[bool, str]:
    profile = load_user_profile()
    settings = get_proactive_settings(profile)
    if force:
        return True, "force"
    if not _channel_enabled(channel, settings):
        return False, "disabled"
    if _in_quiet_hours(settings):
        return False, "quiet_hours"
    if not _has_user_context(channel, messages):
        return False, "no_user_context"

    cooldown = CHANNEL_COOLDOWN_HOURS.get(channel, 8)
    state = _read_state()
    key = _state_key(channel, target_id)
    last_state_time = _parse_datetime((state.get(key) or {}).get("last_sent_at"))
    last_message_time = _last_message_time(messages)
    newest = max([dt for dt in [last_state_time, last_message_time] if dt], default=None)
    elapsed = _hours_since(newest)
    if elapsed is not None and elapsed < cooldown:
        return False, "cooldown"
    return True, "due"


def _mark_sent(channel: str, target_id: str, content: str, reason: str) -> None:
    state = _read_state()
    state[_state_key(channel, target_id)] = {
        "last_sent_at": now_iso(),
        "last_content": content,
        "reason": reason,
    }
    _write_state(state)


def _make_proactive_message(channel: str, content: str, reason: str) -> Dict[str, Any]:
    msg = make_message("assistant", content)
    msg["proactive"] = True
    msg["proactive_channel"] = channel
    msg["proactive_reason"] = reason
    return msg


def maybe_add_care_proactive(
    channel: str,
    messages: List[Dict[str, Any]],
    scores: Optional[Dict[str, int]] = None,
    force: bool = False,
) -> Tuple[List[Dict[str, Any]], bool, str]:
    messages = list(messages or [])
    ok, reason = should_send_proactive(channel, messages, force=force)
    if not ok:
        return messages, False, reason
    profile = load_user_profile()
    content = generate_care_proactive_message(channel, messages, scores or {}, profile)
    messages.append(_make_proactive_message(channel, content, reason))
    _mark_sent(channel, "", content, reason)
    return messages, True, reason


def maybe_add_character_proactive(
    character: Dict[str, Any],
    messages: List[Dict[str, Any]],
    force: bool = False,
) -> Tuple[List[Dict[str, Any]], bool, str]:
    messages = list(messages or [])
    target_id = str(character.get("id") or "")
    ok, reason = should_send_proactive("companion", messages, target_id=target_id, force=force)
    if not ok:
        return messages, False, reason
    profile = load_user_profile()
    content = generate_proactive_message(character, profile)
    messages.append(_make_proactive_message("companion", content, reason))
    _mark_sent("companion", target_id, content, reason)
    return messages, True, reason
