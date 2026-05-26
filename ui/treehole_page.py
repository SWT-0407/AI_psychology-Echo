import base64
from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from services.app_storage import make_message, message_time, save_history_record, save_treehole_messages
from services.local_ai import generate_reply, score_messages
from ui.multimodal_controls import build_multimodal_prompt, render_multimodal_controls


TREEHOLE_BG_PATH = Path(__file__).resolve().parents[1] / "assets" / "treehole_diary_bg.png"


TREEHOLE_CSS = """
<style>
#MainMenu, footer { visibility: hidden; }
.stApp { background: linear-gradient(135deg, #ffe9ee 0%, #fffaf3 55%, #f5ece4 100%); }
.block-container { max-width: 1180px; padding-top: .8rem; }
.tree-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #7d5260;
    margin-bottom: 12px;
}
.tree-title { font-size: 30px; font-weight: 900; }
.tree-subtitle { font-size: 14px; color: #9d7380; }
.tree-history {
    max-width: 960px;
    margin: 14px auto 0;
    padding: 14px 18px;
    border-radius: 8px;
    background: rgba(255,255,255,.55);
    border: 1px solid rgba(220,154,169,.22);
    color: #835b66;
}
.tree-history-title {
    font-size: 13px;
    font-weight: 800;
    letter-spacing: .08em;
    color: #b58391;
    margin-bottom: 8px;
}
.tree-history-line {
    display: grid;
    grid-template-columns: 72px 1fr;
    gap: 10px;
    padding: 7px 0;
    border-top: 1px dashed rgba(220,154,169,.26);
    font-family: "Kaiti SC", "STKaiti", "KaiTi", "FangSong", serif;
    line-height: 1.55;
}
.tree-history-line:first-of-type { border-top: 0; }
.tree-history-role {
    color: #b9788a;
    font-weight: 800;
}
.tree-history-text {
    word-break: break-word;
    white-space: pre-wrap;
}
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
    border: 1px solid rgba(185,112,129,.24) !important;
    background: #ffffff !important;
    color: #875968 !important;
    font-weight: 800 !important;
}
</style>
"""


def _inject_css() -> None:
    st.markdown(TREEHOLE_CSS, unsafe_allow_html=True)


def _treehole_bg_data_url() -> str:
    if not TREEHOLE_BG_PATH.exists():
        return ""
    encoded = base64.b64encode(TREEHOLE_BG_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _latest_message(messages, role: str) -> str:
    for msg in reversed(messages):
        if msg.get("role") == role:
            return str(msg.get("content", ""))
    return ""


def _message_rating(idx: int, msg) -> None:
    role = msg.get("role", "assistant")
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


def _render_history(messages) -> None:
    visible_messages = [m for m in messages if m.get("role") in ("user", "assistant")][-6:]
    if not visible_messages:
        return
    lines = ['<div class="tree-history"><div class="tree-history-title">RECENT INK</div>']
    for msg in visible_messages:
        role = "你" if msg.get("role") == "user" else "日记"
        content = escape(str(msg.get("content", ""))).replace("\n", "<br/>")
        time_text = escape(message_time(msg))
        lines.append(
            f"""
            <div class="tree-history-line">
                <div class="tree-history-role">{role}<br/><span style="font-size:11px;font-weight:400;">{time_text}</span></div>
                <div class="tree-history-text">{content}</div>
            </div>
            """
        )
    lines.append("</div>")
    st.markdown("".join(lines), unsafe_allow_html=True)


def _render_diary_component(messages) -> None:
    bg_url = _treehole_bg_data_url()
    latest_user = _latest_message(messages, "user")
    latest_reply = _latest_message(messages, "assistant")
    today = escape(datetime.now().strftime("%Y / %m / %d"))
    fallback_bg = "linear-gradient(135deg, #fffdf7 0%, #fffaf2 100%)"
    background = f"url('{bg_url}')" if bg_url else fallback_bg
    component_html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          background: transparent;
          font-family: "Microsoft YaHei", sans-serif;
        }}
        .book {{
          width: min(1120px, 100%);
          aspect-ratio: 1458 / 1066;
          margin: 0 auto;
          position: relative;
          background: {background};
          background-repeat: no-repeat;
          background-size: 100% 100%;
          background-position: center;
          filter: drop-shadow(0 18px 32px rgba(133, 82, 92, .18));
        }}
        .date {{
          position: absolute;
          left: 10.2%;
          top: 12.2%;
          color: #dfa2ac;
          font-family: "Comic Sans MS", "Segoe Print", cursive;
          font-size: clamp(13px, 1.35vw, 18px);
          font-weight: 700;
        }}
        textarea {{
          position: absolute;
          left: 9.6%;
          top: 20.2%;
          width: 37.1%;
          height: 66.4%;
          border: 0;
          outline: 0;
          resize: none;
          overflow: auto;
          background: transparent;
          color: #6d4d58;
          font-family: "Segoe Print", "Comic Sans MS", "Kaiti SC", "KaiTi", cursive;
          font-size: clamp(15px, 1.75vw, 23px);
          line-height: 2.03;
          padding: 0 1.2%;
          caret-color: #b26478;
        }}
        textarea::placeholder {{ color: rgba(183, 129, 142, .66); }}
        .reply {{
          position: absolute;
          left: 54.8%;
          top: 20.6%;
          width: 32.6%;
          height: 63.5%;
          overflow: hidden;
          color: #7b4054;
          font-family: "Kaiti SC", "STKaiti", "KaiTi", "FangSong", serif;
          font-size: clamp(15px, 1.55vw, 22px);
          line-height: 1.85;
          white-space: pre-wrap;
          word-break: break-word;
          padding: .3% .8%;
          animation: ink 1.1s ease-out both;
        }}
        .reply.empty {{
          color: rgba(185, 126, 139, .62);
          font-family: "Segoe Print", "Comic Sans MS", cursive;
        }}
        .last-entry {{
          position: absolute;
          left: 9.8%;
          bottom: 9.6%;
          max-width: 36%;
          color: rgba(165, 103, 117, .72);
          font-family: "Kaiti SC", "KaiTi", serif;
          font-size: clamp(11px, 1vw, 14px);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }}
        .actions {{
          position: absolute;
          left: 58.5%;
          bottom: 8.2%;
          display: flex;
          align-items: center;
          gap: 10px;
        }}
        button {{
          border: 1px solid rgba(202, 126, 144, .42);
          background: rgba(255, 255, 255, .82);
          color: #93596c;
          border-radius: 999px;
          padding: 9px 20px;
          font-size: 15px;
          font-weight: 800;
          cursor: pointer;
          box-shadow: 0 8px 18px rgba(188, 122, 139, .16);
        }}
        button:hover {{ background: #fff; }}
        .hint {{
          color: rgba(149, 98, 111, .72);
          font-size: 13px;
          font-family: "Microsoft YaHei", sans-serif;
        }}
        @keyframes ink {{
          from {{ opacity: 0; clip-path: inset(0 100% 0 0); }}
          to {{ opacity: 1; clip-path: inset(0 0 0 0); }}
        }}
        @media (max-width: 720px) {{
          textarea {{ line-height: 1.65; }}
          .hint {{ display: none; }}
          button {{ padding: 7px 14px; font-size: 13px; }}
        }}
      </style>
    </head>
    <body>
      <div class="book">
        <div class="date">Date. {today}</div>
        <textarea id="entry" placeholder="把想说的话写在这里..."></textarea>
        <div class="reply {'empty' if not latest_reply else ''}">{escape(latest_reply) if latest_reply else '写完后，日记会在这里回应你。'}</div>
        <div class="last-entry">{'上一句：' + escape(latest_user) if latest_user else ''}</div>
        <div class="actions">
          <button id="submit" type="button">确定</button>
          <span class="hint">墨迹会留在纸上，日记会慢慢回信</span>
        </div>
      </div>
      <script>
        const submit = document.getElementById("submit");
        const entry = document.getElementById("entry");
        const sendEntry = () => {{
          const text = entry.value.trim();
          if (!text) {{
            entry.focus();
            return;
          }}
          const params = new URLSearchParams(window.parent.location.search);
          params.set("treehole_submit", text);
          window.parent.location.search = params.toString();
        }};
        submit.addEventListener("click", sendEntry);
        entry.addEventListener("keydown", (event) => {{
          if (event.ctrlKey && event.key === "Enter") {{
            event.preventDefault();
            sendEntry();
          }}
        }});
      </script>
    </body>
    </html>
    """
    components.html(component_html, height=820, scrolling=False)


def _submit_treehole_message(prompt: str, emotion=None) -> None:
    prompt = str(prompt or "").strip()
    if not prompt:
        return
    messages = st.session_state.get("treehole_messages", [])
    messages.append(make_message("user", prompt))
    scores = score_messages(messages)
    ai_prompt = build_multimodal_prompt(prompt, emotion)
    messages.append(make_message("assistant", generate_reply("treehole", ai_prompt, messages, scores)))
    st.session_state.treehole_messages = messages
    save_treehole_messages(messages)
    save_history_record("treehole", messages, scores, title="AI 树洞聊天")
    st.rerun()


def render_treehole_page() -> None:
    _inject_css()
    submitted = st.query_params.get("treehole_submit")
    if submitted:
        st.query_params.clear()
        _submit_treehole_message(submitted)

    st.markdown(
        """
        <div class="tree-top">
            <div class="tree-title">AI 树洞日记</div>
            <div class="tree-subtitle">在左页写下秘密，点确定后，日记会在右页用另一种笔迹回应。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("← 返回功能选择", key="tree_back_home"):
        st.session_state.page = "home"
        st.rerun()

    messages = st.session_state.get("treehole_messages", [])
    _render_diary_component(messages)

    for idx, msg in enumerate(messages):
        _message_rating(idx, msg)

    multimodal = render_multimodal_controls("treehole")
    if multimodal.get("voice_text"):
        _submit_treehole_message(multimodal["voice_text"], multimodal.get("emotion"))

    _render_history(messages)
