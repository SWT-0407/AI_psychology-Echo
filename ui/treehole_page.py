from html import escape

import streamlit as st

from services.app_storage import make_message, message_time, save_history_record, save_treehole_messages
from services.local_ai import generate_reply, score_messages


TREEHOLE_CSS = """
<style>
#MainMenu, footer { visibility: hidden; }
.stApp { background: linear-gradient(135deg, #f8eadf 0%, #edf8f1 100%); }
.block-container { max-width: 980px; padding-top: 1rem; }
.tree-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #4d6258;
    margin-bottom: 16px;
}
.tree-title { font-size: 32px; font-weight: 900; }
.tree-chat {
    min-height: 620px;
    border-radius: 18px;
    border: 2px solid rgba(93,116,100,.16);
    background: rgba(255,255,255,.62);
    padding: 24px;
    box-shadow: 0 14px 40px rgba(98,112,96,.12);
}
.tree-msg { display: flex; margin: 16px 0; gap: 10px; }
.tree-msg.user { justify-content: flex-end; }
.tree-avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid rgba(80,80,80,.12);
    flex: 0 0 auto;
}
.tree-bubble {
    max-width: 68%;
    padding: 13px 16px;
    border-radius: 18px;
    line-height: 1.65;
    color: #47564f;
    word-break: break-word;
    white-space: pre-wrap;
}
.tree-msg.assistant .tree-bubble { background: #fffaf1; border-top-left-radius: 6px; }
.tree-msg.user .tree-bubble { background: #dff0e5; border-top-right-radius: 6px; }
.tree-time { color: #829389; font-size: 12px; margin-top: 4px; }
.rating-line { margin-top: 8px; }
.rating-line .stButton > button {
    min-height: 30px;
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
    color: #df9a35 !important;
    font-size: 22px !important;
}
.stButton > button {
    border-radius: 12px !important;
    border: 1px solid rgba(70,90,70,.18) !important;
    background: #ffffff !important;
    color: #4e655b !important;
    font-weight: 800 !important;
}
</style>
"""


def _inject_css() -> None:
    st.markdown(TREEHOLE_CSS, unsafe_allow_html=True)


def _message_block(msg, idx: int) -> None:
    role = msg.get("role", "assistant")
    content = escape(str(msg.get("content", ""))).replace("\n", "<br/>")
    avatar = "🌳" if role == "assistant" else "你"
    row_class = "assistant" if role == "assistant" else "user"
    st.markdown(
        f"""
        <div class="tree-msg {row_class}">
            {'<div class="tree-avatar">' + avatar + '</div>' if role == 'assistant' else ''}
            <div>
                <div class="tree-bubble">{content}</div>
                <div class="tree-time">{escape(message_time(msg))}</div>
            </div>
            {'<div class="tree-avatar">' + avatar + '</div>' if role == 'user' else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if role == "assistant" and idx > 0:
        current = int(msg.get("rating") or 0)
        cols = st.columns([1, 1, 1, 1, 1, 6])
        for star in range(1, 6):
            with cols[star - 1]:
                label = "★" if star <= current else "☆"
                if st.button(label, key=f"tree_rating_{idx}_{star}", help=f"{star} 星"):
                    st.session_state.treehole_messages[idx]["rating"] = star
                    save_treehole_messages(st.session_state.treehole_messages)
                    st.rerun()


def render_treehole_page() -> None:
    _inject_css()
    st.markdown(
        """
        <div class="tree-top">
            <div class="tree-title">🌳 AI 树洞</div>
            <div>每条 AI 回复都可以评分，也可以跳过。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("← 返回功能选择", key="tree_back_home"):
        st.session_state.page = "home"
        st.rerun()

    messages = st.session_state.get("treehole_messages", [])
    st.markdown('<div class="tree-chat">', unsafe_allow_html=True)
    for idx, msg in enumerate(messages):
        _message_block(msg, idx)
    st.markdown("</div>", unsafe_allow_html=True)

    prompt = st.chat_input("说点什么给树洞听...", key="treehole_input")
    if prompt:
        messages.append(make_message("user", prompt))
        scores = score_messages(messages)
        messages.append(make_message("assistant", generate_reply("treehole", prompt, messages, scores)))
        st.session_state.treehole_messages = messages
        save_treehole_messages(messages)
        save_history_record("treehole", messages, scores, title="AI 树洞聊天")
        st.rerun()
