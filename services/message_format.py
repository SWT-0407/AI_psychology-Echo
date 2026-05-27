"""
Helpers for storing and displaying chat messages as readable plain text.
"""
import json
import os
import re
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional


ROLE_LABELS = {
    "user": "我",
    "assistant": "Echo",
    "system": "系统",
}

_BLOCK_TAGS = {"address", "article", "blockquote", "br", "div", "li", "p", "section", "tr"}
_HTML_RE = re.compile(r"</?[a-zA-Z][^>]*>")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        if tag.lower() in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    cleaned: List[str] = []
    previous_blank = False
    for line in lines:
        if not line:
            if cleaned and not previous_blank:
                cleaned.append("")
            previous_blank = True
            continue
        cleaned.append(line)
        previous_blank = False
    return "\n".join(cleaned).strip()


def html_to_readable_text(value: Any) -> str:
    """Convert plain text or a small HTML fragment into user-readable text."""
    text = unescape(str(value or ""))
    if not text:
        return ""
    if not _HTML_RE.search(text):
        return _normalize_text(text)

    parser = _TextExtractor()
    try:
        parser.feed(text)
        parser.close()
        extracted = parser.text()
    except Exception:
        extracted = _HTML_RE.sub("", text)
    return _normalize_text(unescape(extracted))


def normalize_messages(messages: Any) -> List[Dict[str, Any]]:
    """Return message dicts with readable text content while preserving metadata."""
    if not isinstance(messages, list):
        return []

    normalized: List[Dict[str, Any]] = []
    for item in messages:
        if isinstance(item, dict):
            msg = dict(item)
            role = str(msg.get("role") or "assistant")
            content = msg.get("content", "")
        else:
            msg = {}
            role = "assistant"
            content = item

        if role not in ROLE_LABELS:
            role = "assistant"

        msg["role"] = role
        msg["content"] = html_to_readable_text(content)
        normalized.append(msg)
    return normalized


def message_time_label(msg: Dict[str, Any]) -> str:
    raw: Optional[Any] = msg.get("time") or msg.get("created_at") or msg.get("timestamp")
    if not raw:
        return ""
    raw_text = str(raw)
    try:
        return datetime.fromisoformat(raw_text.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return raw_text[:16] if len(raw_text) >= 16 else raw_text


def messages_to_readable_text(messages: Any, title: str = "对话记录") -> str:
    """Format a message list as a plain-text conversation transcript."""
    lines: List[str] = []
    if title:
        lines.extend([title, ""])

    for msg in normalize_messages(messages):
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        speaker = ROLE_LABELS.get(str(msg.get("role")), "Echo")
        time_label = message_time_label(msg)
        header = f"{speaker}（{time_label}）：" if time_label else f"{speaker}："
        lines.extend([header, content, ""])

    return "\n".join(lines).strip() + ("\n" if lines else "")


def dumps_storage_json(data: Any) -> str:
    """Serialize runtime storage JSON compactly unless pretty output is requested."""
    pretty = os.getenv("ECHO_PRETTY_JSON", "").strip().lower() in {"1", "true", "yes", "on"}
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def compact_session_record(data: Any) -> Any:
    """
    Return a storage-light session record.

    Older records kept the same conversation in multiple fields. New writes keep
    only ``messages`` on disk; compatibility fields are restored by
    ``hydrate_session_record`` when records are loaded.
    """
    if not isinstance(data, dict):
        return data

    compact = dict(data)
    messages = normalize_messages(compact.get("messages") or compact.get("display_messages") or [])
    if messages:
        compact["messages"] = messages
    else:
        compact.pop("messages", None)

    for field in (
        "display_messages",
        "conversation_text",
        "diary_profile",
        "diary_moods",
        "user_profile_summary",
    ):
        compact.pop(field, None)

    compact["storage_version"] = "diary_v3_compact"
    return compact


def hydrate_session_record(data: Any, include_conversation_text: bool = True) -> Any:
    """Restore compatibility fields expected by existing UI/read paths."""
    if not isinstance(data, dict):
        return data

    hydrated = dict(data)
    messages = normalize_messages(hydrated.get("messages") or hydrated.get("display_messages") or [])
    hydrated["messages"] = messages
    hydrated["display_messages"] = messages

    if include_conversation_text and not hydrated.get("conversation_text"):
        title = hydrated.get("title") or hydrated.get("summary") or "conversation"
        hydrated["conversation_text"] = messages_to_readable_text(messages, title)

    return hydrated
