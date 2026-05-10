"""
Session 状态管理模块
集中管理 Streamlit session_state 的初始化和重置。
"""
import streamlit as st
from config import DIMENSION_KEYS


def init_session_state():
    """
    初始化所有 session state 变量
    应在应用启动时调用一次。
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "display_messages" not in st.session_state:
        st.session_state.display_messages = [
            {
                "role": "assistant",
                "content": "你好！我是你的专属树洞助手。最近在学习和生活上感觉怎么样？有什么想跟我吐槽的吗？"
            }
        ]

    if "scores" not in st.session_state:
        st.session_state.scores = {k: None for k in DIMENSION_KEYS}

    if "is_completed" not in st.session_state:
        st.session_state.is_completed = False

    if "history" not in st.session_state:
        st.session_state.history = []

    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    if "cloud_consent" not in st.session_state:
        st.session_state.cloud_consent = False


def reset_session_state():
    """
    重置所有 session state（清空并重新初始化）
    """
    st.session_state.messages = []
    st.session_state.display_messages = [
        {
            "role": "assistant",
            "content": "你好！我是你的专属树洞助手。最近在学习和生活上感觉怎么样？有什么想跟我吐槽的吗？"
        }
    ]
    st.session_state.scores = {k: None for k in DIMENSION_KEYS}
    st.session_state.is_completed = False
    st.session_state.history = []


def get_current_scores():
    """获取当前各维度评分列表（None 替换为 5）"""
    from config import DIMENSION_KEYS
    vals = [st.session_state.scores[k] for k in DIMENSION_KEYS]
    return [v if v is not None else 5 for v in vals]
