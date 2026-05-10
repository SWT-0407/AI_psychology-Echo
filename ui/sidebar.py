"""
侧边栏组件模块
包含疗愈风格的导航、实时评分展示、重置按钮等。
"""
import streamlit as st
from config import DIMENSIONS


def _render_nav_item(icon, label, active=False):
    """渲染单个导航项（HTML）"""
    active_class = ' active' if active else ''
    return f'<div class="sidebar-nav-item{active_class}">{icon} {label}</div>'


def render_sidebar():
    """
    渲染侧边栏 UI 组件（疗愈风格导航）
    包括：品牌标识、导航菜单、实时评分追踪、重置按钮。
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

        # 根据当前阶段高亮
        if st.session_state.is_completed:
            nav_items = [
                ("📊", "今日心理状态", False),
                ("🕸️", "六维情绪分析", True),
                ("📈", "历史趋势", False),
                ("📝", "情绪变化记录", False),
                ("🤝", "陪伴模式", False),
            ]
        elif len(st.session_state.display_messages) <= 1:
            nav_items = [
                ("📝", "今日心理状态", True),
                ("🕸️", "六维情绪分析", False),
                ("📈", "历史趋势", False),
                ("📝", "情绪变化记录", False),
                ("🤝", "陪伴模式", False),
            ]
        else:
            nav_items = [
                ("📝", "今日心理状态", False),
                ("🕸️", "六维情绪分析", True),
                ("📈", "历史趋势", False),
                ("📝", "情绪变化记录", False),
                ("🤝", "陪伴模式", False),
            ]

        for icon, label, active in nav_items:
            st.markdown(_render_nav_item(icon, label, active), unsafe_allow_html=True)

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

        has_any_score = False
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
                has_any_score = True
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

        # ---- 设置与重置 ----
        st.markdown(
            '<div style="font-size: 0.75rem; color: #9ab0c8; font-weight: 300; '
            'letter-spacing: 0.08em; padding: 0.3rem 0.8rem; margin-bottom: 0.3rem;">'
            '设 置</div>',
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
