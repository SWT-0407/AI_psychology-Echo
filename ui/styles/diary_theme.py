"""
日记本风格 UI 主题
用于 AI 树洞：加载页 / 档案页 / 心情日历 / 历史记录 / 双人聊天页
"""

import streamlit as st


DIARY_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Nunito:wght@600;800&display=swap');

:root {
    --diary-pink: #f9d9df;
    --diary-deep-pink: #ef9fb0;
    --diary-blue: #aeb9dc;
    --diary-green: #86b99d;
    --diary-purple: #b59bcf;
    --diary-line: #333333;
    --diary-gray: #cbd1db;
    --diary-paper: #fffdfb;
    --diary-user: #ffe4ea;
    --diary-ai: #e7f3ff;
}

html, body, [data-testid="stAppViewContainer"] {
    background: #f9d9df !important;
}

[data-testid="stHeader"] {
    background: rgba(249,217,223,0.85) !important;
}

.block-container {
    padding-top: 1rem !important;
    max-width: 1180px !important;
}

#MainMenu, footer {
    visibility: hidden;
}

.diary-shell {
    width: 100%;
    border: 3px solid #929292;
    background: var(--diary-pink);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 12px 30px rgba(120, 80, 90, 0.16);
    font-family: 'Gaegu', 'Nunito', sans-serif;
}

.diary-tabs {
    height: 52px;
    background: #d5dce6;
    display: flex;
    align-items: end;
    gap: 2px;
    padding: 0 14px;
    border-bottom: 3px solid #8e8e8e;
    overflow-x: auto;
}

.diary-tab {
    min-width: 58px;
    height: 40px;
    background: #ffffff;
    border: 3px solid #8e8e8e;
    border-bottom: none;
    border-radius: 14px 14px 0 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Nunito', sans-serif;
    font-weight: 800;
    color: #888;
    font-size: 15px;
}

.diary-tab.small {
    min-width: 70px;
    font-size: 13px;
}

.diary-tab.active {
    background: #aebee0;
    color: #fff;
}

.diary-tab.month-active {
    background: #f1c8d2;
    color: #6a6a6a;
}

.diary-page {
    min-height: 670px;
    padding: 30px 36px;
    position: relative;
    background: #f9d9df;
}

.cover-scene {
    min-height: 620px;
    position: relative;
    display: grid;
    grid-template-columns: 1fr 1.25fr 1fr;
    align-items: center;
    gap: 16px;
}

.big-bubble {
    background: #fff;
    border: 3px solid #333;
    border-radius: 50%;
    min-height: 290px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    position: relative;
}

.big-bubble::after {
    content: '';
    width: 52px;
    height: 62px;
    background: #fff;
    border-right: 3px solid #333;
    border-bottom: 3px solid #333;
    transform: rotate(25deg);
    position: absolute;
    right: 50px;
    bottom: -34px;
}

.title-year {
    color: var(--diary-purple);
    font-size: 58px;
    font-family: 'Nunito', sans-serif;
    font-weight: 800;
    letter-spacing: 6px;
    text-shadow: 2px 2px 0 #333;
    line-height: 1;
}

.title-main {
    color: var(--diary-green);
    font-size: 54px;
    font-family: 'Nunito', sans-serif;
    font-weight: 800;
    letter-spacing: 3px;
    text-shadow: 2px 2px 0 #333;
    line-height: 1.05;
}

.loading-text {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 32px;
    text-align: center;
    font-size: 24px;
    color: #6b4b55;
    animation: pulse 1.2s infinite ease-in-out;
}

@keyframes pulse {
    0%, 100% { opacity: .45; transform: translateY(0); }
    50% { opacity: 1; transform: translateY(-3px); }
}

.doodle {
    font-size: 90px;
    text-align: center;
    filter: drop-shadow(2px 4px 0 rgba(0,0,0,.08));
}

.doodle-stack {
    display: flex;
    flex-direction: column;
    gap: 28px;
    align-items: center;
}

.intro-grid {
    min-height: 620px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    align-items: center;
    gap: 32px;
}

.intro-title {
    text-align: center;
}

.profile-card {
    width: 100%;
    max-width: 390px;
    margin: 0 auto;
}

.avatar-frame {
    width: 145px;
    height: 145px;
    border: 3px solid #333;
    background: #fff;
    margin: 0 auto 18px auto;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 86px;
}

.profile-line {
    display: grid;
    grid-template-columns: 105px 1fr;
    align-items: center;
    gap: 8px;
    margin: 8px 0;
    font-size: 23px;
    font-weight: 700;
}

.stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
    border: 2px solid #b7838d !important;
    border-radius: 8px !important;
    background: #fffaf9 !important;
    min-height: 38px !important;
}

.stButton > button {
    border: 2px solid #9b6c74 !important;
    background: #f3a1ae !important;
    color: #fff !important;
    border-radius: 12px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 800 !important;
    box-shadow: 2px 3px 0 rgba(0,0,0,.18) !important;
}

.calendar-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}

.month-title {
    color: #8c80c2;
    font-size: 58px;
    font-family: 'Nunito', sans-serif;
    font-weight: 800;
    letter-spacing: 3px;
    text-shadow: 2px 2px 0 #333;
}

.calendar-note {
    min-width: 360px;
    height: 62px;
    border: 3px solid #333;
    background: white;
    border-radius: 24px;
    padding: 12px 22px;
    font-size: 22px;
}

.mood-calendar {
    width: 100%;
    border-collapse: collapse;
    background: #fff;
    border: 3px solid #333;
    table-layout: fixed;
}

.mood-calendar th {
    background: #aeb9dc;
    color: #7f4150;
    border: 2px solid #333;
    height: 34px;
    font-family: 'Nunito', sans-serif;
}

.mood-calendar td {
    border: 2px solid #333;
    height: 92px;
    vertical-align: top;
    padding: 6px;
    font-size: 18px;
    position: relative;
}

.mood-calendar .muted {
    color: #cfcfcf;
}

.mood-emoji {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -38%);
    font-size: 36px;
}

.history-title {
    font-family: 'Nunito', sans-serif;
    font-weight: 800;
    color: #8d747b;
    font-size: 30px;
    margin-bottom: 22px;
}

.history-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 18px;
}

.history-card {
    height: 142px;
    background: rgba(255,255,255,.78);
    border: 2px solid #d0aaa9;
    border-radius: 8px;
    text-align: center;
    padding: 12px 8px;
    overflow: hidden;
}

.history-card.empty {
    border: 2px dashed #d6aaa9;
    background: rgba(255,255,255,.28);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 34px;
    color: #b78b8b;
}

.history-date {
    font-family: 'Nunito', sans-serif;
    font-weight: 800;
    color: #315280;
    font-size: 18px;
    line-height: 1.15;
}

.history-emoji {
    font-size: 30px;
    margin: 10px 0 4px;
}

.history-summary {
    color: #7e6067;
    font-size: 15px;
    line-height: 1.1;
    height: 33px;
    overflow: hidden;
}

.history-time {
    color: #9c5d67;
    font-size: 14px;
}

.chat-paper {
    min-height: 640px;
    background: #fffefc;
    border: 3px solid #333;
    border-radius: 8px;
    padding: 24px 28px;
    position: relative;
    background-image:
        linear-gradient(#edf0f2 1px, transparent 1px),
        linear-gradient(90deg, #edf0f2 1px, transparent 1px);
    background-size: 22px 22px;
}

.chat-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
    font-family: 'Nunito', sans-serif;
    color: #73565c;
    font-weight: 800;
}

.chat-date {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 18px;
}

.chat-scroll {
    padding-bottom: 120px;
}

.msg-row {
    display: flex;
    align-items: flex-start;
    margin: 18px 0;
    gap: 10px;
}

.msg-row.user {
    justify-content: flex-start;
}

.msg-row.assistant {
    justify-content: flex-end;
}

.msg-avatar {
    width: 58px;
    height: 58px;
    background: #fff;
    border: 2px solid #333;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 34px;
    flex: 0 0 auto;
}

.msg-bubble {
    max-width: 64%;
    border: 2px solid #333;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 21px;
    line-height: 1.35;
    color: #4d3f44;
    box-shadow: 2px 3px 0 rgba(0,0,0,.08);
    white-space: pre-wrap;
    word-break: break-word;
}

.msg-row.user .msg-bubble {
    background: var(--diary-user);
}

.msg-row.assistant .msg-bubble {
    background: var(--diary-ai);
}

.msg-time {
    font-size: 14px;
    color: #6f6266;
    margin-top: 4px;
    font-family: 'Nunito', sans-serif;
}

.chat-doodle-left {
    position: absolute;
    left: 22px;
    bottom: 18px;
    font-size: 52px;
}

.chat-doodle-right {
    position: absolute;
    right: 32px;
    bottom: 18px;
    font-size: 58px;
}

.page-actions {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 18px;
    margin-top: 18px;
    font-family: 'Nunito', sans-serif;
    color: #8a666e;
}

.tip-box {
    background: rgba(255,255,255,.56);
    border: 2px dashed #d29ba8;
    border-radius: 12px;
    padding: 12px 16px;
    color: #785e66;
    font-size: 20px;
    margin: 12px 0;
}

/* 隐藏 Streamlit chat 默认样式，让输入框更贴近日记 */
[data-testid="stChatInput"] {
    border: 2px solid #c18b98 !important;
    border-radius: 16px !important;
    background: #fffaf9 !important;
}

@media (max-width: 850px) {
    .cover-scene, .intro-grid {
        grid-template-columns: 1fr;
    }
    .history-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    .msg-bubble {
        max-width: 78%;
    }
    .diary-tab {
        min-width: 48px;
    }
}
</style>
"""


def inject_diary_css():
    st.markdown(DIARY_CSS, unsafe_allow_html=True)


def diary_tabs(active="COVER"):
    tabs = ["COVER", "INTRO", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "NOTE", "INFO"]
    html = ['<div class="diary-tabs">']
    for t in tabs:
        klass = "diary-tab"
        if t in ["COVER", "INTRO", "NOTE", "INFO"]:
            klass += " small"
        if str(t) == str(active):
            klass += " active" if t in ["COVER", "INTRO", "NOTE", "INFO"] else " month-active"
        html.append(f'<div class="{klass}">{t}</div>')
    html.append('</div>')
    return "".join(html)


def open_diary_shell(active="COVER"):
    st.markdown(f'<div class="diary-shell">{diary_tabs(active)}<div class="diary-page">', unsafe_allow_html=True)


def close_diary_shell():
    st.markdown('</div></div>', unsafe_allow_html=True)
