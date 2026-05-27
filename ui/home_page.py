from html import escape

import streamlit as st

from services.proactive_engine import get_proactive_settings, set_proactive_enabled
from services.user_profile import get_profile_summary


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
    height: 330px;
    box-sizing: border-box;
    background: rgba(255,255,255,.78);
    border: 2px solid rgba(70,70,70,.12);
    border-radius: 16px;
    padding: 28px 22px;
    box-shadow: 0 12px 32px rgba(90,70,80,.12);
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
.feature-icon { font-size: 54px; margin-bottom: 12px; }
.feature-name { font-size: 28px; font-weight: 900; color: #3f3c46; }
.feature-desc { color: #675e66; font-size: 16px; line-height: 1.7; margin-top: 12px; min-height: 82px; }
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
.profile-panel {
    margin: 2px 0 24px;
    padding: 18px 20px;
    border-radius: 12px;
    background: rgba(255,255,255,.72);
    border: 1px solid rgba(80,80,80,.12);
    box-shadow: 0 10px 26px rgba(90,70,80,.10);
}
.profile-head {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: center;
    color: #3f3c46;
    font-weight: 900;
    font-size: 18px;
    margin-bottom: 12px;
}
.profile-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}
.profile-cell {
    min-height: 72px;
    padding: 12px 14px;
    border-radius: 8px;
    background: rgba(255,255,255,.66);
    border: 1px solid rgba(90,70,80,.10);
}
.profile-label {
    color: #8b7480;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 6px;
}
.profile-value {
    color: #3f3c46;
    font-size: 17px;
    font-weight: 900;
    line-height: 1.35;
}
.profile-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.profile-tag {
    padding: 4px 8px;
    border-radius: 999px;
    background: #fff;
    border: 1px solid rgba(215,146,164,.36);
    color: #8e5666;
    font-size: 12px;
    font-weight: 800;
}
.proactive-panel {
    margin: -10px 0 24px;
    padding: 12px 16px;
    border-radius: 10px;
    background: rgba(255,255,255,.66);
    border: 1px solid rgba(80,80,80,.12);
    color: #62545c;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
}
.proactive-title {
    font-weight: 900;
    color: #3f3c46;
}
.proactive-note {
    margin-top: 4px;
    font-size: 13px;
    color: #8b7480;
}
@media (max-width: 860px) {
    .profile-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
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


def _render_profile_snapshot() -> None:
    try:
        summary = get_profile_summary()
    except Exception:
        return

    score = summary.get("overall_score")
    score_text = f"{score}/100" if isinstance(score, (int, float)) else "等待评测"
    concern = summary.get("concern_index")
    concern_text = f"画像 {concern}/100" if isinstance(concern, (int, float)) else ""
    tags = summary.get("tags") or ["画像生成中"]
    topics = summary.get("recent_topics") or ["暂无主题"]
    signals = summary.get("signals") or []
    if signals:
        tag_html = "".join(
            f'<span class="profile-tag">{escape(str(item.get("label", "")))} '
            f'{escape(str(round(float(item.get("confidence", 0)) * 100)))}%</span>'
            for item in signals[:6]
        )
    else:
        tag_html = "".join(f'<span class="profile-tag">{escape(str(tag))}</span>' for tag in tags[:6])
    topic_html = "、".join(escape(str(topic)) for topic in topics[:4])
    safety_gate = summary.get("safety_gate_level") or ""
    risk_text = "重点关注" if summary.get("risk_level") in {"medium", "high"} or safety_gate in {"R2", "R3"} else "常规陪伴"

    st.markdown(
        f"""
        <div class="profile-panel">
            <div class="profile-head">
                <span>用户画像中枢</span>
                <span>{escape(risk_text)} · 已记录 {escape(str(summary.get("total_events", 0)))} 次互动</span>
            </div>
            <div class="profile-grid">
                <div class="profile-cell">
                    <div class="profile-label">综合状态</div>
                    <div class="profile-value">{escape(str(summary.get("integrated_level") or summary.get("level") or "暂无评估"))}<br>{escape(score_text)} {escape(concern_text)}</div>
                </div>
                <div class="profile-cell">
                    <div class="profile-label">最近情绪</div>
                    <div class="profile-value">{escape(str(summary.get("latest_emotion") or "暂无"))}</div>
                </div>
                <div class="profile-cell">
                    <div class="profile-label">关注主题</div>
                    <div class="profile-value">{topic_html}</div>
                </div>
                <div class="profile-cell">
                    <div class="profile-label">画像标签</div>
                    <div class="profile-tags">{tag_html}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def _render_proactive_controls() -> None:
    settings = get_proactive_settings()
    enabled = bool(settings.get("enabled", True))
    status = "已开启" if enabled else "已关闭"
    note = "角色、树洞和心理评测会在合适时机轻轻来一条消息。" if enabled else "关闭后不会自动生成主动消息，手动按钮仍可测试。"
    st.markdown(
        f"""
        <div class="proactive-panel">
            <div>
                <div class="proactive-title">主动关怀：{escape(status)}</div>
                <div class="proactive-note">{escape(note)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    label = "关闭主动关怀" if enabled else "开启主动关怀"
    if st.button(label, key="toggle_proactive_care"):
        set_proactive_enabled(not enabled)
        st.rerun()


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
    _render_profile_snapshot()
    if st.button("查看/编辑用户画像", key="go_profile_page"):
        st.session_state.page = "profile"
        st.rerun()
    _render_proactive_controls()

    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        _feature_card("🔬", "心理评测", "手帐日记、每日心情、历史记录和六维心理报告。")
        if st.button("进入心理评测", use_container_width=True, key="go_psytest"):
            st.session_state.page = "psytest"
            st.rerun()
    with c2:
        _feature_card("🗣️", "AI树洞", "支持语音输入和表情识别的温暖聊天空间，每条 AI 回复都可以五星评价。")
        if st.button("进入 AI 树洞", use_container_width=True, key="go_treehole"):
            st.session_state.page = "treehole"
            st.rerun()
    with c3:
        _feature_card("👥", "虚拟角色", "创建自定义角色，支持语音输入和表情识别，像联系人一样继续聊天。")
        if st.button("进入虚拟角色", use_container_width=True, key="go_companion"):
            st.session_state.page = "companion"
            st.rerun()

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    if st.button("退出登录/返回登录页", key="logout"):
        _logout()
        st.rerun()
