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

    # ---- 历史记录新状态 ----
    if "show_history" not in st.session_state:
        st.session_state.show_history = False

    if "selected_session" not in st.session_state:
        st.session_state.selected_session = None

    if "viewing_history" not in st.session_state:
        st.session_state.viewing_history = False

    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False

    # ---- 云端认证状态 ----
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False
    if "skipped_login" not in st.session_state:
        st.session_state.skipped_login = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user_nickname" not in st.session_state:
        st.session_state.user_nickname = None


def reset_session_state():
    """
    重置所有 session state（清空并重新初始化）
    保留用户登录状态。
    """
    # 保留登录信息
    saved_login = {
        "is_logged_in": st.session_state.get("is_logged_in", False),
        "skipped_login": st.session_state.get("skipped_login", False),
        "user_id": st.session_state.get("user_id", None),
        "user_email": st.session_state.get("user_email", None),
        "user_nickname": st.session_state.get("user_nickname", None),
        "cloud_consent": st.session_state.get("cloud_consent", False),
        "upload_full_content": st.session_state.get("upload_full_content", True),
    }

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
    st.session_state.show_history = False
    st.session_state.selected_session = None
    st.session_state.viewing_history = False

    # 恢复登录信息
    for k, v in saved_login.items():
        st.session_state[k] = v


def get_current_scores():
    """获取当前各维度评分列表（None 替换为 5）"""
    from config import DIMENSION_KEYS
    vals = [st.session_state.scores[k] for k in DIMENSION_KEYS]
    return [v if v is not None else 5 for v in vals]
