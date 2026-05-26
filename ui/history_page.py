"""
历史记录详情展示页面
展示单次历史对话的完整记录：聊天内容、六维评分、雷达图、趋势图、AI 建议。
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from Multimodal.config import DIMENSIONS, DIMENSION_KEYS
from services.storage_local import load_session, get_all_trend_data
from utils.visualization import draw_radar_chart, configure_chinese_font
from utils.status_assets import get_status_assets


def render_history_detail_page(session_id):
    """
    渲染历史记录详情页

    Args:
        session_id: str, 会话 ID
    """
    data = load_session(session_id)
    if data is None:
        st.markdown(
            '<div style="text-align: center; padding: 2rem; color: #9ab0c8;">'
            '记录未找到</div>',
            unsafe_allow_html=True
        )
        return

    configure_chinese_font()

    # ---- 头部信息 ----
    timestamp = data.get("timestamp", "")
    level_name = data.get("level_name", "未知")
    icon = data.get("icon", "📝")
    composite_score = data.get("composite_score", 0)
    scores = data.get("scores", {})
    summary = data.get("summary", "")

    try:
        dt = datetime.fromisoformat(timestamp)
        display_time = dt.strftime("%Y 年 %m 月 %d 日  %H:%M")
    except:
        display_time = timestamp

    # ---- 返回按钮 ----
    col_back, _ = st.columns([1, 4])
    with col_back:
        st.markdown(
            '<div style="margin-bottom: 0.5rem;">',
            unsafe_allow_html=True
        )
        if st.button("←  返回历史列表", use_container_width=True):
            st.session_state.viewing_history = False
            st.session_state.selected_session = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- 标题 ----
    st.markdown(
        f'<div style="text-align: center; margin: 0.3rem 0 0.5rem 0;">'
        f'<span style="font-size: 1.1rem; color: #4a6a8a; font-weight: 350;">'
        f'📖 {display_time}</span></div>',
        unsafe_allow_html=True
    )

    if summary:
        st.markdown(
            f'<div style="text-align: center; margin-bottom: 1.2rem;">'
            f'<span style="font-size: 0.9rem; color: #8aabca; font-weight: 300; '
            f'background: rgba(100, 181, 246, 0.06); padding: 0.2rem 1rem; '
            f'border-radius: 16px;">{summary}</span></div>',
            unsafe_allow_html=True
        )

    # ============ 第一部分：历史聊天记录 ============
    st.markdown(
        '<div style="font-size: 0.95rem; color: #4a6a8a; font-weight: 350; '
        'margin-bottom: 0.5rem;">💬 对话记录</div>',
        unsafe_allow_html=True
    )

    display_messages = data.get("display_messages", [])
    with st.container():
        st.markdown(
            '<div class="glass-card" style="padding: 1rem 1.2rem; max-height: 400px; '
            'overflow-y: auto;">',
            unsafe_allow_html=True
        )
        for msg in display_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            with st.chat_message(role):
                st.markdown(
                    f'<div class="chat-message-content">{content}</div>',
                    unsafe_allow_html=True
                )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr>', unsafe_allow_html=True)

    # ============ 第二部分：六维分析 + 趋势图 双列 ============
    col_left, col_right = st.columns([1, 1], gap="large")

    # 当前记录的六维评分值
    current_vals = [scores.get(k, 5) for k in DIMENSION_KEYS]
    current_vals = [v if v is not None else 5 for v in current_vals]
    _, _, theme_color, _ = get_status_assets(composite_score, current_vals)

    with col_left:
        # --- 综合评分卡片 ---
        st.markdown(
            f'<div class="glass-card" style="text-align: center; padding: 1rem; margin-bottom: 1rem;">'
            f'<div style="font-size: 2.5rem; line-height: 1;">{icon}</div>'
            f'<div style="font-size: 1.8rem; font-weight: 300; color: #3a5a7a;">{composite_score}</div>'
            f'<div style="font-size: 0.8rem; color: #8aabca; font-weight: 300;">综合身心指数</div>'
            f'<div style="margin-top: 0.3rem;">'
            f'<span style="display: inline-block; padding: 0.15rem 0.8rem; border-radius: 16px; '
            f'font-size: 0.82rem; background: rgba(100, 181, 246, 0.06); color: {theme_color};">'
            f'{level_name}</span></div></div>',
            unsafe_allow_html=True
        )

        # --- 六维雷达图 ---
        st.markdown(
            '<div style="font-size: 0.9rem; color: #4a6a8a; font-weight: 350; '
            'margin-bottom: 0.3rem;">🕸️ 六维评分</div>',
            unsafe_allow_html=True
        )
        fig = draw_radar_chart(current_vals, list(DIMENSIONS.values()), theme_color, figsize=(4.5, 4.5))
        st.pyplot(fig)

        # 维度数值标签
        labels_html = "".join(
            f'<span class="emotion-tag">{name}: {current_vals[i]}</span> '
            for i, name in enumerate(DIMENSIONS.values())
        )
        st.markdown(
            f'<div style="text-align: center; padding: 0.2rem 0;">{labels_html}</div>',
            unsafe_allow_html=True
        )

    with col_right:
        # --- 趋势图（截止至当前位置） ---
        st.markdown(
            '<div style="font-size: 0.9rem; color: #4a6a8a; font-weight: 350; '
            'margin-bottom: 0.3rem;">📈 总分趋势</div>',
            unsafe_allow_html=True
        )

        all_trends = get_all_trend_data()
        # 找到当前记录在趋势中的位置
        cutoff_index = -1
        for i, t in enumerate(all_trends):
            if t["session_id"] == session_id:
                cutoff_index = i
                break

        if cutoff_index >= 0:
            # 只显示到当前记录为止的数据
            trend_until_now = all_trends[:cutoff_index + 1]
        else:
            trend_until_now = all_trends

        if trend_until_now:
            df_data = []
            for t in trend_until_now:
                df_data.append({
                    "会话时间": t["display_label"],
                    "score": t["score"],
                })
            df = pd.DataFrame(df_data)
            # 用 display_label 做横轴确保顺序
            st.line_chart(
                df.set_index("会话时间"),
                color="#64b5f6",
                use_container_width=True,
                height=200
            )
            st.markdown(
                f'<div style="text-align: center; font-size: 0.75rem; color: #9ab0c8; '
                f'font-weight: 300;">共 {len(trend_until_now)} 次对话记录</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="text-align: center; padding: 2rem; color: #9ab0c8; '
                'font-weight: 300;">暂无趋势数据</div>',
                unsafe_allow_html=True
            )

        # --- AI 建议 ---
        st.markdown(
            '<div style="margin-top: 1rem; font-size: 0.9rem; color: #4a6a8a; font-weight: 350; '
            'margin-bottom: 0.3rem;">📝 AI 建议</div>',
            unsafe_allow_html=True
        )

        ai_suggestion = data.get("ai_suggestion", "")
        if ai_suggestion:
            st.markdown(
                f'<div class="glass-card" style="padding: 1rem; font-size: 0.88rem; '
                f'line-height: 1.7; color: #4a5a6a;">{ai_suggestion}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="text-align: center; padding: 1rem; color: #9ab0c8; '
                'font-weight: 300;">暂无建议记录</div>',
                unsafe_allow_html=True
            )

    st.markdown('<hr>', unsafe_allow_html=True)
