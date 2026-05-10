"""
侧边栏组件模块
包含系统状态监控、实时评分展示、重置按钮等。
"""
import streamlit as st
from config import DIMENSIONS


def render_sidebar():
    """
    渲染侧边栏 UI 组件
    包括 API 状态、实时评分追踪、重置按钮等。
    """
    with st.sidebar:
        st.header("⚙️ 系统状态监控")
        st.success("API Key 已配置")
        st.divider()

        st.header("📊 实时状态追踪 (Input)")
        st.caption("0表示高风险，10表示非常健康。")

        for key, name in DIMENSIONS.items():
            score = st.session_state.scores[key]
            if score is None:
                st.info(f"{name}: 待评估")
            else:
                st.success(f"{name}: **{score}/10**")
                st.progress(score / 10.0)

        if st.session_state.is_completed:
            st.divider()
            st.warning("✅ 特征采集完毕，报告已生成。")

        st.divider()

        # 云端存储授权（如未完成评估时显示）
        if not st.session_state.is_completed:
            from services.storage_cloud import request_user_consent
            consent = request_user_consent()
            if consent:
                st.session_state.cloud_consent = True

        st.divider()

        if st.button("🔄 重置评估系统", use_container_width=True):
            st.session_state.clear()
            st.rerun()
