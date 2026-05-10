"""
日记模式页面
第一阶段：用户以日记方式记录今日状态，触发 AI 初步分析。
"""
import streamlit as st
from datetime import datetime


def render_diary_page():
    """
    渲染日记本封面 UI（疗愈风格）
    显示日期、柔和标题、大文本框，供用户撰写今日随笔。
    Returns:
        str or None: 用户输入的日记内容（点击提交后），否则为 None
    """
    # ----- 首页标题区（仅首轮对话显示） -----
    from styles.theme import render_logo, render_hero
    render_logo()
    render_hero()

    # ----- 日记卡片 -----
    st.markdown(
        '<div class="glass-card" style="padding: 2rem;">',
        unsafe_allow_html=True
    )

    # 日期与问候
    today = datetime.now()
    week_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = week_map[today.weekday()]

    greetings = [
        "今天过得怎么样？",
        "想坐下来聊聊吗？",
        "我在这里，慢慢说。",
        "今天的你，还好吗？",
        "树洞正在听哦。"
    ]
    greeting = greetings[today.day % len(greetings)]

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f'<div class="diary-date">{today.strftime("%Y 年 %m 月 %d 日")} {weekday}</div>',
            unsafe_allow_html=True
        )
        st.markdown(f"**{greeting}**", unsafe_allow_html=True)
    with col2:
        st.markdown(
            '<div style="text-align: right; font-size: 2.5rem; line-height: 1; opacity: 0.7;">📖</div>',
            unsafe_allow_html=True
        )

    st.markdown('<hr style="margin: 1rem 0;">', unsafe_allow_html=True)

    # 引导文字
    st.markdown(
        '<p style="color: #7a9aba; font-weight: 300; font-size: 0.92rem;">'
        '像写日记一样，记录今天发生的事、你的感受、身体状态……<br>'
        '不用在意措辞，想到什么就写什么吧。</p>',
        unsafe_allow_html=True
    )

    # 日记输入区域
    diary_content = st.text_area(
        label="",
        height=280,
        placeholder="今天有什么想和我分享的吗？\n比如：遇到了什么事？心情怎么样？身体有什么感觉？……",
        label_visibility="collapsed"
    )

    # 提交按钮
    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
        submit_clicked = st.button(
            "🌱  写好了，轻轻合上日记本",
            use_container_width=True,
            type="secondary"
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # 处理提交
    if submit_clicked:
        if diary_content and diary_content.strip():
            return diary_content.strip()
        else:
            st.markdown(
                '<div style="text-align: center; padding: 0.5rem; color: #a0b8d0; font-size: 0.85rem; font-weight: 300;">'
                '📝 日记还没写呢～ 随便写点什么都可以。</div>',
                unsafe_allow_html=True
            )
    return None
