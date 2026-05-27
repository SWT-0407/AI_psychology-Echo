import random
import base64
import time
from datetime import datetime
from html import escape
from textwrap import dedent
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

from services.app_storage import (
    build_answer_model,
    companion_chat_path,
    create_character,
    load_characters,
    load_companion_messages,
    make_message,
    message_time,
    save_characters,
    save_companion_messages,
    save_history_record,
    update_companion_state,
)
from services.local_ai import generate_proactive_message, generate_reply, score_messages
from services.proactive_engine import maybe_add_character_proactive
from services.safety import assess_message_safety, attach_safety_metadata, make_safety_reply
from ui.multimodal_controls import build_multimodal_prompt, get_multimodal_manager, render_multimodal_controls


COMPANION_CSS = """
<style>
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #dcdcdc; }
.block-container {
    max-width: none;
    padding: 0;
    width: 100vw;
}
html, body, .stApp {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
}
[data-testid="stVerticalBlock"] { gap: 0; }
[data-testid="stHorizontalBlock"] { gap: 0 !important; }
.wx-page,
.st-key-wx_page {
    height: 100vh;
    min-height: 760px;
    background: #f5f5f5;
    color: #111;
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", Arial, sans-serif;
    overflow: hidden;
}
.wx-window-bar {
    height: 36px;
    background: #d9d9d9;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 34px;
    padding: 0 14px;
    color: #333;
    font-size: 20px;
    box-sizing: border-box;
}
.wx-layout,
.st-key-wx_layout {
    height: calc(100vh - 36px);
    min-height: 724px;
    display: grid;
    grid-template-columns: 356px 1fr;
    background: #f5f5f5;
}
.wx-sidebar {
    height: calc(100vh - 36px);
    min-height: 724px;
    background: #e9e9eb;
    border-right: 1px solid #d8d8dc;
    overflow: hidden;
}
.wx-left-head {
    height: 108px;
    padding: 17px 14px 0 14px;
    box-sizing: border-box;
}
.wx-search-row {
    display: grid;
    grid-template-columns: 1fr 46px;
    gap: 12px;
    align-items: center;
}
.wx-search-fake {
    height: 39px;
    background: #f7f7f9;
    border-radius: 8px;
    display: flex;
    align-items: center;
    color: #9a9aa0;
    padding: 0 13px;
    gap: 8px;
    font-size: 16px;
}
.wx-plus {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 2px solid #3e4145;
    color: #3e4145;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    line-height: 1;
}
.wx-add-panel {
    background: #fff;
    border: 1px solid #dcdde0;
    border-radius: 6px;
    padding: 12px;
    margin: 12px 14px;
}
div[data-testid="stDialog"] {
    z-index: 100000 !important;
}
div[data-testid="stDialog"] section[role="dialog"] {
    width: min(820px, calc(100vw - 32px)) !important;
    max-height: min(86vh, 820px) !important;
    overflow-y: auto !important;
}
div[data-testid="stDialog"] section[role="dialog"] > div {
    padding: 22px 26px 24px !important;
}
div[data-testid="stDialog"] .stForm {
    border: 0;
    padding: 0;
}
.wx-profile-note {
    color: #737373;
    font-size: 14px;
    margin: -4px 0 14px;
}
.wx-list {
    height: calc(100vh - 144px);
    min-height: 580px;
    overflow-y: auto;
    padding-bottom: 18px;
}
.wx-contact {
    position: relative;
    display: grid;
    grid-template-columns: 54px 1fr 46px;
    gap: 14px;
    align-items: center;
    height: 98px;
    padding: 0 18px 0 14px;
    box-sizing: border-box;
    text-decoration: none;
    color: inherit;
    background: #e9e9eb;
    border-bottom: 1px solid #dddddf;
    cursor: default;
}
.wx-contact:hover { background: #dedfe2; }
.wx-contact.active {
    background: #18b36d;
    color: #fff;
    border-bottom-color: #18b36d;
}
.wx-avatar {
    width: 54px;
    height: 54px;
    border-radius: 5px;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    flex: 0 0 auto;
    box-shadow: inset 0 0 0 1px rgba(0,0,0,.04);
}
.wx-avatar.file {
    background: #16cf6d;
    color: #fff;
    font-size: 26px;
    font-weight: 800;
}
.wx-contact.active .wx-avatar { box-shadow: none; }
.wx-contact-main { min-width: 0; }
.wx-contact-name {
    font-size: 20px;
    line-height: 1.2;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}
.wx-contact-preview {
    margin-top: 8px;
    color: #9a9aa0;
    font-size: 16px;
    line-height: 1.25;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}
.wx-contact.active .wx-contact-preview { color: rgba(255,255,255,.82); }
.wx-contact-time {
    align-self: start;
    margin-top: 30px;
    text-align: right;
    color: #999ca2;
    font-size: 15px;
    white-space: nowrap;
}
.wx-contact.active .wx-contact-time { color: rgba(255,255,255,.82); }
.wx-unread {
    position: absolute;
    left: 57px;
    top: 18px;
    min-width: 14px;
    height: 14px;
    padding: 0 4px;
    border-radius: 999px;
    background: #fa5151;
    color: #fff;
    font-size: 10px;
    line-height: 14px;
    text-align: center;
}
.wx-muted {
    position: absolute;
    right: 20px;
    bottom: 18px;
    color: #9a9aa0;
}
.wx-contact.active .wx-muted { color: rgba(255,255,255,.75); }
.wx-chat {
    height: calc(100vh - 36px);
    min-height: 724px;
    background: #f5f5f5;
    display: flex;
    flex-direction: column;
}
.wx-chat-head {
    height: 72px;
    border-bottom: 1px solid #e5e5e5;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 26px;
    box-sizing: border-box;
    background: #f7f7f7;
}
.wx-chat-title {
    color: #111;
    font-size: 22px;
    font-weight: 400;
}
.wx-chat-actions {
    display: flex;
    align-items: center;
    gap: 16px;
    color: #3d3d3d;
    font-size: 24px;
}
.wx-chat-body {
    flex: 1;
    min-height: 420px;
    padding: 24px 72px 20px 72px;
    overflow-y: auto;
    box-sizing: border-box;
}
.wx-time-line {
    color: #9b9b9b;
    text-align: center;
    font-size: 14px;
    margin: 6px 0 22px;
}
.wx-msg {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin: 22px 0;
}
.wx-msg.user {
    justify-content: flex-end;
}
.wx-msg-avatar {
    width: 54px;
    height: 54px;
    border-radius: 6px;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    flex: 0 0 auto;
    box-shadow: inset 0 0 0 1px rgba(0,0,0,.04);
}
.wx-me-avatar {
    background: #e8eef8;
    color: #38527a;
    font-size: 20px;
    font-weight: 700;
}
.wx-bubble {
    position: relative;
    max-width: min(72%, 940px) !important;
    min-width: 32px;
    padding: 12px 16px;
    border-radius: 6px;
    color: #111;
    font-size: 20px;
    line-height: 1.45;
    white-space: pre-wrap;
    word-break: break-word;
}
.wx-msg-image {
    display: block;
    max-width: min(360px, 100%);
    max-height: 320px;
    border-radius: 6px;
    margin-bottom: 6px;
    object-fit: contain;
}
.wx-msg.assistant .wx-bubble {
    background: #fff;
}
.wx-msg.user .wx-bubble {
    background: #95ec69;
}
.wx-msg.assistant .wx-bubble:before {
    content: "";
    position: absolute;
    left: -8px;
    top: 16px;
    border-top: 8px solid transparent;
    border-bottom: 8px solid transparent;
    border-right: 9px solid #fff;
}
.wx-msg.user .wx-bubble:after {
    content: "";
    position: absolute;
    right: -8px;
    top: 16px;
    border-top: 8px solid transparent;
    border-bottom: 8px solid transparent;
    border-left: 9px solid #95ec69;
}
.wx-typing {
    margin-left: 70px;
    color: #8c8c8c;
    font-size: 15px;
}
.wx-empty {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #8d8d8d;
    font-size: 17px;
}
.wx-composer {
    height: 195px;
    border-top: 1px solid #dddddd;
    background: #fff;
    padding: 14px 22px 12px;
    box-sizing: border-box;
}
.wx-tool-row {
    display: flex;
    align-items: center;
    gap: 24px;
    color: #505050;
    font-size: 24px;
    margin-bottom: 8px;
}
.wx-composer .wx-tool-row {
    display: none;
}
.wx-send-row {
    display: flex;
    align-items: flex-end;
    gap: 14px;
}
.wx-side-actions {
    position: fixed;
    left: 374px;
    bottom: 14px;
    display: flex;
    gap: 8px;
    z-index: 3;
}
.wx-side-action {
    border: 1px solid #d4d4d4;
    background: #fff;
    border-radius: 4px;
    padding: 5px 10px;
    color: #555;
    font-size: 13px;
}
.wx-form-title {
    font-size: 15px;
    color: #333;
    margin-bottom: 8px;
    font-weight: 700;
}
.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div {
    border-radius: 6px !important;
    border-color: #d9d9d9 !important;
    background: #fff !important;
}
.wx-composer + div textarea,
textarea[aria-label="发消息"] {
    min-height: 86px !important;
    border: 0 !important;
    box-shadow: none !important;
    font-size: 18px !important;
    resize: none !important;
}
.stButton > button,
.stFormSubmitButton > button {
    border-radius: 6px !important;
    border: 1px solid #d8d8d8 !important;
    background: #f5f5f5 !important;
    color: #111 !important;
}
.stFormSubmitButton > button {
    background: #f5f5f5 !important;
    color: #9b9b9b !important;
    min-width: 82px;
}
.st-key-wx_page {
    height: 100vh;
    max-height: 100vh;
    overflow: hidden;
}
.st-key-wx_layout > div[data-testid="stHorizontalBlock"] {
    height: calc(100vh - 36px);
    display: block !important;
    gap: 0 !important;
}
.st-key-wx_layout > div[data-testid="stHorizontalBlock"] > div {
    width: 100% !important;
    min-width: 0 !important;
}
.wx-sidebar {
    display: grid !important;
    grid-template-columns: 88px minmax(0, 1fr) !important;
    width: 420px !important;
    position: fixed !important;
    left: 0 !important;
    top: 36px !important;
    bottom: 0 !important;
    height: calc(100vh - 36px) !important;
    min-height: 0 !important;
    z-index: 10 !important;
}
.wx-rail {
    background: #dedede;
    border-right: 1px solid #d3d3d3;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 18px 0 14px;
    box-sizing: border-box;
    gap: 26px;
}
.wx-rail-avatar {
    width: 54px;
    height: 54px;
    border-radius: 8px;
    background: #f7f7f7;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
}
.wx-rail-icon {
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #696969;
    font-size: 27px;
}
.wx-rail-icon.active { color: #07c160; }
.wx-rail-spacer { flex: 1; }
.wx-conv-panel {
    min-width: 0;
    height: 100%;
    background: #e9e9eb;
    overflow: hidden;
}
.wx-sidebar-buttons {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    padding: 0 14px 12px;
}
.wx-sidebar-buttons .stButton > button {
    min-height: 34px;
    font-size: 13px;
    padding: 4px 8px;
}
.wx-chat,
.st-key-wx_layout .wx-chat {
    position: fixed !important;
    left: 420px !important;
    right: 0 !important;
    top: 36px !important;
    bottom: 0 !important;
    width: auto !important;
    height: calc(100vh - 36px) !important;
    min-height: 0 !important;
    overflow: hidden !important;
    z-index: 9 !important;
}
.wx-chat *,
.wx-sidebar * {
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
}
.wx-chat-body {
    height: calc(100vh - 36px - 72px - 196px) !important;
    min-height: 0 !important;
    flex: 0 0 auto !important;
    width: 100% !important;
}
.wx-composer {
    height: 196px !important;
    flex: 0 0 196px !important;
}
.st-key-wx_composer_controls {
    position: fixed !important;
    left: 440px !important;
    right: 16px !important;
    bottom: 20px !important;
    z-index: 20 !important;
    height: 150px !important;
    background: #fff;
    border: 1px solid #dcdcdc;
    border-radius: 8px;
    padding: 8px 14px 8px;
    box-sizing: border-box;
}
.st-key-wx_composer_controls [data-testid="stHorizontalBlock"] {
    gap: 8px !important;
    align-items: center !important;
}
.st-key-wx_composer_controls textarea {
    min-height: 96px !important;
    height: 96px !important;
    border: 0 !important;
    box-shadow: none !important;
    font-size: 18px !important;
    resize: none !important;
    padding: 8px 0 !important;
    line-height: 1.45 !important;
}
.st-key-wx_composer_controls .stForm {
    border: 0;
    padding: 0;
}
.wx-input-shell {
    height: 100%;
    display: flex;
    flex-direction: column;
}
.wx-bottom-tools {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #5f6368;
    min-height: 24px;
}
.wx-tool-spacer {
    flex: 1;
}
.wx-emoji-panel {
    border-top: 1px solid #eeeeee;
    padding: 6px 0 2px;
}
.wx-attachment-panel {
    border-top: 1px solid #eeeeee;
    padding-top: 8px;
    margin-top: 2px;
}
.wx-listen-status {
    color: #6f7378;
    font-size: 14px;
    line-height: 24px;
    padding-top: 4px;
    white-space: nowrap;
}
.st-key-wx_composer_controls .stButton > button,
.st-key-wx_composer_controls .stFormSubmitButton > button {
    min-height: 24px !important;
    height: 24px !important;
    width: 28px !important;
    min-width: 28px !important;
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
    color: #5f6368 !important;
    font-size: 21px !important;
    box-shadow: none !important;
    line-height: 1 !important;
}
.st-key-wx_composer_controls button {
    min-height: 24px !important;
    height: 24px !important;
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}
.st-key-wx_composer_controls div[data-testid="stButton"],
.st-key-wx_composer_controls .stButton {
    height: 24px !important;
    min-height: 24px !important;
}
.st-key-wx_composer_controls .stButton > button:hover,
.st-key-wx_composer_controls .stButton > button:focus,
.st-key-wx_composer_controls .stButton > button:active {
    border: 0 !important;
    background: transparent !important;
    color: #111 !important;
    box-shadow: none !important;
}
.st-key-wx_composer_controls .stFormSubmitButton > button {
    min-width: 68px !important;
    border: 1px solid #e4e4e4 !important;
    background: #f4f4f4 !important;
    color: #b5b5b5 !important;
    font-size: 14px !important;
}
.st-key-wx_composer_controls [class*="_send_button"] button {
    width: 56px !important;
    min-width: 56px !important;
    height: 28px !important;
    min-height: 28px !important;
    padding: 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    color: #4f5965 !important;
    font-size: 27px !important;
    line-height: 1 !important;
}
.st-key-wx_composer_controls [class*="_send_button"] button:hover,
.st-key-wx_composer_controls [class*="_send_button"] button:focus,
.st-key-wx_composer_controls [class*="_send_button"] button:active {
    background: transparent !important;
    color: #111 !important;
    border: 0 !important;
    box-shadow: none !important;
}
.st-key-wx_composer_controls .stFileUploader,
.st-key-wx_composer_controls [data-testid="stFileUploader"] {
    max-width: 220px !important;
}
.st-key-wx_composer_controls [data-testid="stFileUploader"] section {
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
}
.st-key-wx_composer_controls [data-testid="stFileUploader"] section > div {
    display: none !important;
}
.st-key-wx_composer_controls [data-testid="stFileUploader"] small {
    display: none !important;
}
.st-key-wx_composer_controls [data-testid="stFileUploader"] label {
    font-size: 0 !important;
}
.st-key-wx_composer_controls [data-testid="stFileUploader"] label:after {
    content: "□";
    font-size: 22px;
    color: #5f6368;
}
.st-key-wx_composer_controls [data-testid="stAudioInput"] {
    max-width: 120px !important;
}
.st-key-wx_composer_controls [data-testid="stAudioInput"] label {
    font-size: 0 !important;
}
.st-key-wx_composer_controls [data-testid="stAudioInput"] label:after {
    content: "🎙";
    font-size: 19px;
    color: #5f6368;
}
.st-key-wx_composer_controls [data-testid="stAudioInput"] > div {
    min-height: 28px !important;
}
.wx-list {
    position: fixed !important;
    left: 88px !important;
    top: 144px !important;
    bottom: 0 !important;
    width: 332px !important;
    height: auto !important;
    min-height: 0 !important;
    z-index: 13 !important;
    background: #e9e9eb;
}
.wx-contact {
    width: 332px !important;
    left: 0 !important;
}
.st-key-toggle_add_contact,
.st-key-simulate_unread,
.st-key-companion_back_home {
    position: fixed !important;
    z-index: 30 !important;
    top: 108px !important;
    width: 92px !important;
}
.st-key-toggle_add_contact { left: 102px !important; }
.st-key-simulate_unread { left: 202px !important; }
.st-key-companion_back_home { left: 302px !important; }
.st-key-toggle_add_contact button,
.st-key-simulate_unread button,
.st-key-companion_back_home button {
    min-height: 28px !important;
    height: 28px !important;
    padding: 0 8px !important;
    font-size: 13px !important;
}
@media (max-width: 980px) {
    html, body, .stApp { overflow: auto; }
    .wx-page, .st-key-wx_page { height: auto; max-height: none; overflow: visible; }
    .wx-layout { display: block; height: auto; }
    .wx-sidebar { position: static !important; width: 100% !important; grid-template-columns: 64px 1fr !important; height: auto !important; min-height: 0 !important; }
    .wx-rail { min-height: 420px; }
    .st-key-wx_layout .wx-chat, .wx-chat { position: static !important; height: auto !important; min-height: 0 !important; }
    .wx-list { height: auto; max-height: 420px; }
    .wx-chat-body { height: 55vh !important; padding: 20px 18px; }
    .wx-bubble { max-width: 78%; font-size: 17px; }
    .wx-composer { height: auto; }
    .st-key-wx_composer_controls {
        position: static !important;
        height: auto !important;
        margin: 0;
    }
}
</style>
"""


IDENTITIES = ["恋人", "朋友", "家人", "姐姐", "哥哥", "同学", "导师", "自定义"]
ACQUAINTANCE_METHODS = ["同学", "同事", "网友", "前任", "朋友介绍", "亲人", "兴趣圈", "其他"]
GENDER_OPTIONS = ["未填写", "女", "男", "非二元/其他", "不想标注"]
PROACTIVE_LINES = {
    "恋人": ["还没睡？", "今天有没有乖乖吃饭。", "突然有点想你。"],
    "朋友": ["你又安静一整天了。", "出来聊两句？", "别一个人憋着。"],
    "家人": ["今天吃饭了吗？", "别熬太晚。", "累了就先休息。"],
    "姐姐": ["今天过得怎么样？", "有事可以跟姐姐说。", "先喝口水，慢慢讲。"],
    "哥哥": ["谁欺负你了？", "别怕，我听着。", "今天还撑得住吗？"],
    "同学": ["作业写了吗哈哈。", "今天课多不多？", "要不要一起摸会儿鱼。"],
    "导师": ["今天最困扰你的问题是什么？", "我们可以先拆一个小步骤。", "先把事情说清楚，不急着评价。"],
}


def _inject_css() -> None:
    st.markdown(COMPANION_CSS, unsafe_allow_html=True)


def _query_selected_id() -> Optional[str]:
    try:
        value = st.query_params.get("companion_char")
        if isinstance(value, list):
            return value[0] if value else None
        return value
    except Exception:
        return None


def _fmt_time(raw: str) -> str:
    try:
        dt = datetime.fromisoformat(str(raw))
        now = datetime.now()
        if dt.date() == now.date():
            return dt.strftime("%H:%M")
        return dt.strftime("%m/%d")
    except Exception:
        return ""


def _last_message(messages: List[Dict[str, Any]]) -> str:
    if not messages:
        return "还没有消息"
    return str(messages[-1].get("content", "")) or "还没有消息"


def _last_time(messages: List[Dict[str, Any]]) -> str:
    if not messages:
        return ""
    return _fmt_time(messages[-1].get("time") or messages[-1].get("timestamp") or "")


def _sort_characters(chars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        chars,
        key=lambda c: (
            bool(c.get("pinned")),
            int(c.get("unread") or 0),
            str(c.get("updated_at") or c.get("last_active") or ""),
        ),
        reverse=True,
    )


def _save_character(char: Dict[str, Any]) -> None:
    chars = load_characters()
    for idx, item in enumerate(chars):
        if item.get("id") == char.get("id"):
            char["updated_at"] = datetime.now().isoformat(timespec="seconds")
            chars[idx] = char
            save_characters(chars)
            return


def _mark_read(char: Dict[str, Any]) -> None:
    if int(char.get("unread") or 0) == 0:
        return
    char["unread"] = 0
    char["last_read_at"] = datetime.now().isoformat(timespec="seconds")
    _save_character(char)


def _touch_character(char: Dict[str, Any], unread_delta: int = 0) -> None:
    char["last_active"] = datetime.now().isoformat(timespec="seconds")
    char["updated_at"] = char["last_active"]
    char["unread"] = max(0, int(char.get("unread") or 0) + unread_delta)
    _save_character(char)


def _proactive_text(char: Dict[str, Any]) -> str:
    identity = char.get("identity", "朋友")
    lines = PROACTIVE_LINES.get(identity, PROACTIVE_LINES["朋友"])
    return random.choice(lines)


def _proactive_text(char: Dict[str, Any]) -> str:
    try:
        return generate_proactive_message(char)
    except Exception:
        identity = char.get("identity", "朋友")
        lines = PROACTIVE_LINES.get(identity) or next(iter(PROACTIVE_LINES.values()))
        return random.choice(lines)


def _simulate_unread() -> None:
    chars = load_characters()
    if not chars:
        return
    selected_id = st.session_state.get("selected_character_id")
    count = random.randint(1, min(3, len(chars)))
    for char in random.sample(chars, k=count):
        messages = load_companion_messages(char["id"])
        messages, added, _ = maybe_add_character_proactive(char, messages, force=True)
        if added:
            save_companion_messages(char["id"], messages)
            _touch_character(char, unread_delta=0 if char["id"] == selected_id else 1)


def _maybe_auto_unread(characters: List[Dict[str, Any]], selected_id: Optional[str]) -> bool:
    for char in _sort_characters(characters):
        messages = load_companion_messages(char["id"])
        messages, added, _ = maybe_add_character_proactive(char, messages)
        if not added:
            continue
        save_companion_messages(char["id"], messages)
        _touch_character(char, unread_delta=0 if char["id"] == selected_id else 1)
        return True
    return False


def _handle_query_selection(characters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    query_id = _query_selected_id()
    if query_id:
        st.session_state.selected_character_id = query_id

    selected_id = st.session_state.get("selected_character_id")
    selected = next((c for c in characters if c.get("id") == selected_id), None)
    if not selected and characters:
        selected = _sort_characters(characters)[0]
        st.session_state.selected_character_id = selected["id"]

    if selected:
        _mark_read(selected)
    return selected


def _contact_href(char_id: str) -> str:
    return f"?companion_char={quote(str(char_id))}"


def _contact_html(char: Dict[str, Any], active: bool, messages: List[Dict[str, Any]]) -> str:
    unread = int(char.get("unread") or 0)
    unread_html = f'<span class="wx-unread">{unread}</span>' if unread else ""
    active_class = " active" if active else ""
    pin = "📌 " if char.get("pinned") else ""
    muted = '<span class="wx-muted">⌁</span>' if not active else ""
    return dedent(f"""
    <a class="wx-contact{active_class}" href="{_contact_href(char.get("id", ""))}">
        <div class="wx-avatar">{escape(char.get("emoji", "😊"))}</div>
        <div class="wx-contact-main">
            <div class="wx-contact-name">{pin}{escape(char.get("name", "新朋友"))}</div>
            <div class="wx-contact-preview">{escape(_last_message(messages))}</div>
        </div>
        <div class="wx-contact-time">{escape(_last_time(messages))}</div>
        {unread_html}
        {muted}
    </a>
    """).strip()


def _file_helper_row(active: bool) -> str:
    active_class = " active" if active else ""
    return dedent(f"""
    <a class="wx-contact{active_class}" href="?companion_file=1">
        <div class="wx-avatar file">↪</div>
        <div class="wx-contact-main">
            <div class="wx-contact-name">文件传输助手</div>
            <div class="wx-contact-preview">这里是你的 AI 角色聊天区</div>
        </div>
        <div class="wx-contact-time">{datetime.now().strftime("%H:%M")}</div>
    </a>
    """).strip()


def _render_add_contact(characters: List[Dict[str, Any]]) -> None:
    should_show = st.session_state.get("show_add_contact", False) or not characters
    if not should_show:
        return

    def save_profile(
        name: str,
        emoji: str,
        identity: str,
        gender: str,
        age: str,
        occupation: str,
        city: str,
        daily_rhythm: str,
        acquaintance_method: str,
        acquaintance_duration: str,
        contact_frequency: str,
        interaction_content: str,
        offline_interaction: str,
        specialness: str,
        boundaries: str,
        emotional_pattern: str,
        core_need: str,
        core_fear: str,
        defense_mechanism: str,
        affection_style: str,
        family_background: str,
        important_events: str,
        unfinished_complex: str,
        personal_desire: str,
        day_night_variation: str,
        recent_state: str,
        emotional_residue: str,
        impression: str,
    ) -> None:
        personality_parts = [
            emotional_pattern.strip(),
            f"需要{core_need.strip()}" if core_need.strip() else "",
            f"害怕{core_fear.strip()}" if core_fear.strip() else "",
            f"防御方式：{defense_mechanism.strip()}" if defense_mechanism.strip() else "",
            f"亲近表达：{affection_style.strip()}" if affection_style.strip() else "",
            impression.strip(),
        ]
        personality = "；".join(part for part in personality_parts if part) or "温柔、耐心、愿意认真陪伴聊天。"
        speaking_style = "自然、像微信聊天一样简短亲近。"
        char = create_character(name, emoji, personality, identity, age, speaking_style)
        char["gender"] = "" if gender == "未填写" else gender
        char["occupation"] = occupation.strip()
        char["city"] = city.strip()
        char["relationship_profile"] = {
            "acquaintance_method": acquaintance_method,
            "acquaintance_duration": acquaintance_duration.strip(),
            "contact_frequency": contact_frequency.strip(),
            "interaction_content": interaction_content.strip(),
            "offline_interaction": offline_interaction.strip(),
            "specialness": specialness.strip(),
            "boundaries": boundaries.strip(),
            "emotional_pattern": emotional_pattern.strip(),
            "impression": impression.strip(),
        }
        char["persona_profile"] = {
            "surface": {
                "gender": "" if gender == "未填写" else gender,
                "age": age.strip(),
                "occupation": occupation.strip(),
                "city": city.strip(),
                "daily_rhythm": daily_rhythm.strip(),
                "speaking_style": speaking_style,
            },
            "core": {
                "need": core_need.strip(),
                "fear": core_fear.strip(),
                "defense": defense_mechanism.strip(),
                "affection": affection_style.strip(),
            },
            "life": {
                "family": family_background.strip(),
                "key_events": important_events.strip(),
                "unfinished": unfinished_complex.strip(),
            },
            "time": {
                "day_night": day_night_variation.strip(),
                "recent_state": recent_state.strip(),
                "emotional_residue": emotional_residue.strip(),
            },
            "desire": {
                "personal_desire": personal_desire.strip(),
            },
        }
        char["answer_model"] = build_answer_model(char)
        _save_character(char)
        st.session_state.selected_character_id = char["id"]
        st.session_state.show_add_contact = False
        _mark_read(char)
        st.rerun()

    def render_form() -> None:
        st.markdown('<div class="wx-profile-note">为这个人建一张关系档案，空着也可以之后再补。</div>', unsafe_allow_html=True)
        with st.form("add_contact_form", clear_on_submit=False):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                name = st.text_input("昵称", placeholder="例如：小月")
            with c2:
                gender = st.selectbox("性别", GENDER_OPTIONS)
            with c3:
                age = st.text_input("年龄", placeholder="例如：22")

            c_profile1, c_profile2 = st.columns([1, 1])
            with c_profile1:
                occupation = st.text_input("职业/身份", placeholder="例如：设计师、研究生、咖啡店店员")
            with c_profile2:
                city = st.text_input("城市", placeholder="例如：上海")
            daily_rhythm = st.text_area(
                "生活节奏",
                placeholder="例如：长期加班，独居，睡眠差，深夜更活跃，白天回复断断续续",
                height=70,
            )

            c4, c5, c6 = st.columns([1, 1, 1])
            with c4:
                emoji = st.text_input("头像", value="😊")
            with c5:
                identity = st.selectbox("关系身份", IDENTITIES, index=1)
            with c6:
                acquaintance_method = st.selectbox("怎么认识的", ACQUAINTANCE_METHODS)

            acquaintance_duration = st.text_input(
                "认识多久了",
                placeholder="例如：三个月；最近两周突然变亲近",
            )
            contact_frequency = st.text_area(
                "联系频率",
                placeholder="多久聊天、谁更主动、聊到什么程度",
                height=76,
            )
            interaction_content = st.text_area(
                "聊天/相处内容",
                placeholder="只是办事，还是会聊情绪、生活、秘密、未来",
                height=76,
            )
            offline_interaction = st.text_area(
                "现实中的互动",
                placeholder="是否经常单独见面、陪伴、送东西、互相照顾",
                height=76,
            )
            specialness = st.text_area(
                "对彼此的特殊性",
                placeholder="有没有区别对待、优先级高不高",
                height=76,
            )
            boundaries = st.text_area(
                "边界感",
                placeholder="会不会避嫌、隐藏、暧昧、吃醋",
                height=76,
            )
            emotional_pattern = st.text_area(
                "那个人本身的性格与情感模式",
                placeholder="外向还是依赖型、是否容易和人暧昧",
                height=76,
            )
            st.markdown("**人格结构**")
            p1, p2 = st.columns([1, 1])
            with p1:
                core_need = st.text_input("核心需求", placeholder="例如：被认可、安全感、自由")
            with p2:
                core_fear = st.text_input("核心恐惧", placeholder="例如：被忽视、失控、无价值")
            p3, p4 = st.columns([1, 1])
            with p3:
                defense_mechanism = st.text_input("防御机制", placeholder="例如：嘴硬、冷淡、开玩笑、逃避")
            with p4:
                affection_style = st.text_input("情感表达方式", placeholder="例如：分享生活、照顾细节、故意冷一下")

            st.markdown("**人生痕迹**")
            family_background = st.text_area(
                "原生家庭",
                placeholder="例如：从小被要求懂事，习惯自己消化情绪",
                height=70,
            )
            important_events = st.text_area(
                "重要事件",
                placeholder="至少包含一次遗憾、一次高光、一次创伤或一段难忘关系",
                height=70,
            )
            unfinished_complex = st.text_area(
                "未完成情结",
                placeholder="例如：想证明自己，不甘心，忘不掉某段关系",
                height=70,
            )

            st.markdown("**时间感与欲望**")
            personal_desire = st.text_area(
                "私人欲望/目标",
                placeholder="例如：想做出自己的作品集，想逃离消耗型关系，想被认真选择",
                height=70,
            )
            t1, t2 = st.columns([1, 1])
            with t1:
                day_night_variation = st.text_area(
                    "昼夜状态变化",
                    placeholder="例如：白天理性克制，深夜更感性",
                    height=70,
                )
            with t2:
                recent_state = st.text_area(
                    "最近状态",
                    placeholder="例如：最近项目压身，情绪比平时更敏感",
                    height=70,
                )
            emotional_residue = st.text_area(
                "情绪残留",
                placeholder="例如：昨天被临时放鸽子，今天还会有点冷淡",
                height=70,
            )
            impression = st.text_area(
                "你对 TA 的印象",
                placeholder="写下你的直觉、关键词、让你在意的细节……",
                height=104,
            )
            submitted = st.form_submit_button("建立档案", use_container_width=True)

        if submitted:
            save_profile(
                name,
                emoji,
                identity,
                gender,
                age,
                occupation,
                city,
                daily_rhythm,
                acquaintance_method,
                acquaintance_duration,
                contact_frequency,
                interaction_content,
                offline_interaction,
                specialness,
                boundaries,
                emotional_pattern,
                core_need,
                core_fear,
                defense_mechanism,
                affection_style,
                family_background,
                important_events,
                unfinished_complex,
                personal_desire,
                day_night_variation,
                recent_state,
                emotional_residue,
                impression,
            )
        if st.button("取消", use_container_width=True, key="cancel_add_contact"):
            st.session_state.show_add_contact = False
            st.rerun()

    if hasattr(st, "dialog"):
        @st.dialog("新建人物档案", width="large")
        def add_contact_dialog() -> None:
            render_form()

        add_contact_dialog()
    else:
        st.markdown('<div class="wx-add-panel"><div class="wx-form-title">新建人物档案</div>', unsafe_allow_html=True)
        render_form()
        st.markdown("</div>", unsafe_allow_html=True)


def _render_sidebar(characters: List[Dict[str, Any]], selected: Optional[Dict[str, Any]]) -> None:
    selected_id = selected.get("id") if selected else ""
    st.markdown('<aside class="wx-sidebar">', unsafe_allow_html=True)
    st.markdown(
        dedent("""
        <div class="wx-left-head">
            <div class="wx-search-row">
                <div class="wx-search-fake">⌕ <span>搜索</span></div>
                <div class="wx-plus">+</div>
            </div>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

    b1, b2, b3 = st.columns([1, 1, 1])
    with b1:
        if st.button("添加", use_container_width=True, key="toggle_add_contact"):
            st.session_state.show_add_contact = not st.session_state.get("show_add_contact", False)
            st.rerun()
    with b2:
        if st.button("新消息", use_container_width=True, key="simulate_unread"):
            _simulate_unread()
            st.rerun()
    with b3:
        if st.button("首页", use_container_width=True, key="companion_back_home"):
            st.session_state.page = "home"
            st.rerun()

    _render_add_contact(characters)

    st.markdown('<div class="wx-list">', unsafe_allow_html=True)
    if not characters:
        st.markdown(_file_helper_row(active=True), unsafe_allow_html=True)
    for char in _sort_characters(load_characters()):
        messages = load_companion_messages(char["id"])
        st.markdown(_contact_html(char, char.get("id") == selected_id, messages), unsafe_allow_html=True)
    st.markdown("</div></aside>", unsafe_allow_html=True)


def _message_html(msg: Dict[str, Any], char: Dict[str, Any]) -> str:
    role = msg.get("role", "assistant")
    content = escape(str(msg.get("content", ""))).replace("\n", "<br/>")
    image_data = str(msg.get("image_data") or "")
    image_html = ""
    if image_data:
        image_alt = escape(str(msg.get("image_name") or "图片"))
        image_html = f'<img class="wx-msg-image" src="{escape(image_data)}" alt="{image_alt}" />'
    if role == "user":
        return dedent(f"""
        <div class="wx-msg user">
            <div class="wx-bubble">{image_html}{content}</div>
            <div class="wx-msg-avatar wx-me-avatar">我</div>
        </div>
        """).strip()
    return dedent(f"""
    <div class="wx-msg assistant">
        <div class="wx-msg-avatar">{escape(char.get("emoji", "😊"))}</div>
        <div class="wx-bubble">{image_html}{content}</div>
    </div>
    """).strip()


def _message_time_line(messages: List[Dict[str, Any]]) -> str:
    if not messages:
        return datetime.now().strftime("%H:%M")
    first = messages[0]
    raw = first.get("time") or first.get("timestamp") or ""
    try:
        dt = datetime.fromisoformat(str(raw))
        now = datetime.now()
        if dt.date() == now.date():
            return dt.strftime("%H:%M")
        return dt.strftime("%Y年%m月%d日 %H:%M")
    except Exception:
        return message_time(first) or datetime.now().strftime("%H:%M")


def _render_chat_messages(selected: Optional[Dict[str, Any]]) -> None:
    if not selected:
        st.markdown(
            dedent("""
            <main class="wx-chat">
                <div class="wx-chat-head">
                    <div class="wx-chat-title">消息</div>
                    <div class="wx-chat-actions">☰</div>
                </div>
                <div class="wx-chat-body"><div class="wx-empty">从左侧添加或选择一个联系人</div></div>
                <div class="wx-composer"></div>
            </main>
            """).strip(),
            unsafe_allow_html=True,
        )
        return

    messages = load_companion_messages(selected["id"])
    title = escape(selected.get("name", "新朋友"))
    subtitle = " · ".join(
        x for x in [
            selected.get("identity", "朋友"),
            f'{selected.get("age")}岁' if selected.get("age") else "",
            "已置顶" if selected.get("pinned") else "",
        ]
        if x
    )
    message_html = [f'<div class="wx-time-line">{escape(_message_time_line(messages))}</div>']
    for msg in messages[-40:]:
        if msg.get("role") in ("user", "assistant"):
            message_html.append(_message_html(msg, selected))
    if st.session_state.get("typing_character_id") == selected.get("id"):
        message_html.append(f'<div class="wx-typing">{title} 正在输入...</div>')

    st.markdown(
        dedent(f"""
        <main class="wx-chat">
            <div class="wx-chat-head">
                <div>
                    <div class="wx-chat-title">{title}</div>
                    <div style="font-size:13px;color:#888;margin-top:3px;">{escape(subtitle or "微信风格陪伴聊天")}</div>
                </div>
                <div class="wx-chat-actions">☵⌄</div>
            </div>
            <div class="wx-chat-body">
                {''.join(message_html)}
            </div>
            <div class="wx-composer"></div>
        </main>
        """).strip(),
        unsafe_allow_html=True,
    )


def _uploaded_image_message(uploaded_file) -> Optional[Dict[str, str]]:
    if uploaded_file is None:
        return None
    image_bytes = uploaded_file.getvalue()
    if not image_bytes:
        return None
    mime_type = getattr(uploaded_file, "type", "") or "image/png"
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return {
        "name": getattr(uploaded_file, "name", "") or "图片",
        "data": f"data:{mime_type};base64,{encoded}",
    }


def _audio_to_text(scope: str, audio_file) -> str:
    if audio_file is None:
        return ""
    audio_bytes = audio_file.getvalue()
    if not audio_bytes:
        return ""
    digest_key = f"{scope}_compact_audio_digest"
    digest = str(hash(audio_bytes))
    if st.session_state.get(digest_key) == digest:
        return ""

    mm = get_multimodal_manager()
    filename = getattr(audio_file, "name", "") or "audio.webm"
    mime_type = getattr(audio_file, "type", "") or "audio/webm"
    with st.spinner("正在识别录音..."):
        text = mm.transcribe_audio(audio_bytes, filename=filename, mime_type=mime_type).strip()
    st.session_state[digest_key] = digest
    if text:
        st.toast(f"已识别：{text}")
    elif getattr(mm, "last_speech_error", ""):
        st.error(f"语音识别服务调用失败：{mm.last_speech_error}")
    else:
        st.warning("录音已收到，但没有识别出文字。")
    return text


def _submit_companion_message(selected: Dict[str, Any], prompt: str, emotion=None, image=None) -> None:
    prompt = str(prompt or "").strip()
    if not prompt and not image:
        return

    messages = load_companion_messages(selected["id"])
    assessment = assess_message_safety(prompt)
    user_message = attach_safety_metadata(make_message("user", prompt or "[图片]"), assessment)
    if image:
        user_message["image_name"] = image["name"]
        user_message["image_data"] = image["data"]
    messages.append(user_message)
    scores = score_messages(messages)
    selected["unread"] = 0
    _touch_character(selected, unread_delta=0)

    if assessment.needs_support:
        reply = make_safety_reply(assessment, selected.get("name", "Echo"))
    else:
        st.session_state.typing_character_id = selected["id"]
        with st.spinner(f"{selected.get('name', '对方')} 正在输入..."):
            time.sleep(0.8)
            ai_prompt = build_multimodal_prompt(prompt or "我发了一张图片。", emotion)
            reply = generate_reply("companion", ai_prompt, messages, scores, selected)
        st.session_state.typing_character_id = None

    assistant_message = make_message("assistant", reply)
    if assessment.needs_support:
        assistant_message["safety_response"] = True
        assistant_message["safety_level"] = assessment.level
    messages.append(assistant_message)
    save_companion_messages(selected["id"], messages)
    update_companion_state(selected, prompt or "我发了一张图片。", reply, emotion)
    _touch_character(selected, unread_delta=0)
    save_history_record("companion", messages, scores, title=f"与 {selected.get('name', '新朋友')} 的聊天")
    st.rerun()


def _render_message_form(selected: Optional[Dict[str, Any]]) -> None:
    if not selected:
        return

    multimodal = render_multimodal_controls(f"companion_{selected['id']}")
    if multimodal.get("voice_text"):
        _submit_companion_message(selected, multimodal["voice_text"], multimodal.get("emotion"))

    with st.form(f"send_companion_{selected['id']}", clear_on_submit=True):
        text_col, send_col = st.columns([8, 1])
        with text_col:
            prompt = st.text_area(
                "发消息",
                label_visibility="collapsed",
                placeholder="输入消息...",
                height=92,
                key=f"companion_text_{selected['id']}",
            )
        with send_col:
            submitted = st.form_submit_button("发送", use_container_width=True)

    if submitted and prompt.strip():
        _submit_companion_message(selected, prompt, multimodal.get("emotion"))


def _query_param(name: str) -> Optional[str]:
    try:
        value = st.query_params.get(name)
        if isinstance(value, list):
            return value[0] if value else None
        return value
    except Exception:
        return None


def _clear_companion_action_params(selected_id: Optional[str] = None) -> None:
    try:
        st.query_params.clear()
        if selected_id:
            st.query_params["companion_char"] = selected_id
    except Exception:
        pass


def _handle_contact_action(characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    action = _query_param("contact_action")
    char_id = _query_param("contact_target")
    if action not in {"toggle_pin", "clear_unread", "delete_chat", "delete_role"} or not char_id:
        return characters

    target = next((c for c in characters if c.get("id") == char_id), None)
    if not target:
        _clear_companion_action_params(st.session_state.get("selected_character_id"))
        st.rerun()

    if action == "toggle_pin":
        target["pinned"] = not bool(target.get("pinned"))
        _save_character(target)
        st.toast("已置顶" if target.get("pinned") else "已取消置顶")
        _clear_companion_action_params(char_id)
        st.rerun()

    if action == "clear_unread":
        _mark_read(target)
        st.toast("未读已清空")
        _clear_companion_action_params(char_id)
        st.rerun()

    if action == "delete_chat":
        save_companion_messages(char_id, [])
        _touch_character(target, unread_delta=0)
        st.toast("聊天记录已删除")
        _clear_companion_action_params(char_id)
        st.rerun()

    remaining = [c for c in characters if c.get("id") != char_id]
    save_characters(remaining)
    try:
        companion_chat_path(char_id).unlink(missing_ok=True)
    except Exception:
        save_companion_messages(char_id, [])

    if st.session_state.get("selected_character_id") == char_id:
        st.session_state.selected_character_id = remaining[0]["id"] if remaining else None
    st.toast("角色已删除")
    _clear_companion_action_params(st.session_state.get("selected_character_id"))
    st.rerun()


def _render_sidebar(characters: List[Dict[str, Any]], selected: Optional[Dict[str, Any]]) -> None:
    selected_id = selected.get("id") if selected else ""
    st.markdown(
        dedent("""
        <aside class="wx-sidebar">
            <nav class="wx-rail">
                <div class="wx-rail-avatar">🙂</div>
                <div class="wx-rail-icon active">●</div>
                <div class="wx-rail-icon">☰</div>
                <div class="wx-rail-icon">□</div>
                <div class="wx-rail-icon">◎</div>
                <div class="wx-rail-spacer"></div>
                <div class="wx-rail-icon">▣</div>
                <div class="wx-rail-icon">☷</div>
            </nav>
            <section class="wx-conv-panel">
                <div class="wx-left-head">
                    <div class="wx-search-row">
                        <div class="wx-search-fake">⌕<span>搜索</span></div>
                        <div class="wx-plus">+</div>
                    </div>
                </div>
        """).strip(),
        unsafe_allow_html=True,
    )

    st.markdown('<div class="wx-sidebar-buttons">', unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 1, 1])
    with b1:
        if st.button("添加", use_container_width=True, key="toggle_add_contact"):
            st.session_state.show_add_contact = not st.session_state.get("show_add_contact", False)
            st.rerun()
    with b2:
        if st.button("新消息", use_container_width=True, key="simulate_unread"):
            _simulate_unread()
            st.rerun()
    with b3:
        if st.button("首页", use_container_width=True, key="companion_back_home"):
            st.session_state.page = "home"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    _render_add_contact(characters)

    list_html = ['<div class="wx-list">']
    if not characters:
        list_html.append(_file_helper_row(active=True))
    for char in _sort_characters(load_characters()):
        messages = load_companion_messages(char["id"])
        active = char.get("id") == selected_id
        unread = int(char.get("unread") or 0)
        unread_html = f'<span class="wx-unread">{unread}</span>' if unread else ""
        muted = '<span class="wx-muted">⌁</span>' if not active else ""
        pin = "📌 " if char.get("pinned") else ""
        char_id = escape(str(char.get("id", "")))
        pinned_attr = "1" if char.get("pinned") else "0"
        list_html.append(dedent(f"""
        <div class="wx-contact{' active' if active else ''}" data-char-id="{char_id}" data-pinned="{pinned_attr}" onclick="window.location.href='{_contact_href(char.get("id", ""))}'">
            <div class="wx-avatar">{escape(char.get("emoji", "😊"))}</div>
            <div class="wx-contact-main">
                <div class="wx-contact-name">{pin}{escape(char.get("name", "新朋友"))}</div>
                <div class="wx-contact-preview">{escape(_last_message(messages))}</div>
            </div>
            <div class="wx-contact-time">{escape(_last_time(messages))}</div>
            {unread_html}
            {muted}
        </div>
        """).strip())
    list_html.append("</div></section></aside>")
    st.markdown("".join(list_html), unsafe_allow_html=True)


def _install_contact_context_menu() -> None:
    components.html(
        """
        <script>
        (() => {
          const doc = window.parent.document;
          const old = doc.getElementById("wx-contact-context-menu");
          if (old) old.remove();

          const menu = doc.createElement("div");
          menu.id = "wx-contact-context-menu";
          menu.style.cssText = [
            "position:fixed",
            "display:none",
            "z-index:99999",
            "min-width:150px",
            "padding:6px 0",
            "border:1px solid #cfcfcf",
            "border-radius:6px",
            "background:#fff",
            "box-shadow:0 8px 24px rgba(0,0,0,.16)",
            "font:14px Microsoft YaHei, Segoe UI, sans-serif",
            "color:#222"
          ].join(";");

          const item = (label, action, danger) => {
            const el = doc.createElement("div");
            el.textContent = label;
            el.dataset.action = action;
            el.style.cssText = `padding:9px 16px;cursor:default;color:${danger ? "#d93025" : "#222"}`;
            el.addEventListener("mouseenter", () => el.style.background = "#f2f2f2");
            el.addEventListener("mouseleave", () => el.style.background = "transparent");
            return el;
          };

          menu.appendChild(item("置顶", "toggle_pin", false));
          menu.appendChild(item("清未读", "clear_unread", false));
          menu.appendChild(item("删除聊天", "delete_chat", false));
          menu.appendChild(item("删除角色", "delete_role", true));
          doc.body.appendChild(menu);

          let currentId = null;
          let currentPinned = false;
          const hide = () => {
            menu.style.display = "none";
            currentId = null;
            currentPinned = false;
          };

          doc.addEventListener("contextmenu", (event) => {
            const contact = event.target.closest && event.target.closest(".wx-contact[data-char-id]");
            if (!contact) {
              hide();
              return;
            }
            event.preventDefault();
            currentId = contact.dataset.charId;
            currentPinned = contact.dataset.pinned === "1";
            const pinItem = menu.querySelector('[data-action="toggle_pin"]');
            if (pinItem) pinItem.textContent = currentPinned ? "取消置顶" : "置顶";
            menu.style.left = `${event.clientX}px`;
            menu.style.top = `${event.clientY}px`;
            menu.style.display = "block";
          }, true);

          doc.addEventListener("click", (event) => {
            const action = event.target.dataset && event.target.dataset.action;
            if (!action || !currentId) {
              hide();
              return;
            }
            if (action === "toggle_pin" || action === "clear_unread") {
              const url = new URL(window.parent.location.href);
              url.searchParams.set("companion_char", currentId);
              url.searchParams.set("contact_target", currentId);
              url.searchParams.set("contact_action", action);
              window.parent.location.href = url.toString();
              hide();
              return;
            }
            const message = action === "delete_role"
              ? "确定删除这个角色和它的聊天记录吗？"
              : "确定删除这个角色的聊天记录吗？";
            if (window.parent.confirm(message)) {
              const url = new URL(window.parent.location.href);
              url.searchParams.set("companion_char", currentId);
              url.searchParams.set("contact_target", currentId);
              url.searchParams.set("contact_action", action);
              window.parent.location.href = url.toString();
            }
            hide();
          }, true);

          doc.addEventListener("scroll", hide, true);
          doc.addEventListener("keydown", (event) => {
            if (event.key === "Escape") hide();
          }, true);
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def _render_message_form(selected: Optional[Dict[str, Any]]) -> None:
    if not selected:
        return

    with st.container(key="wx_composer_controls"):
        scope = f"companion_{selected['id']}"
        text_key = f"companion_text_{selected['id']}"
        emoji_key = f"{scope}_emoji_panel"
        image_key = f"{scope}_image_upload"
        audio_key = f"{scope}_audio_input_compact"
        uploaded_image = None
        voice_clicked = False

        prompt = st.text_area(
            "发送消息",
            label_visibility="collapsed",
            placeholder="输入消息...",
            height=100,
            key=text_key,
        )

        tool_cols = st.columns([0.32, 0.32, 0.32, 7.52, 1.14])
        with tool_cols[0]:
            if st.button("☺", key=f"{scope}_emoji_toggle", help="发表情"):
                st.session_state[emoji_key] = not st.session_state.get(emoji_key, False)
                st.rerun()
        with tool_cols[1]:
            if st.button("□", key=f"{scope}_image_toggle", help="发送图片"):
                st.session_state[f"{scope}_image_panel"] = not st.session_state.get(f"{scope}_image_panel", False)
                st.rerun()
        with tool_cols[2]:
            audio_file = None
            voice_clicked = st.button("🎙", key=f"{scope}_voice_button", help="录音")
        with tool_cols[4]:
            submitted = st.button("↗", key=f"{scope}_send_button", use_container_width=True, help="发送")

        if voice_clicked:
            with st.spinner("正在聆听..."):
                voice_text = get_multimodal_manager().listen_speech(timeout=5.0)
            if voice_text:
                _submit_companion_message(selected, voice_text)
            else:
                st.warning("未检测到语音，请重试。")

        if st.session_state.get(f"{scope}_image_panel", False):
            st.markdown('<div class="wx-attachment-panel">', unsafe_allow_html=True)
            uploaded_image = st.file_uploader(
                "发送图片",
                type=["png", "jpg", "jpeg", "webp"],
                label_visibility="collapsed",
                key=image_key,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.get(emoji_key, False):
            st.markdown('<div class="wx-emoji-panel">', unsafe_allow_html=True)
            emoji_cols = st.columns(12)
            emojis = ["😀", "😊", "😂", "🥺", "😍", "😌", "😢", "😡", "👍", "❤️", "🌙", "✨"]
            for idx, emoji in enumerate(emojis):
                with emoji_cols[idx]:
                    if st.button(emoji, key=f"{scope}_emoji_{idx}", help=f"发送 {emoji}"):
                        st.session_state[emoji_key] = False
                        _submit_companion_message(selected, emoji)
            st.markdown("</div>", unsafe_allow_html=True)

        image = _uploaded_image_message(uploaded_image)
        if image:
            image_digest_key = f"{scope}_image_digest"
            image_digest = image["data"][:80] + image["name"]
            if st.session_state.get(image_digest_key) != image_digest:
                st.session_state[image_digest_key] = image_digest
                _submit_companion_message(selected, "", image=image)

        voice_text = _audio_to_text(scope, audio_file)
        if voice_text:
            _submit_companion_message(selected, voice_text)

        if submitted and prompt.strip():
            _submit_companion_message(selected, prompt)


def render_companion_page() -> None:
    _inject_css()
    st.session_state.page = "companion"

    characters = _handle_contact_action(load_characters())
    selected = _handle_query_selection(characters)
    if _maybe_auto_unread(characters, selected.get("id") if selected else None):
        characters = load_characters()
        selected = _handle_query_selection(characters)

    page_container = st.container(key="wx_page")
    with page_container:
        st.markdown('<div class="wx-window-bar">⌖ － □ ×</div>', unsafe_allow_html=True)
        layout_container = st.container(key="wx_layout")
        with layout_container:
            left, right = st.columns([0.245, 0.755], gap="small")
            with left:
                _render_sidebar(characters, selected)
                _install_contact_context_menu()
            with right:
                _render_chat_messages(selected)
                _render_message_form(selected)
