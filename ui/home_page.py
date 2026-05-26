import streamlit as st


HOME_CSS = """
<style>
#MainMenu, footer { visibility: hidden; }
.stApp {
    background: linear-gradient(135deg, #f7dce4 0%, #fff8f6 48%, #e8f4ef 100%);
}
.block-container { max-width: 1120px; padding-top: 2rem; }
.home-hello {
    color: #6b5960;
    font-size: 18px;
    margin-bottom: 18px;
}
.home-title {
    color: #3f3c46;
    font-size: 40px;
    font-weight: 900;
    margin: 10px 0 8px;
}
.feature-card {
    min-height: 260px;
    background: rgba(255,255,255,.78);
    border: 2px solid rgba(70,70,70,.12);
    border-radius: 16px;
    padding: 28px 22px;
    box-shadow: 0 12px 32px rgba(90,70,80,.12);
    text-align: center;
}
.feature-icon { font-size: 54px; margin-bottom: 12px; }
.feature-name { font-size: 28px; font-weight: 900; color: #3f3c46; }
.feature-desc { color: #675e66; font-size: 16px; line-height: 1.7; margin-top: 12px; }
.status-strip {
    display: inline-flex;
    gap: 10px;
    align-items: center;
    padding: 8px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,.65);
    border: 1px solid rgba(80,80,80,.12);
    color: #6b5960;
    margin-bottom: 18px;
}
.stButton > button {
    border-radius: 12px !important;
    border: 2px solid rgba(80,80,80,.18) !important;
    background: #ffffff !important;
    color: #4a3f48 !important;
    font-weight: 800 !important;
    min-height: 46px;
}
.stButton > button:hover {
    border-color: #d792a4 !important;
    color: #9d5367 !important;
}
</style>
"""


def _inject_css() -> None:
    st.markdown(HOME_CSS, unsafe_allow_html=True)


def _feature_card(icon: str, name: str, desc: str) -> None:
    st.markdown(
        f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <div class="feature-name">{name}</div>
            <div class="feature-desc">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _display_user() -> str:
    if st.session_state.get("is_logged_in"):
        return st.session_state.get("user_nickname") or st.session_state.get("user_email") or "已登录用户"
    return "本地模式"


def _logout() -> None:
    try:
        from services.storage_auth import logout_user
        logout_user()
    except Exception:
        pass
    st.session_state.is_logged_in = False
    st.session_state.skipped_login = False
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.user_nickname = ""
    st.session_state.cloud_consent = False
    st.session_state.page = "home"


def render_home_page() -> None:
    _inject_css()
    mode_text = "云端账号" if st.session_state.get("is_logged_in") else "本地存储"
    st.markdown(
        f"""
        <div class="status-strip">🔐 当前身份：{_display_user()} · {mode_text}</div>
        <div class="home-title">今天想进入哪一个空间？</div>
        <div class="home-hello">你的手帐档案、每日心情和聊天历史都会保存到原来的 data 存储结构里。</div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        _feature_card("🔬", "心理评测", "手帐日记、每日心情、历史记录和六维心理报告。")
        if st.button("进入心理评测", use_container_width=True, key="go_psytest"):
            st.session_state.page = "psytest"
            st.rerun()
    with c2:
        _feature_card("🗣️", "AI树洞", "温暖柔和的聊天空间，每条 AI 回复都可以五星评价。")
        if st.button("进入 AI 树洞", use_container_width=True, key="go_treehole"):
            st.session_state.page = "treehole"
            st.rerun()
    with c3:
        _feature_card("👥", "虚拟伴侣", "创建自定义角色，像联系人一样点开后继续聊天。")
        if st.button("进入虚拟伴侣", use_container_width=True, key="go_companion"):
            st.session_state.page = "companion"
            st.rerun()

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    if st.button("退出登录/返回登录页", key="logout"):
        _logout()
        st.rerun()
