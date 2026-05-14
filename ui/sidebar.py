
"""
侧边栏组件模块
包含疗愈风格的导航：开始聊天、历史记录（可展开子栏）、设置（可展开子栏）。
"""
import streamlit as st
from config import DIMENSIONS
from services.storage_local import get_session_summaries


def _render_history_sublist():
    """
    渲染『历史记录』的子栏列表
    按时间从旧到新排列，点击加载对应记录。
    无记录时显示「无」。
    """
    summaries = get_session_summaries()

    if not summaries:
        st.markdown(
            '<div style="padding: 0.3rem 0.8rem 0.8rem 2rem; color: #9ab0c8; '
            'font-size: 0.82rem; font-weight: 300; font-style: italic;">无</div>',
            unsafe_allow_html=True
        )
        return

    for sess in summaries:
        sid = sess["session_id"]
        display = sess["display_date"]
        score = sess.get("score")

        if st.button(
            f"📄 {display}",
            key=f"hist_{sid}",
            use_container_width=True,
        ):
            st.session_state.viewing_history = True
            st.session_state.selected_session = sid
            st.rerun()


def render_sidebar():
    """
    渲染侧边栏 UI 组件（疗愈风格导航）
    包括：品牌标识、导航菜单（开始聊天/历史记录/设置）、实时评分追踪、重置按钮。
    """
    with st.sidebar:
        # ---- 品牌区 ----
        st.markdown(
            '<div style="padding: 0.5rem 0 1rem 0;">'
            '<span style="font-size: 1.5rem; line-height: 1;">🌱</span>'
            '<span style="font-size: 1rem; font-weight: 350; color: #4a6a8a; '
            'margin-left: 8px; letter-spacing: 0.04em;">心聆 · Echo</span>'
            '</div>',
            unsafe_allow_html=True
        )

        # ---- 导航菜单 ----
        st.markdown(
            '<div style="font-size: 0.75rem; color: #9ab0c8; font-weight: 300; '
            'letter-spacing: 0.08em; padding: 0.3rem 0.8rem; margin-bottom: 0.3rem;">'
            '导 航</div>',
            unsafe_allow_html=True
        )

        # ===== 【开始聊天】 =====
        if st.button(
            "💬  开始聊天",
            use_container_width=True,
            key="sidebar_start_chat"
        ):
            # 重置到初始状态，进入日记模式
            st.session_state.viewing_history = False
            st.session_state.selected_session = None
            st.session_state.is_completed = False
            st.rerun()

        # ===== 【历史记录】 =====
        if st.button(
            "📂  历史记录",
            use_container_width=True,
            key="sidebar_history_btn"
        ):
            # 切换展开/收起状态
            current = st.session_state.get("show_history", False)
            st.session_state.show_history = not current
            if current:
                # 收起时清除查看状态
                st.session_state.viewing_history = False
                st.session_state.selected_session = None
            st.rerun()

        # 展开历史记录子栏
        if st.session_state.get("show_history", False):
            _render_history_sublist()

        # ===== 【设置】 =====
        if st.button(
            "⚙️  设置",
            use_container_width=True,
            key="sidebar_settings_btn"
        ):
            current = st.session_state.get("show_settings", False)
            st.session_state.show_settings = not current
            st.rerun()

        # 展开设置子栏（暂时留空）
        if st.session_state.get("show_settings", False):
            st.markdown(
                '<div style="padding: 0.3rem 0.8rem 0.8rem 2rem; color: #9ab0c8; '
                'font-size: 0.82rem; font-weight: 300; font-style: italic;">'
                '设置功能开发中...</div>',
                unsafe_allow_html=True
            )

        st.markdown('<hr>', unsafe_allow_html=True)

        # ---- 实时状态追踪 ----
        st.markdown(
            '<div style="font-size: 0.75rem; color: #9ab0c8; font-weight: 300; '
            'letter-spacing: 0.08em; padding: 0.3rem 0.8rem; margin-bottom: 0.5rem;">'
            '状 态 追 踪</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="font-size: 0.78rem; color: #8aabca; font-weight: 300; '
            'padding: 0 0.8rem 0.5rem 0.8rem;">'
            '0 表示需关注 · 10 表示非常健康</div>',
            unsafe_allow_html=True
        )

        for key, name in DIMENSIONS.items():
            score = st.session_state.scores[key]
            if score is None:
                st.markdown(
                    f'<div style="display: flex; justify-content: space-between; '
                    f'align-items: center; padding: 0.2rem 0.8rem;">'
                    f'<span style="color: #8aabca; font-size: 0.82rem; font-weight: 300;">{name}</span>'
                    f'<span style="color: #b0c8e0; font-size: 0.78rem; font-weight: 300;">待评估</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                pct = score / 10.0
                st.markdown(
                    f'<div style="display: flex; justify-content: space-between; '
                    f'align-items: center; padding: 0.15rem 0.8rem;">'
                    f'<span style="color: #4a6a8a; font-size: 0.82rem; font-weight: 350;">{name}</span>'
                    f'<span style="color: #4a6a8a; font-size: 0.82rem; font-weight: 350;">{score}/10</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.progress(pct)

        # ---- 完成状态提示 ----
        if st.session_state.is_completed:
            st.markdown(
                '<div style="text-align: center; padding: 0.5rem; '
                'color: #8aabca; font-size: 0.85rem; font-weight: 300;">'
                '✅ 报告已生成，可随时重置</div>',
                unsafe_allow_html=True
            )

        # ---- 云端存储授权 ----
        if not st.session_state.is_completed:
            st.markdown('<hr>', unsafe_allow_html=True)
            from services.storage_cloud import request_user_consent
            consent = request_user_consent()
            if consent:
                st.session_state.cloud_consent = True

        st.markdown('<hr>', unsafe_allow_html=True)

        # ---- 操作区 ----
        st.markdown(
            '<div style="font-size: 0.75rem; color: #9ab0c8; font-weight: 300; '
            'letter-spacing: 0.08em; padding: 0.3rem 0.8rem; margin-bottom: 0.3rem;">'
            '操 作</div>',
            unsafe_allow_html=True
        )

        # API 状态
        st.markdown(
            '<div style="display: flex; align-items: center; gap: 6px; padding: 0.3rem 0.8rem;">'
            '<span style="color: #a5d6a7; font-size: 0.6rem;">●</span>'
            '<span style="color: #8aabca; font-size: 0.82rem; font-weight: 300;">API 已就绪</span>'
            '</div>',
            unsafe_allow_html=True
        )

        if st.button("🔄  重置", use_container_width=True):
            st.session_state.clear()
            st.rerun()
