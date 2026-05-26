"""
AI 树洞日记本 UI 的轻量本地存储
负责：用户档案 / 每日心情 emoji / 历史记录读取 / 历史记录分页
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

BASE_DIR = Path("data")
DIARY_DIR = BASE_DIR / "diary_ui"
PROFILE_PATH = DIARY_DIR / "profile.json"
MOOD_PATH = DIARY_DIR / "moods.json"
HISTORY_DIR = BASE_DIR / "history"


def _ensure_dirs():
    DIARY_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return default
    return default


def _write_json(path: Path, data):
    _ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_profile() -> Optional[Dict[str, Any]]:
    return _read_json(PROFILE_PATH, None)


def save_profile(profile: Dict[str, Any]) -> None:
    profile["created_at"] = profile.get("created_at") or datetime.now().isoformat(timespec="seconds")
    _write_json(PROFILE_PATH, profile)
    st.session_state.diary_profile = profile


def load_moods() -> Dict[str, str]:
    return _read_json(MOOD_PATH, {})


def save_mood(date_key: str, emoji: str) -> None:
    moods = load_moods()
    if emoji and emoji != "不填写":
        moods[date_key] = emoji
    elif date_key in moods:
        moods.pop(date_key)
    _write_json(MOOD_PATH, moods)
    st.session_state.diary_moods = moods


def normalize_message_time(msg: Dict[str, Any]) -> str:
    raw = msg.get("time") or msg.get("created_at") or msg.get("timestamp")
    if raw:
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).strftime("%H:%M")
        except Exception:
            return str(raw)[11:16] if len(str(raw)) >= 16 else ""
    return ""


def _extract_messages(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ["display_messages", "messages", "chat_history", "conversation"]:
        val = data.get(key)
        if isinstance(val, list):
            return val
    return []


def _extract_created_at(data: Any, fallback_ts: float) -> datetime:
    if isinstance(data, dict):
        for key in ["created_at", "saved_at", "timestamp", "time", "date"]:
            raw = data.get(key)
            if raw:
                try:
                    return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    pass
    return datetime.fromtimestamp(fallback_ts)


def _extract_scores(data: Any) -> Dict[str, Any]:
    if isinstance(data, dict):
        for key in ["scores", "final_scores", "dimension_scores"]:
            if isinstance(data.get(key), dict):
                return data[key]
    return {}


def _summary_from_messages(messages: List[Dict[str, Any]]) -> str:
    for msg in messages:
        if msg.get("role") == "user" and msg.get("content"):
            txt = str(msg.get("content", "")).replace("\n", " ").strip()
            return txt[:22] + ("..." if len(txt) > 22 else "")
    return "一次树洞聊天"


def mood_from_scores(scores: Dict[str, Any]) -> str:
    try:
        vals = [float(v) for v in scores.values() if v is not None]
        if not vals:
            return "🙂"
        avg = sum(vals) / len(vals)
        if avg >= 8:
            return "😊"
        if avg >= 6:
            return "🙂"
        if avg >= 4:
            return "😐"
        if avg >= 2.5:
            return "😟"
        return "😢"
    except Exception:
        return "🙂"


def load_history_records() -> List[Dict[str, Any]]:
    _ensure_dirs()
    records = []
    for path in HISTORY_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            stat = path.stat()
            created = _extract_created_at(data, stat.st_mtime)
            messages = _extract_messages(data)
            scores = _extract_scores(data)
            records.append({
                "id": path.stem,
                "path": str(path),
                "created_at": created,
                "date": created.strftime("%Y-%m-%d"),
                "time": created.strftime("%H:%M"),
                "month_day": created.strftime("%m/%d"),
                "weekday": created.strftime("%a").upper(),
                "emoji": mood_from_scores(scores),
                "summary": _summary_from_messages(messages),
                "messages": messages,
                "scores": scores,
                "raw": data,
            })
        except Exception:
            continue
    records.sort(key=lambda x: x["created_at"], reverse=True)
    return records


def read_history_by_id(record_id: str) -> Optional[Dict[str, Any]]:
    for rec in load_history_records():
        if rec["id"] == record_id:
            return rec
    return None
