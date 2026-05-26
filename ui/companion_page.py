import random
import time
from datetime import datetime
from html import escape
from textwrap import dedent
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import streamlit as st

from services.app_storage import (
    create_character,
    load_characters,
    load_companion_messages,
    make_message,
    message_time,
    save_characters,
    save_companion_messages,
    save_history_record,
)
from services.local_ai import generate_reply, score_messages
from ui.multimodal_controls import build_multimodal_prompt, render_multimodal_controls


COMPANION_CSS = """
<style>
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #dcdcdc; }
.block-container {
    max-width: none;
    padding: 0;
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
    max-width: min(72%, 940px);
    padding: 12px 16px;
    border-radius: 6px;
    color: #111;
    font-size: 20px;
    line-height: 1.45;
    white-space: pre-wrap;
    word-break: break-word;
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
@media (max-width: 980px) {
    .wx-page { height: auto; overflow: visible; }
    .wx-layout { display: block; height: auto; }
    .wx-sidebar, .wx-chat { height: auto; min-height: 0; }
    .wx-list { height: auto; max-height: 420px; }
    .wx-chat-body { padding: 20px 18px; }
    .wx-bubble { max-width: 78%; font-size: 17px; }
    .wx-composer { height: auto; }
}
</style>
"""


IDENTITIES = ["恋人", "朋友", "家人", "姐姐", "哥哥", "同学", "导师", "自定义"]
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


def _simulate_unread() -> None:
    chars = load_characters()
    if not chars:
        return
    selected_id = st.session_state.get("selected_character_id")
    count = random.randint(1, min(3, len(chars)))
    for char in random.sample(chars, k=count):
        messages = load_companion_messages(char["id"])
        messages.append(make_message("assistant", _proactive_text(char)))
        save_companion_messages(char["id"], messages)
        _touch_character(char, unread_delta=0 if char["id"] == selected_id else 1)


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

    st.markdown('<div class="wx-add-panel"><div class="wx-form-title">添加联系人</div>', unsafe_allow_html=True)
    with st.form("add_contact_form", clear_on_submit=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            name = st.text_input("昵称", placeholder="例如：小晚")
        with c2:
            emoji = st.text_input("头像", value="💜")
        c3, c4 = st.columns([1, 1])
        with c3:
            identity = st.selectbox("身份", IDENTITIES, index=1)
        with c4:
            age = st.text_input("年龄", placeholder="例如：22")
        personality = st.text_area("性格", placeholder="例如：嘴硬心软、很会哄人、偶尔爱吐槽。")
        speaking_style = st.text_area("说话风格", placeholder="例如：短句、微信口吻、亲近但不过度说教。")
        submitted = st.form_submit_button("添加到通讯录", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        char = create_character(name, emoji, personality, identity, age, speaking_style)
        st.session_state.selected_character_id = char["id"]
        st.session_state.show_add_contact = False
        _mark_read(char)
        st.rerun()


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
    if role == "user":
        return dedent(f"""
        <div class="wx-msg user">
            <div class="wx-bubble">{content}</div>
            <div class="wx-msg-avatar wx-me-avatar">我</div>
        </div>
        """).strip()
    return dedent(f"""
    <div class="wx-msg assistant">
        <div class="wx-msg-avatar">{escape(char.get("emoji", "😊"))}</div>
        <div class="wx-bubble">{content}</div>
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
                <div class="wx-composer"><div class="wx-tool-row">☺ ◇ □ ✂⌄ ♫</div></div>
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
            <div class="wx-composer">
                <div class="wx-tool-row">☺ ◇ □ ✂⌄ ♫</div>
            </div>
        </main>
        """).strip(),
        unsafe_allow_html=True,
    )


def _render_selected_actions(selected: Optional[Dict[str, Any]]) -> None:
    if not selected:
        return
    a1, a2, a3 = st.columns([1, 1, 5])
    with a1:
        label = "取消置顶" if selected.get("pinned") else "置顶"
        if st.button(label, use_container_width=True, key="pin_selected"):
            selected["pinned"] = not bool(selected.get("pinned"))
            _save_character(selected)
            st.rerun()
    with a2:
        if st.button("清未读", use_container_width=True, key="clear_unread_selected"):
            _mark_read(selected)
            st.rerun()


def _submit_companion_message(selected: Dict[str, Any], prompt: str, emotion=None) -> None:
    prompt = str(prompt or "").strip()
    if not prompt:
        return

    messages = load_companion_messages(selected["id"])
    messages.append(make_message("user", prompt))
    scores = score_messages(messages)
    selected["intimacy"] = int(selected.get("intimacy") or 0) + 1
    selected["unread"] = 0
    _touch_character(selected, unread_delta=0)

    st.session_state.typing_character_id = selected["id"]
    with st.spinner(f"{selected.get('name', '对方')} 正在输入..."):
        time.sleep(0.8)
        ai_prompt = build_multimodal_prompt(prompt, emotion)
        reply = generate_reply("companion", ai_prompt, messages, scores, selected)
    st.session_state.typing_character_id = None

    messages.append(make_message("assistant", reply))
    save_companion_messages(selected["id"], messages)
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


def render_companion_page() -> None:
    _inject_css()
    st.session_state.page = "companion"

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
            with right:
                _render_chat_messages(selected)
                _render_selected_actions(selected)
                _render_message_form(selected)
