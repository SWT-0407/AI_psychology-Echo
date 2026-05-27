import base64
import hashlib
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st
import streamlit.components.v1 as components

from services.app_storage import make_message, message_time, save_history_record, save_treehole_messages
from services.local_ai import generate_reply, score_messages
from services.proactive_engine import maybe_add_care_proactive
from services.safety import assess_message_safety, attach_safety_metadata, make_safety_reply
from services.treehole_ai_service import (
    TreeholeModelError,
    generate_treehole_model_reply,
    get_last_fallback_errors,
    model_source_label,
)
from ui.crisis_alert import queue_crisis_alert, render_crisis_alert_if_needed
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
.tree-history-image {
    display: block;
    max-width: min(260px, 100%);
    max-height: 220px;
    object-fit: contain;
    border-radius: 6px;
    margin: 2px 0 8px;
    border: 1px solid rgba(220,154,169,.22);
}
.multimodal-image-panel {
    max-width: 960px;
    margin: 4px auto 12px;
    padding: 10px 12px;
    border-radius: 8px;
    border: 1px dashed rgba(185,112,129,.28);
    background: rgba(255,255,255,.46);
}
div[class*="st-key-treehole_image_toggle"] button {
    min-height: 42px !important;
    padding: 0 !important;
    font-size: 24px !important;
    border-radius: 8px !important;
}
.rating-line {
    max-width: 960px;
    margin: 8px auto 0;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #b58391;
    font-size: 13px;
}
.rating-stars {
    display: inline-flex;
    align-items: center;
    gap: 13px;
}
.rating-stars a {
    text-decoration: none;
    color: #ffd34e;
    font-size: 34px;
    line-height: 1;
    text-shadow:
        0 2px 0 rgba(245, 181, 44, .3),
        0 4px 10px rgba(255, 199, 55, .28);
    transition: transform .15s ease, filter .15s ease;
}
.rating-stars a.empty {
    color: #ffe7a2;
    opacity: .72;
}
.rating-stars a:hover {
    transform: translateY(-2px) scale(1.08);
    filter: saturate(1.18);
}
.rating-label {
    color: #b58391;
    font-size: 13px;
    font-weight: 700;
    text-align: right;
    white-space: nowrap;
}
div[class*="st-key-tree_rating_"] {
    margin-top: -4px;
}
div[class*="st-key-tree_rating_"] button {
    color: #ffd34e !important;
    text-shadow:
        0 2px 0 rgba(245, 181, 44, .3),
        0 4px 10px rgba(255, 199, 55, .28);
}
.stButton > button {
    border-radius: 12px !important;
    border: 1px solid rgba(185,112,129,.24) !important;
    background: #ffffff !important;
    color: #875968 !important;
    font-weight: 800 !important;
}
div[data-testid="stForm"] {
    max-width: 960px;
    margin: -28px auto 14px auto;
    padding: 16px 18px 18px !important;
    border: 1px solid rgba(220,154,169,.28) !important;
    border-radius: 8px !important;
    background: rgba(255, 252, 246, .82) !important;
    box-shadow: 0 14px 30px rgba(133, 82, 92, .08) !important;
}
.stTextArea textarea {
    min-height: 140px !important;
    border: 0 !important;
    border-radius: 4px !important;
    background:
        repeating-linear-gradient(
            transparent 0,
            transparent 33px,
            rgba(241, 182, 194, .55) 34px,
            transparent 35px
        ),
        rgba(255,255,255,.18) !important;
    color: #6d4d58 !important;
    font-family: "Segoe Print", "Comic Sans MS", "Kaiti SC", "KaiTi", cursive !important;
    font-size: 20px !important;
    line-height: 35px !important;
    box-shadow: none !important;
}
.stTextArea textarea::placeholder {
    color: rgba(183, 129, 142, .68) !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) {
    position: relative;
    width: min(1120px, 100%);
    max-width: 1120px;
    aspect-ratio: 1458 / 1066;
    margin: 0 auto 14px auto;
    padding: 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    background-repeat: no-repeat !important;
    background-size: 100% 100% !important;
    background-position: center !important;
    box-shadow: none !important;
    overflow: hidden;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) label {
    display: none !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) div[data-testid="stElementContainer"]:has(textarea) {
    position: absolute !important;
    left: 10.1% !important;
    top: 24.8% !important;
    width: 36.7% !important;
    height: 63.6% !important;
    z-index: 50 !important;
    pointer-events: auto !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) [data-testid="stTextArea"] {
    position: relative !important;
    left: auto !important;
    top: auto !important;
    margin-top: 0 !important;
    width: 100% !important;
    height: 100% !important;
    z-index: 50 !important;
    pointer-events: auto !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) [data-testid="stTextArea"] > div,
div[data-testid="stForm"]:has(#treehole-diary-anchor) [data-testid="stTextArea"] div[data-baseweb="textarea"] {
    height: 100% !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) div[data-testid="InputInstructions"] {
    display: none !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) textarea {
    width: 100% !important;
    height: 100% !important;
    min-height: 100% !important;
    resize: none !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    color: rgba(109, 77, 88, .78) !important;
    font-family: "Segoe Print", "Comic Sans MS", "Kaiti SC", "KaiTi", cursive !important;
    font-size: clamp(15px, 1.45vw, 22px) !important;
    line-height: 2.03 !important;
    padding: 0 1.2% !important;
    caret-color: #c86f86 !important;
    pointer-events: auto !important;
    position: relative !important;
    z-index: 51 !important;
    outline: none !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) textarea::placeholder {
    color: rgba(183, 129, 142, .56) !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) div[data-testid="stElementContainer"]:has(div[data-testid="stFormSubmitButton"]) {
    position: absolute !important;
    left: 36.2% !important;
    top: 83.6% !important;
    width: 10% !important;
    z-index: 60 !important;
    pointer-events: auto !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) div[data-testid="stElementContainer"]:has(div[data-testid="stFormSubmitButton"]):last-of-type {
    left: 77% !important;
    top: 81% !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) div[data-testid="stFormSubmitButton"] {
    position: relative !important;
    left: auto !important;
    top: 0 !important;
    margin-top: 0 !important;
    width: 100% !important;
    z-index: 60 !important;
}
div[data-testid="stForm"]:has(#treehole-diary-anchor) div[data-testid="stFormSubmitButton"] button {
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    color: #c86f86 !important;
    font-size: clamp(17px, 1.7vw, 26px) !important;
    font-weight: 950 !important;
    min-height: auto !important;
    padding: 0 !important;
}
.treehole-page-date {
    position: absolute;
    left: 10.2% !important;
    top: 0 !important;
    margin-top: calc(min(1120px, calc(100vw - 60px)) * 1066 / 1458 * .122) !important;
    color: #dfa2ac;
    font-family: "Comic Sans MS", "Segoe Print", cursive;
    font-size: clamp(13px, 1.35vw, 18px);
    font-weight: 700;
    z-index: 4;
    pointer-events: none;
}
.treehole-page-reply {
    position: absolute;
    left: 54.6% !important;
    top: 0 !important;
    margin-top: calc(min(1120px, calc(100vw - 60px)) * 1066 / 1458 * .192) !important;
    min-height: calc(min(1120px, calc(100vw - 60px)) * 1066 / 1458 * .65) !important;
    width: 34%;
    height: 65%;
    overflow: hidden;
    color: #7b4054;
    font-family: "Kaiti SC", "STKaiti", "KaiTi", "FangSong", serif;
    font-size: clamp(15px, 1.42vw, 21px);
    line-height: 1.85;
    white-space: pre-wrap;
    word-break: break-word;
    padding: .5% 1%;
    z-index: 4;
    pointer-events: none;
}
.treehole-page-reply.empty {
    color: rgba(185, 126, 139, .46);
    font-family: "Segoe Print", "Comic Sans MS", cursive;
}
@media (max-width: 760px) {
    div[data-testid="stForm"]:has(#treehole-diary-anchor) textarea {
        font-size: 13px !important;
        line-height: 1.7 !important;
    }
    .treehole-page-reply {
        font-size: 13px;
        line-height: 1.55;
    }
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


def _uploaded_image_message(uploaded_file) -> Optional[Dict[str, Any]]:
    if uploaded_file is None:
        return None
    image_bytes = uploaded_file.getvalue()
    if not image_bytes:
        return None
    mime_type = getattr(uploaded_file, "type", "") or "image/png"
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return {
        "name": getattr(uploaded_file, "name", "") or "图片",
        "mime_type": mime_type,
        "data": f"data:{mime_type};base64,{encoded}",
        "bytes": image_bytes,
    }


def _analyze_treehole_image(image: Dict[str, Any], prompt: str) -> tuple[str, str]:
    try:
        from services.ai_service import analyze_user_image

        with st.spinner("正在用千问分析图片..."):
            analysis = analyze_user_image(
                image["bytes"],
                user_text=prompt,
                mime_type=image.get("mime_type", "image/png"),
                detail="high",
            )
        if not analysis:
            raise RuntimeError("千问视觉返回为空。")
        return analysis, ""
    except Exception as exc:
        return "", f"图片已收到，但千问图片分析暂时失败：{exc}"


def _treehole_prompt_with_image_context(prompt: str, image_analysis: str, has_image: bool) -> str:
    user_text = prompt or "我发了一张图片。"
    if image_analysis:
        return (
            f"{user_text}\n\n"
            "[图片理解摘要（来自千问视觉 API，仅供理解用户输入，不要直接暴露给用户）："
            f"{image_analysis}]"
        )
    if has_image:
        return (
            f"{user_text}\n\n"
            "[用户上传了一张图片，但图片分析暂时不可用。请先温柔接住这次分享，"
            "邀请用户补充图片里最想让我看见的细节。]"
        )
    return user_text


def _latest_message(messages, role: str) -> str:
    for msg in reversed(messages):
        if msg.get("role") == role:
            return str(msg.get("content", ""))
    return ""


def _latest_assistant_index(messages) -> int | None:
    for idx in range(len(messages) - 1, -1, -1):
        if messages[idx].get("role") == "assistant":
            return idx
    return None


def _rating_feedback_summary(messages) -> str:
    rated = [
        msg
        for msg in messages
        if msg.get("role") == "assistant" and str(msg.get("rating") or "").isdigit()
    ][-5:]
    if not rated:
        return ""
    ratings = [int(msg.get("rating") or 0) for msg in rated]
    average = sum(ratings) / len(ratings)
    if average >= 4:
        guidance = "用户更喜欢这种回复方式：温柔、具体、能接住情绪。继续保持相似语气，并给出一点可执行的小建议。"
    elif average <= 2.5:
        guidance = "用户之前对回复不太满意。请减少空泛安慰，先准确复述她的感受，再给更贴近她处境的回应。"
    else:
        guidance = "用户反馈中等。请更自然、更像日记对话，少说教，多回应她刚写下的具体内容。"
    return (
        "\n\n[过往日记回复评分反馈："
        f"最近 {len(rated)} 次平均 {average:.1f}/5。{guidance}]"
    )


def _latest_model_source(messages) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            return str(msg.get("model_source") or "")
    return ""


def _save_treehole_history(messages, scores, title: str) -> None:
    record_id = save_history_record(
        "treehole",
        messages,
        scores,
        st.session_state.get("treehole_record_id"),
        title=title,
    )
    st.session_state.treehole_record_id = record_id


def _save_treehole_rating(idx: int, star: int) -> bool:
    messages = list(st.session_state.get("treehole_messages", []))
    if not (0 <= idx < len(messages) and 1 <= star <= 5):
        return False
    msg = dict(messages[idx])
    if msg.get("role") != "assistant":
        return False
    if int(msg.get("rating") or 0) == star:
        return False

    msg["rating"] = star
    msg["rated_at"] = datetime.now().isoformat(timespec="seconds")
    messages[idx] = msg
    st.session_state.treehole_messages = messages
    scores = score_messages(messages)
    save_treehole_messages(messages)
    _save_treehole_history(messages, scores, title="AI 树洞聊天")
    return True


def _handle_treehole_rating_change(idx: int, widget_key: str) -> None:
    selected = st.session_state.get(widget_key)
    if selected is None:
        return
    _save_treehole_rating(idx, int(selected) + 1)


@st.fragment
def _message_rating(idx: int, msg) -> None:
    role = msg.get("role", "assistant")
    if role == "assistant" and idx > 0:
        current = int(msg.get("rating") or 0)
        widget_key = f"tree_rating_{idx}"
        label_col, stars_col = st.columns([0.16, 0.84], gap="small", vertical_alignment="center")
        with label_col:
            st.markdown('<div class="rating-label">这次日记回应：</div>', unsafe_allow_html=True)
        with stars_col:
            st.feedback(
                "stars",
                key=widget_key,
                default=current - 1 if current else None,
                on_change=_handle_treehole_rating_change,
                args=(idx, widget_key),
                width="content",
            )


def _render_history(messages) -> None:
    visible_messages = [m for m in messages if m.get("role") in ("user", "assistant")][-6:]
    if not visible_messages:
        return
    lines = ['<div class="tree-history"><div class="tree-history-title">RECENT INK</div>']
    for msg in visible_messages:
        role = "你" if msg.get("role") == "user" else "日记"
        content = escape(str(msg.get("content", ""))).replace("\n", "<br/>")
        image_data = str(msg.get("image_data") or "")
        image_html = ""
        if image_data:
            image_alt = escape(str(msg.get("image_name") or "图片"))
            image_html = f'<img class="tree-history-image" src="{escape(image_data)}" alt="{image_alt}" />'
        time_text = escape(message_time(msg))
        lines.append(
            f'<div class="tree-history-line">'
            f'<div class="tree-history-role">{role}<br/><span style="font-size:11px;font-weight:400;">{time_text}</span></div>'
            f'<div class="tree-history-text">{image_html}{content}</div>'
            f'</div>'
        )
    lines.append("</div>")
    st.markdown("".join(lines), unsafe_allow_html=True)


def _render_diary_component(messages) -> None:
    bg_url = _treehole_bg_data_url()
    show_latest_reply = bool(st.session_state.get("treehole_show_latest_reply"))
    latest_user = _latest_message(messages, "user") if show_latest_reply else ""
    latest_reply = _latest_message(messages, "assistant") if show_latest_reply else ""
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
        .ghost-writing {{
          position: absolute;
          left: 9.6%;
          top: 20.2%;
          width: 37.1%;
          height: 66.4%;
          overflow: auto;
          color: rgba(109, 77, 88, .58);
          font-family: "Segoe Print", "Comic Sans MS", "Kaiti SC", "KaiTi", cursive;
          font-size: clamp(15px, 1.75vw, 23px);
          line-height: 2.03;
          padding: 0 1.2%;
          white-space: pre-wrap;
          word-break: break-word;
        }}
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
          .ghost-writing {{ line-height: 1.65; }}
          .hint {{ display: none; }}
          button {{ padding: 7px 14px; font-size: 13px; }}
        }}
      </style>
    </head>
    <body>
      <div class="book">
        <div class="date">Date. {today}</div>
        <div class="ghost-writing">{escape(latest_user)}</div>
        <div class="reply {'empty' if not latest_reply else ''}">{escape(latest_reply) if latest_reply else ' '}</div>
        <div class="last-entry">{'上一句：' + escape(latest_user) if latest_user else ''}</div>
      </div>
    </body>
    </html>
    """
    components.html(component_html, height=820, scrolling=False)


def _submit_treehole_message(prompt: str, emotion=None, image: Optional[Dict[str, Any]] = None) -> None:
    prompt = str(prompt or "").strip()
    if not prompt and not image:
        return

    image_analysis = ""
    if image:
        image_analysis, image_notice = _analyze_treehole_image(image, prompt)
        st.session_state.treehole_image_notice = image_notice

    entry_page = int(st.session_state.get("treehole_entry_page", 0)) + 1
    st.session_state.treehole_entry_page = entry_page
    st.session_state.treehole_entry_key = f"treehole_native_entry_{entry_page}"

    messages = st.session_state.get("treehole_messages", [])
    assessment_text = "\n".join(part for part in [prompt, image_analysis] if part) or "[图片]"
    assessment = assess_message_safety(assessment_text)
    user_message = attach_safety_metadata(make_message("user", prompt or "[图片]"), assessment)
    if image:
        user_message["image_name"] = image["name"]
        user_message["image_data"] = image["data"]
        user_message["image_mime_type"] = image.get("mime_type", "")
    if image_analysis:
        user_message["image_analysis"] = image_analysis
        user_message["image_analysis_source"] = "qwen_vision"
    messages.append(user_message)

    scores = score_messages(messages)
    if assessment.needs_support:
        reply = make_safety_reply(assessment, "树洞")
        assistant_message = make_message("assistant", reply)
        assistant_message["safety_response"] = True
        assistant_message["safety_level"] = assessment.level
        if assessment.is_crisis:
            assistant_message["crisis_popup"] = True
            queue_crisis_alert("treehole", assessment, assessment_text, "树洞")
        messages.append(assistant_message)
    else:
        base_prompt = _treehole_prompt_with_image_context(prompt, image_analysis, bool(image))
        ai_prompt = build_multimodal_prompt(base_prompt, emotion) + _rating_feedback_summary(messages)
        try:
            reply, model_source = generate_treehole_model_reply(ai_prompt, messages, scores)
            fallback_errors = get_last_fallback_errors()
            if fallback_errors and model_source != "local_finetuned":
                st.session_state.treehole_model_notice = (
                    f"本地微调模型暂时没加载成功，已改用 {model_source_label(model_source)}。"
                    f"原因：{fallback_errors[-1]}"
                )
            else:
                st.session_state.treehole_model_notice = ""
        except TreeholeModelError as exc:
            reply = generate_reply("treehole", ai_prompt, messages, scores)
            model_source = "local_template"
            st.session_state.treehole_model_notice = (
                "真实模型调用失败，已临时使用本地规则兜底。"
                f"原因：{exc}"
            )
        assistant_message = make_message("assistant", reply)
        assistant_message["model_source"] = model_source
        messages.append(assistant_message)

    st.session_state.treehole_messages = messages
    st.session_state.treehole_show_latest_reply = True
    save_treehole_messages(messages)
    _save_treehole_history(messages, scores, title="AI 树洞聊天")
    st.rerun()


def _apply_treehole_proactive(force: bool = False) -> bool:
    messages = st.session_state.get("treehole_messages", [])
    scores = score_messages(messages)
    messages, added, _ = maybe_add_care_proactive("treehole", messages, scores, force=force)
    if not added:
        return False
    st.session_state.treehole_messages = messages
    st.session_state.treehole_show_latest_reply = True
    save_treehole_messages(messages)
    _save_treehole_history(messages, scores, title="AI 树洞主动关怀")
    return True


def render_treehole_page() -> None:
    _inject_css()
    render_crisis_alert_if_needed()
    flip_page = st.query_params.get("treehole_flip")
    if flip_page:
        st.query_params.clear()
        st.session_state.treehole_show_latest_reply = False
        entry_page = int(st.session_state.get("treehole_entry_page", 0)) + 1
        st.session_state.treehole_entry_page = entry_page
        st.session_state.treehole_entry_key = f"treehole_native_entry_{entry_page}"
        st.rerun()

    rating = st.query_params.get("tree_rating")
    if rating:
        try:
            idx_text, star_text = str(rating).split(":", 1)
            _save_treehole_rating(int(idx_text), int(star_text))
        except ValueError:
            pass
        st.query_params.clear()

    submitted = st.query_params.get("treehole_submit")
    if submitted:
        st.query_params.clear()
        _submit_treehole_message(submitted)

    _apply_treehole_proactive()

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
    if st.button("收一条主动关怀", key="tree_force_proactive"):
        if _apply_treehole_proactive(force=True):
            st.rerun()
        st.toast("还没有足够画像时，先写下一点心情会更准。")
    model_notice = st.session_state.get("treehole_model_notice", "")
    if model_notice:
        st.warning(model_notice)
    image_notice = st.session_state.pop("treehole_image_notice", "")
    if image_notice:
        st.warning(image_notice)

    messages = st.session_state.get("treehole_messages", [])
    bg_url = _treehole_bg_data_url()
    if bg_url:
        st.markdown(
            f"""
            <style>
            div[data-testid="stForm"]:has(#treehole-diary-anchor) {{
                background-image: url('{bg_url}') !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
    show_latest_reply = bool(st.session_state.get("treehole_show_latest_reply"))
    latest_reply = _latest_message(messages, "assistant") if show_latest_reply else ""
    reply_html = escape(latest_reply).replace("\n", "<br/>") if latest_reply else "日记会在这里回应你。"
    reply_class = "" if latest_reply else " empty"
    today = escape(datetime.now().strftime("%Y / %m / %d"))
    entry_key = st.session_state.setdefault("treehole_entry_key", "treehole_native_entry_0")

    with st.form("treehole_diary_form", clear_on_submit=False):
        st.markdown(
            f"""
            <span id="treehole-diary-anchor"></span>
            <div class="treehole-page-date">{today}</div>
            <div class="treehole-page-reply{reply_class}">{reply_html}</div>
            """,
            unsafe_allow_html=True,
        )
        prompt = st.text_area(
            "写在日记左页",
            key=entry_key,
            placeholder="把想说的话写在这里...",
            label_visibility="collapsed",
        )
        form_submitted = st.form_submit_button("确定", use_container_width=True)
        flip_submitted = st.form_submit_button("翻页", use_container_width=True)
    if flip_submitted:
        st.session_state.treehole_show_latest_reply = False
        entry_page = int(st.session_state.get("treehole_entry_page", 0)) + 1
        st.session_state.treehole_entry_page = entry_page
        st.session_state.treehole_entry_key = f"treehole_native_entry_{entry_page}"
        st.rerun()
    if form_submitted:
        _submit_treehole_message(prompt)

    latest_assistant_idx = _latest_assistant_index(messages)
    latest_source = _latest_model_source(messages)
    if latest_source:
        st.caption(f"本次回复来源：{model_source_label(latest_source)}")
    if latest_assistant_idx is not None:
        _message_rating(latest_assistant_idx, messages[latest_assistant_idx])

    multimodal = render_multimodal_controls("treehole", image_upload=True)
    image = _uploaded_image_message(multimodal.get("image_file"))
    if image:
        image_digest_key = "treehole_image_digest"
        image_digest = hashlib.sha256(image["bytes"]).hexdigest() + image["name"]
        if st.session_state.get(image_digest_key) != image_digest:
            st.session_state[image_digest_key] = image_digest
            _submit_treehole_message(prompt, multimodal.get("emotion"), image=image)
    if multimodal.get("voice_text"):
        _submit_treehole_message(multimodal["voice_text"], multimodal.get("emotion"))

    _render_history(messages)
