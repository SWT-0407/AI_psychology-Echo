import calendar
import base64
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from services.app_storage import (
    list_history_records,
    load_history_record,
    make_message,
    message_date,
    message_time,
    save_history_record,
    save_mood,
    save_profile,
    update_history_messages,
)
from services.local_ai import DIMENSIONS, generate_reply, make_report, score_messages


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "assets" / "diary_templates"
TEMPLATE_FILES = {
    "cover": "cover.jpg",
    "intro": "intro.jpg",
    "calendar": "calendar.jpg",
    "history": "history.jpg",
    "chat": "chat.jpg",
}


DIARY_CSS = """
<style>
#MainMenu, footer { visibility: hidden; }
.stApp { background: #f6d9df; }
.block-container { max-width: 1180px; padding-top: 1rem; }
.diary-shell {
    border: 3px solid #8f8f8f;
    border-radius: 8px;
    background: #f6d9df;
    overflow: hidden;
    box-shadow: 0 16px 42px rgba(90,64,74,.18);
    margin-bottom: 16px;
}
.diary-tabs {
    height: 54px;
    background: #d7dde6;
    border-bottom: 3px solid #8f8f8f;
    display: flex;
    align-items: end;
    gap: 2px;
    padding: 0 14px;
    overflow-x: auto;
}
.diary-tab {
    min-width: 58px;
    height: 40px;
    border: 3px solid #8f8f8f;
    border-bottom: 0;
    border-radius: 14px 14px 0 0;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    color: #8a8a8a;
}
.diary-tab.small { min-width: 72px; font-size: 13px; }
.diary-tab.active { background: #aebddd; color: #fff; }
.diary-tab.month-active { background: #efc6d1; color: #666; }
.diary-page {
    min-height: 650px;
    padding: 30px 36px;
    position: relative;
    overflow: hidden;
}
.cover-scene {
    min-height: 610px;
    display: grid;
    grid-template-columns: 1fr 1.25fr 1fr;
    align-items: center;
    gap: 20px;
    position: relative;
}
.cover-scene:after {
    content: "";
    position: absolute;
    left: -36px;
    right: -36px;
    bottom: -30px;
    height: 188px;
    background: #eca7b8;
    border-top: 3px solid #333;
    z-index: 0;
}
.cover-scene > div {
    position: relative;
    z-index: 1;
}
.big-bubble {
    background: white;
    border: 3px solid #333;
    border-radius: 50%;
    min-height: 310px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    text-align: center;
}
.big-bubble:after {
    content: "";
    position: absolute;
    right: 52px;
    bottom: -35px;
    width: 48px;
    height: 64px;
    background: #fff;
    border-right: 3px solid #333;
    border-bottom: 3px solid #333;
    transform: rotate(24deg);
}
.title-year {
    color: #aa94cf;
    font-size: 62px;
    font-weight: 950;
    letter-spacing: 4px;
    text-shadow: 2px 2px 0 #333;
    line-height: 1;
}
.title-main {
    color: #8ab49e;
    font-size: 52px;
    font-weight: 950;
    letter-spacing: 2px;
    text-shadow: 2px 2px 0 #333;
    line-height: 1.05;
}
.doodle { text-align: center; font-size: 82px; margin: 28px 0; }
.cover-prop {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 96px;
    min-height: 84px;
    margin: 10px;
    font-size: 62px;
}
.cover-side-note {
    display: inline-block;
    background: #fffaf0;
    border: 3px solid #333;
    border-radius: 8px;
    padding: 12px 16px;
    transform: rotate(-4deg);
    font-size: 38px;
}
.loading-text {
    text-align: center;
    color: #704d59;
    font-size: 24px;
    font-weight: 800;
    margin-top: 18px;
}
.intro-grid {
    min-height: 420px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 34px;
    align-items: center;
}
.intro-title { text-align: center; }
.avatar-frame {
    width: 150px;
    height: 150px;
    margin: 0 auto 20px;
    background: #fff;
    border: 3px solid #333;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 82px;
}
.profile-lines {
    max-width: 520px;
    margin: 0 auto 14px auto;
    color: #282229;
    font-weight: 900;
    font-size: 19px;
}
.profile-lines span {
    display: inline-block;
    min-width: 120px;
}
.profile-form-wrap {
    max-width: 760px;
    margin: -22px auto 0 auto;
}
.tip-box {
    background: rgba(255,255,255,.62);
    border: 2px dashed #d09aa8;
    border-radius: 12px;
    padding: 12px 16px;
    color: #735861;
    margin: 12px 0;
    font-size: 17px;
}
.calendar-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 18px;
    margin-bottom: 16px;
}
.month-title {
    color: #8f83c6;
    font-size: 62px;
    font-weight: 950;
    letter-spacing: 3px;
    text-shadow: 2px 2px 0 #333;
}
.calendar-note {
    flex: 1;
    max-width: 520px;
    min-height: 64px;
    border: 3px solid #333;
    border-radius: 24px;
    background: #fff;
    padding: 12px 20px;
    color: #66535a;
    font-size: 18px;
}
.calendar-deco {
    display: grid;
    grid-template-columns: 126px 1fr 120px;
    align-items: center;
    gap: 14px;
    margin-bottom: 10px;
}
.calendar-bear {
    font-size: 86px;
    text-align: center;
}
.calendar-cloud {
    min-height: 74px;
    background: #fff;
    border: 3px solid #333;
    border-radius: 42px;
    box-shadow: 0 5px 0 rgba(0,0,0,.04);
    position: relative;
}
.calendar-cloud:before,
.calendar-cloud:after {
    content: "⭐";
    position: absolute;
    top: -18px;
    font-size: 34px;
}
.calendar-cloud:before { left: -28px; }
.calendar-cloud:after { right: -22px; }
.calendar-cat {
    font-size: 72px;
    text-align: center;
}
.mood-calendar {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    background: #fff;
    border: 3px solid #333;
}
.mood-calendar th {
    height: 36px;
    background: #aeb9dc;
    color: #834e59;
    border: 2px solid #333;
}
.mood-calendar td {
    height: 92px;
    border: 2px solid #333;
    vertical-align: top;
    padding: 6px;
    position: relative;
    font-weight: 700;
}
.mood-emoji {
    position: absolute;
    left: 50%;
    top: 52%;
    transform: translate(-50%, -50%);
    font-size: 32px;
}
.history-title {
    color: #8c747b;
    font-size: 32px;
    font-weight: 950;
    margin-bottom: 16px;
}
.history-header {
    display: grid;
    grid-template-columns: 100px 1fr;
    align-items: center;
    gap: 18px;
    margin-bottom: 12px;
}
.history-month {
    color: #8f83c6;
    font-size: 58px;
    font-weight: 950;
    line-height: .9;
    text-shadow: 2px 2px 0 #333;
}
.history-bubble {
    min-height: 88px;
    background: #fff;
    border: 3px solid #333;
    border-radius: 48px;
}
.history-spread {
    display: grid;
    grid-template-columns: 1fr 1.35fr;
    gap: 50px;
}
.history-column {
    display: grid;
    gap: 0;
}
.history-column.left { margin-top: 150px; }
.history-column.right { margin-top: 0; }
.history-card {
    height: 156px;
    display: grid;
    grid-template-columns: 116px 1fr;
    background: #fff;
    border: 2px solid #333;
    overflow: hidden;
    border-radius: 0;
}
.history-card:first-child { border-radius: 8px 8px 0 0; }
.history-card:last-child { border-radius: 0 0 8px 8px; }
.history-card + .history-card { border-top: 0; }
.history-column.right .history-card { height: 117px; }
.history-column.right .history-card .history-summary { height: 42px; }
.history-card.empty {
    opacity: .55;
    background: rgba(255,255,255,.62);
}
.history-date {
    background: #aeb9dc;
    border-right: 2px solid #333;
    padding: 12px;
    color: #2f3450;
    font-weight: 900;
}
.history-body {
    padding: 14px;
    color: #67555d;
    background-image:
        linear-gradient(#e7e7e7 1px, transparent 1px),
        linear-gradient(90deg, #e7e7e7 1px, transparent 1px);
    background-size: 20px 20px;
}
.history-summary {
    height: 58px;
    overflow: hidden;
    line-height: 1.45;
    word-break: break-word;
}
.history-meta { color: #9a626d; font-size: 14px; margin-top: 12px; }
.chat-paper {
    min-height: 620px;
    background: #fffefc;
    border: 3px solid #333;
    border-radius: 8px;
    padding: 86px 28px 100px;
    position: relative;
    background-image:
        linear-gradient(#edf0f2 1px, transparent 1px),
        linear-gradient(90deg, #edf0f2 1px, transparent 1px);
    background-size: 22px 22px;
}
.chat-paper:before {
    content: "⭐  🧦";
    position: absolute;
    left: 38px;
    top: 26px;
    font-size: 44px;
    transform: rotate(-12deg);
    z-index: 0;
}
.chat-paper:after {
    content: "🐴";
    position: absolute;
    right: 54px;
    bottom: 38px;
    font-size: 74px;
    transform: rotate(-5deg);
    z-index: 0;
}
.chat-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #73565c;
    font-weight: 900;
    margin-bottom: 18px;
    position: relative;
    z-index: 1;
}
.msg-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin: 18px 0;
    position: relative;
    z-index: 1;
}
.msg-row.user { justify-content: flex-end; }
.msg-row.assistant { justify-content: flex-start; }
.msg-avatar {
    width: 54px;
    height: 54px;
    background: #fff;
    border: 2px solid #333;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    flex: 0 0 auto;
}
.msg-stack { max-width: 68%; }
.msg-bubble {
    border: 2px solid #333;
    border-radius: 12px;
    padding: 12px 16px;
    color: #4d3f44;
    font-size: 17px;
    line-height: 1.55;
    white-space: pre-wrap;
    word-break: break-word;
    box-shadow: 2px 3px 0 rgba(0,0,0,.08);
}
.msg-row.user .msg-bubble { background: #ffe2e9; }
.msg-row.assistant .msg-bubble { background: #e8f4ff; }
.msg-time { font-size: 13px; color: #79676c; margin-top: 4px; }
.score-pill {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 999px;
    background: #fff;
    border: 2px solid #d09aa8;
    color: #765965;
    margin: 4px;
    font-weight: 800;
}
.stButton > button {
    border-radius: 12px !important;
    border: 2px solid #9a6a73 !important;
    background: #fff !important;
    color: #6a4a52 !important;
    font-weight: 850 !important;
}
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    border: 2px solid #c6949d !important;
    border-radius: 10px !important;
    background: #fffdfc !important;
}
.template-frame {
    width: 100%;
    aspect-ratio: 1178 / 884;
    background-repeat: no-repeat;
    background-position: center top;
    background-size: 100% 100%;
    position: relative;
    margin: 0 auto 14px auto;
}
.template-cover { aspect-ratio: 1178 / 884; }
.template-intro { aspect-ratio: 1048 / 786; }
.template-calendar { aspect-ratio: 1103 / 827; }
.template-history { aspect-ratio: 1093 / 819; }
.template-chat { aspect-ratio: 1101 / 826; }
.template-overlay {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
}
.tpl-text {
    position: absolute;
    color: #2c2528;
    font-size: clamp(12px, 1.45vw, 18px);
    line-height: 1.25;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.tpl-mood {
    position: absolute;
    transform: translate(-50%, -50%);
    font-size: clamp(18px, 3vw, 34px);
}
.tpl-card {
    position: absolute;
    overflow: hidden;
    color: #55484e;
    font-size: clamp(10px, 1.1vw, 14px);
    line-height: 1.35;
}
.tpl-date-chip {
    position: absolute;
    height: 5.2%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.4%;
    background: #aeb8d7;
    color: #333;
    font-size: clamp(11px, 1.35vw, 16px);
    line-height: 1;
    box-sizing: border-box;
}
.tpl-date-chip.sun { color: #d8878e; }
.tpl-msg {
    position: relative;
    max-width: 58%;
    padding: 10px 14px;
    margin: 10px 0;
    border-radius: 12px;
    border: 2px solid #333;
    font-size: clamp(12px, 1.35vw, 16px);
    line-height: 1.45;
    white-space: pre-wrap;
    word-break: break-word;
}
.tpl-chat-list {
    position: absolute;
    left: 8%;
    right: 8%;
    top: 16%;
    bottom: 12%;
    overflow: hidden;
}
.tpl-msg.user {
    margin-left: auto;
    background: #ffe2e9;
}
.tpl-msg.assistant {
    margin-right: auto;
    background: #e8f4ff;
}
.tpl-avatar {
    display: inline-flex;
    width: 34px;
    height: 34px;
    border: 2px solid #333;
    border-radius: 8px;
    background: #fff;
    align-items: center;
    justify-content: center;
    margin: 0 6px;
}
@media (max-width: 850px) {
    .cover-scene, .intro-grid, .history-spread, .calendar-deco, .history-header {
        grid-template-columns: 1fr;
    }
    .calendar-head { flex-direction: column; align-items: stretch; }
    .msg-stack { max-width: 78%; }
    .history-column.left { margin-top: 0; }
    .history-column.right .history-card,
    .history-card { height: 138px; }
}
</style>
"""


def _inject_css() -> None:
    st.markdown(DIARY_CSS, unsafe_allow_html=True)


def _template_path(name: str) -> Optional[Path]:
    filename = TEMPLATE_FILES.get(name)
    if not filename:
        return None
    path = TEMPLATE_DIR / filename
    return path if path.exists() else None


def _template_data_url(name: str) -> Optional[str]:
    path = _template_path(name)
    if not path:
        return None
    suffix = path.suffix.lower()
    mime = "image/png"
    if suffix in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    elif suffix == ".webp":
        mime = "image/webp"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _render_template(name: str, overlays: str = "") -> bool:
    url = _template_data_url(name)
    if not url:
        return False
    st.markdown(
        f"""
        <div class="template-frame template-{name}" style="background-image: url('{url}');">
            <div class="template-overlay">{overlays}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return True


def _template_help() -> None:
    st.info(
        "要完全使用原图且不改变原图字体，请把 5 张模板图放到 "
        "`assets/diary_templates/`，文件名分别为 "
        "`cover.jpg`, `intro.jpg`, `calendar.jpg`, `history.jpg`, `chat.jpg`。"
    )


def _weekday_en(dt: datetime) -> str:
    return ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][dt.weekday()]


def _month_tab() -> str:
    return str(datetime.now().month)


def _tabs(active: str) -> str:
    tabs = ["COVER", "INTRO", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "NOTE", "INFO"]
    html = ['<div class="diary-tabs">']
    for item in tabs:
        klass = "diary-tab"
        if item in ["COVER", "INTRO", "NOTE", "INFO"]:
            klass += " small"
        if str(item) == str(active):
            klass += " active" if item in ["COVER", "INTRO", "NOTE", "INFO"] else " month-active"
        html.append(f'<div class="{klass}">{item}</div>')
    html.append("</div>")
    return "".join(html)


def _open_shell(active: str) -> None:
    st.markdown(f'<div class="diary-shell">{_tabs(active)}<div class="diary-page">', unsafe_allow_html=True)


def _close_shell() -> None:
    st.markdown("</div></div>", unsafe_allow_html=True)


def _back_home_button() -> None:
    if st.button("← 返回功能选择", key="psy_back_home"):
        st.session_state.page = "home"
        st.rerun()


def render_cover() -> None:
    year = datetime.now().year
    if _render_template("cover"):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            if st.button("进入我的心理日记本", use_container_width=True, key="enter_diary_tpl"):
                st.session_state.diary_stage = "INTRO" if not st.session_state.get("diary_profile") else _month_tab()
                st.rerun()
        return

    _template_help()
    _open_shell("COVER")
    st.markdown(
        f"""
        <div class="cover-scene">
            <div>
                <div class="cover-prop">🪴</div>
                <div class="doodle">🐰📖</div>
                <div class="cover-side-note">🍰</div>
            </div>
            <div>
                <div class="big-bubble">
                    <div class="title-year">{year}</div>
                    <div class="title-main">EVERY<br/>HEALING<br/>DIARY</div>
                </div>
                <div class="loading-text">Opening your diary...</div>
            </div>
            <div>
                <div class="doodle">🐻✏️</div>
                <div class="cover-prop">🐱</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _close_shell()
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("进入我的心理日记本", use_container_width=True, key="enter_diary"):
            st.session_state.diary_stage = "INTRO" if not st.session_state.get("diary_profile") else _month_tab()
            st.rerun()


def render_intro() -> None:
    year = datetime.now().year
    profile = st.session_state.get("diary_profile") or {}
    profile_overlays = f"""
        <div class="tpl-text" style="left:57%;top:51%;width:22%;">{escape(profile.get("name", ""))}</div>
        <div class="tpl-text" style="left:57%;top:56%;width:22%;">{escape(profile.get("mbti", ""))}</div>
        <div class="tpl-text" style="left:57%;top:61%;width:22%;">{escape(profile.get("sns", ""))}</div>
        <div class="tpl-text" style="left:61%;top:66%;width:18%;">{escape(profile.get("deco_level", ""))}</div>
        <div class="tpl-text" style="left:62%;top:71%;width:20%;">{escape(profile.get("signature", ""))}</div>
    """
    if _render_template("intro", profile_overlays):
        with st.form("diary_profile_form_tpl"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("NAME", value=profile.get("name", st.session_state.get("user_nickname", "")))
                mbti = st.text_input("MBTI", value=profile.get("mbti", ""), placeholder="可不填")
                sns = st.text_input("SNS @", value=profile.get("sns", ""), placeholder="可不填")
            with c2:
                deco_level = st.selectbox("DECO LEVEL", ["Lv.1", "Lv.2", "Lv.3", "Lv.4"], index=0)
                companion = st.text_input("AI COMPANION", value=profile.get("companion", "Echo"))
                signature = st.text_input("SIGNATURE", value=profile.get("signature", ""), placeholder="写一句给自己的话")
            submitted = st.form_submit_button("START", use_container_width=True)
        if submitted:
            save_profile({
                "name": name.strip() or "日记本主人",
                "mbti": mbti.strip(),
                "sns": sns.strip(),
                "deco_level": deco_level,
                "companion": companion.strip() or "Echo",
                "signature": signature.strip(),
            })
            st.session_state.diary_stage = _month_tab()
            st.rerun()
        return

    _open_shell("INTRO")
    st.markdown(
        f"""
        <div class="intro-grid">
            <div class="intro-title">
                <div class="title-year">{year}</div>
                <div class="title-main">EVERY<br/>HEALING<br/>DIARY</div>
            </div>
            <div>
                <div class="avatar-frame">🐰</div>
                <div class="profile-lines">
                    <div><span>NAME :</span> {escape(profile.get("name", "________"))}</div>
                    <div><span>MBTI :</span> {escape(profile.get("mbti", "________"))}</div>
                    <div><span>SNS :</span> @{escape(profile.get("sns", "________"))}</div>
                    <div><span>DECO LEVEL :</span> {escape(profile.get("deco_level", "Lv.__"))}</div>
                    <div><span>SIGNATURE :</span> {escape(profile.get("signature", "________"))}</div>
                </div>
            </div>
        </div>
        <div class="profile-form-wrap">
        """,
        unsafe_allow_html=True,
    )
    with st.form("diary_profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("NAME", value=profile.get("name", st.session_state.get("user_nickname", "")))
            mbti = st.text_input("MBTI", value=profile.get("mbti", ""), placeholder="可不填")
            sns = st.text_input("SNS @", value=profile.get("sns", ""), placeholder="可不填")
        with c2:
            deco_level = st.selectbox("DECO LEVEL", ["Lv.1", "Lv.2", "Lv.3", "Lv.4"], index=0)
            companion = st.text_input("AI COMPANION", value=profile.get("companion", "Echo"))
            signature = st.text_input("SIGNATURE", value=profile.get("signature", ""), placeholder="写一句给自己的话")
        submitted = st.form_submit_button("START", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    _close_shell()

    if submitted:
        save_profile({
            "name": name.strip() or "日记本主人",
            "mbti": mbti.strip(),
            "sns": sns.strip(),
            "deco_level": deco_level,
            "companion": companion.strip() or "Echo",
            "signature": signature.strip(),
        })
        st.session_state.diary_stage = _month_tab()
        st.rerun()


def render_calendar() -> None:
    today = datetime.now()
    year, month = today.year, today.month
    date_key = today.strftime("%Y-%m-%d")
    moods = st.session_state.get("diary_moods", {}) or {}
    options = ["", "😊", "🙂", "😐", "😕", "😢", "😡", "😴", "🥰", "🌧️", "🌈"]
    labels = ["不填写"] + options[1:]
    current = moods.get(date_key, "")
    current_index = options.index(current) if current in options else 0

    if _template_path("calendar"):
        cal_for_overlay = calendar.Calendar(firstweekday=6)
        weeks_for_overlay = cal_for_overlay.monthdayscalendar(year, month)
        overlay_parts = []
        for row_idx, week in enumerate(weeks_for_overlay):
            for col_idx, day in enumerate(week):
                if day == 0:
                    continue
                key = f"{year}-{month:02d}-{day:02d}"
                emoji = moods.get(key, "")
                if not emoji:
                    continue
                left = 15.6 + col_idx * 11.75 + 5.85
                top = 25.2 + row_idx * 11.55 + 6.0
                overlay_parts.append(
                    f'<div class="tpl-mood" style="left:{left:.2f}%;top:{top:.2f}%;">{escape(emoji)}</div>'
                )
        _render_template("calendar", "".join(overlay_parts))
        clean_options = ["", "😊", "🙂", "😐", "😕", "😢", "😡", "😴", "🥰", "🌧️", "🌈"]
        clean_labels = ["不填写"] + clean_options[1:]
        clean_current_index = clean_options.index(current) if current in clean_options else 0
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            picked_label = st.selectbox("今日心情", clean_labels, index=clean_current_index, key="mood_select_tpl")
            picked = "" if picked_label == "不填写" else picked_label
        with c2:
            if st.button("保存到今天", use_container_width=True, key="save_mood_tpl"):
                save_mood(date_key, picked)
                st.success("已保存。")
                st.rerun()
        with c3:
            st.caption("原图作为底图显示，日期格子的字体和装饰不会被重画。")
        return

    _open_shell(str(month))
    st.markdown(
        f"""
        <div class="calendar-head">
            <div class="month-title">{month}<span style="font-size:42px;margin-left:14px;">{today.strftime("%B").upper()}</span></div>
            <div class="calendar-note">今天是 {today.strftime("%Y.%m.%d")} · {_weekday_en(today)}，可以给今天贴一个心情 emoji，不填也会保留空白。</div>
        </div>
        <div class="calendar-deco">
            <div class="calendar-bear">🐻🎉</div>
            <div class="calendar-cloud"></div>
            <div class="calendar-cat">🐱</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        picked_label = st.selectbox("今日心情", labels, index=current_index, key="mood_select")
        picked = "" if picked_label == "不填写" else picked_label
    with c2:
        if st.button("保存到今天", use_container_width=True, key="save_mood"):
            save_mood(date_key, picked)
            st.success("已保存。")
            st.rerun()
    with c3:
        st.markdown("<div class='tip-box'>每天只保存一个心情 emoji；没填的日期会像原图一样留白。</div>", unsafe_allow_html=True)

    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)
    weekdays = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    html = ['<table class="mood-calendar"><thead><tr>']
    for day_name in weekdays:
        html.append(f"<th>{day_name}</th>")
    html.append("</tr></thead><tbody>")
    for week in weeks:
        html.append("<tr>")
        for day in week:
            if day == 0:
                html.append("<td></td>")
                continue
            key = f"{year}-{month:02d}-{day:02d}"
            emoji = escape(moods.get(key, ""))
            color = "#d07782" if datetime(year, month, day).weekday() == 6 else "#333"
            html.append(f'<td><span style="color:{color}">{day}</span><span class="mood-emoji">{emoji}</span></td>')
        html.append("</tr>")
    html.append("</tbody></table>")
    st.markdown("".join(html), unsafe_allow_html=True)
    _close_shell()


def _history_card(record: Optional[Dict[str, Any]], fallback_dt: datetime) -> str:
    if record:
        raw_time = record.get("updated_at") or record.get("created_at") or ""
        try:
            dt = datetime.fromisoformat(raw_time)
        except Exception:
            dt = fallback_dt
        summary = escape(record.get("summary", ""))
        mood = escape(record.get("mood", "") or "📝")
        meta = dt.strftime("%H:%M")
        body = f"""
            <div style="font-size:28px">{mood}</div>
            <div class="history-summary">{summary}</div>
            <div class="history-meta">{meta}</div>
        """
        empty_class = ""
    else:
        dt = fallback_dt
        body = '<div class="history-summary"></div>'
        empty_class = " empty"

    return f"""
    <div class="history-card{empty_class}">
        <div class="history-date">{_weekday_en(dt)}<br/><span style="font-size:26px">{dt.day}</span></div>
        <div class="history-body">{body}</div>
    </div>
    """


def render_history() -> None:
    records = list_history_records("psytest")
    page_size = 7
    total_pages = max(1, (len(records) + page_size - 1) // page_size)
    page = min(st.session_state.get("diary_history_page", 0), total_pages - 1)
    start = page * page_size
    cells: List[Optional[Dict[str, Any]]] = records[start:start + page_size]
    cells += [None] * (page_size - len(cells))

    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    fallback_dates = [monday + timedelta(days=offset) for offset in range(7)]

    if _template_path("history"):
        slots = [
            (4.0, 32.0, 42.0, 16.0),
            (4.0, 52.8, 42.0, 16.0),
            (4.0, 73.5, 42.0, 16.0),
            (54.0, 10.8, 42.0, 15.0),
            (54.0, 31.2, 42.0, 15.0),
            (54.0, 51.8, 42.0, 15.0),
            (54.0, 72.4, 42.0, 15.0),
        ]
        overlay_parts = []
        date_slots = [
            (4.0, 33.2, 13.6),
            (4.0, 54.2, 13.6),
            (4.0, 75.3, 13.6),
            (52.2, 11.0, 13.6),
            (52.2, 33.1, 13.6),
            (52.2, 55.0, 13.6),
            (52.2, 77.0, 13.6),
        ]
        for idx, dt in enumerate(fallback_dates):
            x, y, w = date_slots[idx]
            sun_class = " sun" if dt.weekday() == 6 else ""
            overlay_parts.append(
                f"""
                <div class="tpl-date-chip{sun_class}" style="left:{x}%;top:{y}%;width:{w}%;">
                    <span>{_weekday_en(dt)}</span><span>{dt.day}</span>
                </div>
                """
            )
        for idx, record in enumerate(cells):
            if not record:
                continue
            x, y, w, h = slots[idx]
            raw_time = record.get("updated_at") or record.get("created_at") or ""
            try:
                dt = datetime.fromisoformat(raw_time)
                meta = dt.strftime("%H:%M")
            except Exception:
                meta = ""
            summary = escape(record.get("summary", ""))
            mood = escape(record.get("mood", "") or "📝")
            overlay_parts.append(
                f"""
                <div class="tpl-card" style="left:{x}%;top:{y}%;width:{w}%;height:{h}%;">
                    <div style="font-size:clamp(16px,2vw,28px);">{mood}</div>
                    <div>{summary}</div>
                    <div style="color:#9a626d;margin-top:4px;">{meta}</div>
                </div>
                """
            )
        _render_template("history", "".join(overlay_parts))

        for row in range(4):
            cols = st.columns(2)
            for col_idx in range(2):
                idx = row * 2 + col_idx
                if idx >= page_size:
                    continue
                record = cells[idx]
                with cols[col_idx]:
                    if record:
                        if st.button("打开这条记录", key=f"open_hist_tpl_{record['id']}", use_container_width=True):
                            st.session_state.selected_history_id = record["id"]
                            st.session_state.diary_stage = "HISTORY_CHAT"
                            st.rerun()
                    else:
                        st.button("空白记录框", key=f"empty_hist_tpl_{page}_{idx}", disabled=True, use_container_width=True)
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("上一页", disabled=page <= 0, use_container_width=True, key="history_prev_tpl"):
                st.session_state.diary_history_page = max(0, page - 1)
                st.rerun()
        with c2:
            st.caption(f"第 {page + 1} / {total_pages} 页 · 共 {len(records)} 条")
        with c3:
            if st.button("下一页", disabled=page >= total_pages - 1, use_container_width=True, key="history_next_tpl"):
                st.session_state.diary_history_page = min(total_pages - 1, page + 1)
                st.rerun()
        return

    _open_shell("INFO")
    st.markdown(
        f"""
        <div class="history-header">
            <div class="history-month">{today.month}<br/><span style="font-size:18px;text-shadow:none;color:#333;">{today.year}<br/>{today.strftime("%b").upper()}</span></div>
            <div class="history-bubble"></div>
        </div>
        <div class="history-title">HISTORY RECORDS</div>
        """,
        unsafe_allow_html=True,
    )
    left_cards = "".join(_history_card(cells[i], fallback_dates[i]) for i in range(3))
    right_cards = "".join(_history_card(cells[i], fallback_dates[i]) for i in range(3, 7))
    st.markdown(
        f"""
        <div class="history-spread">
            <div class="history-column left">{left_cards}</div>
            <div class="history-column right">{right_cards}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _close_shell()

    for row in range(4):
        cols = st.columns(2)
        for col_idx in range(2):
            idx = row * 2 + col_idx
            if idx >= page_size:
                continue
            record = cells[idx]
            with cols[col_idx]:
                if record:
                    if st.button("打开这条记录", key=f"open_hist_{record['id']}", use_container_width=True):
                        st.session_state.selected_history_id = record["id"]
                        st.session_state.diary_stage = "HISTORY_CHAT"
                        st.rerun()
                else:
                    st.button("空白记录框", key=f"empty_hist_{page}_{idx}", disabled=True, use_container_width=True)

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("上一页", disabled=page <= 0, use_container_width=True, key="history_prev"):
            st.session_state.diary_history_page = max(0, page - 1)
            st.rerun()
    with c2:
        st.markdown(f"<div class='tip-box' style='text-align:center'>第 {page + 1} / {total_pages} 页 · 共 {len(records)} 条</div>", unsafe_allow_html=True)
    with c3:
        if st.button("下一页", disabled=page >= total_pages - 1, use_container_width=True, key="history_next"):
            st.session_state.diary_history_page = min(total_pages - 1, page + 1)
            st.rerun()


def _message_html(msg: Dict[str, Any], user_avatar: str = "🐰", ai_avatar: str = "🐻") -> str:
    role = msg.get("role", "assistant")
    content = escape(str(msg.get("content", ""))).replace("\n", "<br/>")
    t = message_time(msg)
    if role == "user":
        return f"""
        <div class="msg-row user">
            <div class="msg-stack"><div class="msg-bubble">{content}</div><div class="msg-time" style="text-align:right">{escape(t)}</div></div>
            <div class="msg-avatar">{user_avatar}</div>
        </div>
        """
    return f"""
    <div class="msg-row assistant">
        <div class="msg-avatar">{ai_avatar}</div>
        <div class="msg-stack"><div class="msg-bubble">{content}</div><div class="msg-time">{escape(t)}</div></div>
    </div>
    """


def _chat_paper(messages: List[Dict[str, Any]], title: str) -> None:
    now = datetime.now()
    date_text = message_date(messages[0]) if messages else now.strftime("%Y.%m.%d")
    if _template_path("chat"):
        parts = [
            f'<div class="tpl-text" style="left:8%;top:9%;width:42%;">{escape(date_text)} · {_weekday_en(now)} · {now.strftime("%H:%M")}</div>',
            '<div class="tpl-chat-list">',
        ]
        visible_messages = [m for m in messages if m.get("role") in ("user", "assistant")][-8:]
        for msg in visible_messages:
            role = msg.get("role", "assistant")
            content = escape(str(msg.get("content", ""))).replace("\n", "<br/>")
            if role == "user":
                parts.append(f'<div class="tpl-msg user">{content}</div>')
            else:
                parts.append(f'<div class="tpl-msg assistant"><span class="tpl-avatar">🐻</span>{content}</div>')
        parts.append("</div>")
        _render_template("chat", "".join(parts))
        return

    html = [
        '<div class="chat-paper">',
        f'<div class="chat-top"><div>{escape(date_text)} · {_weekday_en(now)} · {now.strftime("%H:%M")}</div><div>{escape(title)}</div></div>',
    ]
    for msg in messages:
        html.append(_message_html(msg))
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_live_chat() -> None:
    profile = st.session_state.get("diary_profile") or {}
    companion = profile.get("companion", "Echo")
    messages = st.session_state.get("psy_messages", [])

    _open_shell("NOTE")
    _chat_paper(messages, f"{companion} is listening")
    scores = st.session_state.get("psy_scores") or score_messages(messages)
    score_html = "".join(f'<span class="score-pill">{name}: {scores.get(key, 5)}/10</span>' for key, name in DIMENSIONS.items())
    st.markdown(f"<div>{score_html}</div>", unsafe_allow_html=True)
    if st.session_state.get("show_psy_report"):
        st.markdown(make_report(scores, messages), unsafe_allow_html=True)
    _close_shell()

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("生成/查看报告", use_container_width=True, key="show_report"):
            st.session_state.show_psy_report = not st.session_state.get("show_psy_report", False)
            st.rerun()
    with c2:
        if st.button("历史记录", use_container_width=True, key="go_history_from_chat"):
            st.session_state.diary_stage = "INFO"
            st.rerun()
    with c3:
        if st.button("重新开始一次评测", use_container_width=True, key="reset_psy_chat"):
            st.session_state.psy_messages = [make_message("assistant", "新的日记页打开了。今天先从哪里说起？")]
            st.session_state.psy_scores = {}
            st.session_state.psy_record_id = None
            st.session_state.show_psy_report = False
            st.rerun()

    prompt = st.chat_input("写在今天的日记里...", key="psy_chat_input")
    if prompt:
        messages.append(make_message("user", prompt))
        scores = score_messages(messages)
        reply = generate_reply("psytest", prompt, messages, scores)
        messages.append(make_message("assistant", reply))
        record_id = save_history_record("psytest", messages, scores, st.session_state.get("psy_record_id"), mood="")
        st.session_state.psy_record_id = record_id
        st.session_state.psy_messages = messages
        st.session_state.psy_scores = scores
        st.rerun()


def render_history_chat() -> None:
    record_id = st.session_state.get("selected_history_id")
    record = load_history_record(record_id) if record_id else None
    if not record:
        st.warning("这条历史记录没有找到。")
        if st.button("返回历史记录"):
            st.session_state.selected_history_id = None
            st.session_state.diary_stage = "INFO"
            st.rerun()
        return

    messages = record.get("messages") or record.get("display_messages") or []
    _open_shell("NOTE")
    _chat_paper(messages, "History Chat")
    _close_shell()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("返回历史记录", use_container_width=True, key="back_history_list"):
            st.session_state.selected_history_id = None
            st.session_state.diary_stage = "INFO"
            st.rerun()
    with c2:
        if st.button("把这条记录接着聊", use_container_width=True, key="continue_history"):
            st.session_state.psy_messages = messages
            st.session_state.psy_scores = record.get("scores", {})
            st.session_state.psy_record_id = record_id
            st.session_state.selected_history_id = None
            st.session_state.diary_stage = "NOTE"
            st.rerun()

    prompt = st.chat_input("继续追问或补充这条历史记录...", key="history_chat_input")
    if prompt:
        messages.append(make_message("user", prompt))
        scores = score_messages(messages)
        messages.append(make_message("assistant", generate_reply("psytest", prompt, messages, scores)))
        update_history_messages(record_id, messages, scores)
        st.rerun()


def render_nav() -> None:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("心情日历", use_container_width=True, key="nav_calendar"):
            st.session_state.diary_stage = _month_tab()
            st.rerun()
    with c2:
        if st.button("双人聊天", use_container_width=True, key="nav_chat"):
            st.session_state.diary_stage = "NOTE"
            st.rerun()
    with c3:
        if st.button("历史记录", use_container_width=True, key="nav_history"):
            st.session_state.diary_stage = "INFO"
            st.rerun()
    with c4:
        _back_home_button()


def render_psytest_diary() -> None:
    _inject_css()
    stage = st.session_state.get("diary_stage", "cover")

    if stage == "cover":
        render_cover()
        return
    if stage == "INTRO" or not st.session_state.get("diary_profile"):
        render_intro()
        _back_home_button()
        return
    if stage == "INFO":
        render_history()
    elif stage == "HISTORY_CHAT":
        render_history_chat()
    elif stage == "NOTE":
        render_live_chat()
    else:
        render_calendar()

    if stage != "HISTORY_CHAT":
        render_nav()
