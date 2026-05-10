"""
日记模式页面
第一阶段：用户以日记方式记录今日状态，触发 AI 初步分析。
"""
import streamlit as st
from datetime import datetime


def render_diary_page():
    """
    渲染日记本封面 UI
    显示日期、天气、文本框，供用户撰写今日随笔。
    用户提交日记内容后，写入 session_state 并触发后续处理。

    Returns:
        str or None: 用户输入的日记内容（点击提交后），否则为 None
    """
    st.title("📓 我的心理日记本")

    with st.container(border=True):
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            today = datetime.now()
            week_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            st.subheader(f"{today.strftime('%Y-%m-%d')} {week_map[today.weekday()]}")
        with col_t2:
            st.subheader("☀️ 天气：晴")

    st.write("---")
    st.info("📖 **今日随笔**：请先像写日记一样，记录下你今天发生的事情、感受或身体状态。我会基于此进行初步分析。")

    diary_content = st.text_area(
        "在此处开始撰写你的日记...",
        height=350,
        placeholder="今天过得怎么样？发生了什么特别的事吗？"
    )

    if st.button("写好了，合上日记本"):
        if diary_content.strip():
            return diary_content
        else:
            st.warning("日记还没写呢~")

    return None
