from html import escape
from typing import Any, Dict, List

import streamlit as st

from services.user_profile import (
    delete_profile_signal,
    get_profile_summary,
    list_profile_signals,
    load_user_profile,
    update_profile_preferences,
    update_profile_signal_status,
)


PROFILE_CSS = """
<style>
#MainMenu, footer { visibility: hidden; }
.stApp {
    background: linear-gradient(135deg, #f8e2e8 0%, #fffaf6 48%, #edf7f1 100%);
}
.block-container {
    max-width: 1120px;
    padding-top: 1.2rem;
}
.profile-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-bottom: 18px;
}
.profile-title {
    color: #3f3c46;
    font-size: 34px;
    font-weight: 950;
}
.profile-sub {
    color: #7c6872;
    font-size: 15px;
    margin-top: 4px;
}
.profile-band {
    padding: 18px 20px;
    border-radius: 8px;
    background: rgba(255,255,255,.74);
    border: 1px solid rgba(80,80,80,.12);
    margin-bottom: 18px;
}
.summary-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}
.summary-cell {
    min-height: 82px;
    padding: 13px 14px;
    border-radius: 8px;
    background: rgba(255,255,255,.66);
    border: 1px solid rgba(80,80,80,.10);
}
.summary-label {
    color: #8c7480;
    font-size: 12px;
    font-weight: 850;
    margin-bottom: 7px;
}
.summary-value {
    color: #3f3c46;
    font-size: 18px;
    font-weight: 900;
    line-height: 1.35;
}
.signal-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}
.signal-card {
    padding: 14px 16px;
    border-radius: 8px;
    background: rgba(255,255,255,.78);
    border: 1px solid rgba(80,80,80,.12);
}
.signal-head {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
    margin-bottom: 8px;
}
.signal-label {
    color: #3f3c46;
    font-size: 19px;
    font-weight: 900;
}
.signal-pill {
    padding: 4px 8px;
    border-radius: 999px;
    background: #fff;
    border: 1px solid rgba(209, 141, 159, .42);
    color: #8f5666;
    font-size: 12px;
    font-weight: 850;
    white-space: nowrap;
}
.signal-meta {
    color: #806d76;
    font-size: 13px;
    line-height: 1.6;
}
.signal-evidence {
    margin-top: 8px;
    color: #5d5057;
    font-size: 14px;
    line-height: 1.55;
    word-break: break-word;
}
.empty-note {
    color: #7c6872;
    padding: 18px 0;
}
.stButton > button,
.stFormSubmitButton > button {
    border-radius: 10px !important;
    border: 1px solid rgba(80,80,80,.16) !important;
    background: #ffffff !important;
    color: #4a3f48 !important;
    font-weight: 850 !important;
}
@media (max-width: 860px) {
    .summary-grid,
    .signal-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""


CATEGORY_LABELS = {
    "state": "状态",
    "topic": "主题",
    "emotion": "情绪",
    "preference": "偏好",
    "concern": "关注点",
    "legacy": "旧标签",
}


def _inject_css() -> None:
    st.markdown(PROFILE_CSS, unsafe_allow_html=True)


def _category_label(category: str) -> str:
    return CATEGORY_LABELS.get(str(category or ""), str(category or "画像"))


def _confidence_text(value: Any) -> str:
    try:
        return f"{round(float(value) * 100)}%"
    except (TypeError, ValueError):
        return "待确认"


def _signal_card(signal: Dict[str, Any], index: int) -> None:
    signal_id = str(signal.get("id") or "")
    status = str(signal.get("status") or "active")
    confidence = signal.get("current_confidence", signal.get("confidence"))
    sources = "、".join(str(item) for item in signal.get("sources", []) if item) or "本地画像"
    evidence = str(signal.get("last_evidence") or "暂无证据摘录")
    status_text = "当前" if status == "active" else "已隐藏" if status == "hidden" else "已否定"

    st.markdown(
        f"""
        <div class="signal-card">
            <div class="signal-head">
                <div class="signal-label">{escape(str(signal.get("label") or ""))}</div>
                <div class="signal-pill">{escape(_category_label(str(signal.get("category") or "")))} · {escape(_confidence_text(confidence))}</div>
            </div>
            <div class="signal-meta">
                {escape(status_text)} · 证据 {escape(str(signal.get("evidence_count", 0)))} 次 · 来源：{escape(sources)}
            </div>
            <div class="signal-evidence">{escape(evidence)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns([1, 1, 1, 5])
    if status == "active":
        with cols[0]:
            if st.button("保留", key=f"keep_signal_{index}"):
                update_profile_signal_status(signal_id, "active")
                st.toast("已保留")
                st.rerun()
        with cols[1]:
            if st.button("隐藏", key=f"hide_signal_{index}"):
                update_profile_signal_status(signal_id, "hidden")
                st.rerun()
    else:
        with cols[0]:
            if st.button("恢复", key=f"restore_signal_{index}"):
                update_profile_signal_status(signal_id, "active")
                st.rerun()
    with cols[2]:
        if st.button("删除", key=f"delete_signal_{index}"):
            delete_profile_signal(signal_id)
            st.rerun()


def _render_summary(summary: Dict[str, Any]) -> None:
    score = summary.get("overall_score")
    score_text = f"{score}/100" if isinstance(score, (int, float)) else "等待评测"
    topics = "、".join(escape(str(item)) for item in (summary.get("recent_topics") or ["暂无"]))
    tags = "、".join(escape(str(item)) for item in (summary.get("tags") or ["画像生成中"]))
    st.markdown(
        f"""
        <section class="profile-band">
            <div class="summary-grid">
                <div class="summary-cell">
                    <div class="summary-label">综合状态</div>
                    <div class="summary-value">{escape(str(summary.get("integrated_level") or summary.get("level") or "暂无"))}<br>{escape(score_text)}</div>
                </div>
                <div class="summary-cell">
                    <div class="summary-label">最近情绪</div>
                    <div class="summary-value">{escape(str(summary.get("latest_emotion") or "暂无"))}</div>
                </div>
                <div class="summary-cell">
                    <div class="summary-label">关注主题</div>
                    <div class="summary-value">{topics}</div>
                </div>
                <div class="summary-cell">
                    <div class="summary-label">画像标签</div>
                    <div class="summary-value">{tags}</div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_preferences(profile: Dict[str, Any]) -> None:
    prefs = profile.get("preferences") or {}
    with st.form("profile_preferences_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            reply_style = st.selectbox(
                "陪伴风格",
                ["温柔陪伴", "理性分析", "轻松聊天", "直接建议"],
                index=["温柔陪伴", "理性分析", "轻松聊天", "直接建议"].index(prefs.get("reply_style", "温柔陪伴"))
                if prefs.get("reply_style", "温柔陪伴") in ["温柔陪伴", "理性分析", "轻松聊天", "直接建议"]
                else 0,
            )
        with c2:
            reply_length = st.selectbox(
                "回复长度",
                ["短一点", "适中", "详细一点"],
                index=["短一点", "适中", "详细一点"].index(prefs.get("reply_length", "适中"))
                if prefs.get("reply_length", "适中") in ["短一点", "适中", "详细一点"]
                else 1,
            )
        with c3:
            advice_mode = st.selectbox(
                "建议方式",
                ["先共情再建议", "只倾听少建议", "先给行动建议", "先帮我拆解问题"],
                index=["先共情再建议", "只倾听少建议", "先给行动建议", "先帮我拆解问题"].index(
                    prefs.get("advice_mode", "先共情再建议")
                )
                if prefs.get("advice_mode", "先共情再建议") in ["先共情再建议", "只倾听少建议", "先给行动建议", "先帮我拆解问题"]
                else 0,
            )
        c4, c5 = st.columns(2)
        with c4:
            proactive_ok = st.checkbox("接受主动关怀", value=bool(prefs.get("proactive_ok", True)))
        with c5:
            multimodal_ok = st.checkbox("接受多模态参与画像", value=bool(prefs.get("multimodal_ok", False)))
        avoid_topics = st.text_area("不希望 Echo 主动提起的话题", value=str(prefs.get("avoid_topics") or ""), height=72)
        submitted = st.form_submit_button("保存偏好", use_container_width=True)

    if submitted:
        update_profile_preferences(
            {
                "reply_style": reply_style,
                "reply_length": reply_length,
                "advice_mode": advice_mode,
                "proactive_ok": proactive_ok,
                "multimodal_ok": multimodal_ok,
                "avoid_topics": avoid_topics.strip(),
            }
        )
        st.success("画像偏好已更新。")
        st.rerun()


def _render_signal_list(signals: List[Dict[str, Any]], active: bool) -> None:
    filtered = [
        signal
        for signal in signals
        if (str(signal.get("status") or "active") == "active") == active
    ]
    if not filtered:
        st.markdown('<div class="empty-note">还没有可显示的画像信号。</div>', unsafe_allow_html=True)
        return
    st.markdown('<div class="signal-grid">', unsafe_allow_html=True)
    for idx, signal in enumerate(filtered):
        _signal_card(signal, idx + (0 if active else 1000))
    st.markdown("</div>", unsafe_allow_html=True)


def render_profile_page() -> None:
    _inject_css()
    profile = load_user_profile()
    summary = get_profile_summary()

    st.markdown(
        """
        <div class="profile-top">
            <div>
                <div class="profile-title">Echo 对我的理解</div>
                <div class="profile-sub">用户填写的信息与系统推断分开保存；画像信号会随时间自然变弱。</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("返回首页", key="profile_back_home"):
        st.session_state.page = "home"
        st.rerun()

    _render_summary(summary)

    st.markdown('<section class="profile-band">', unsafe_allow_html=True)
    st.subheader("陪伴偏好")
    _render_preferences(profile)
    st.markdown("</section>", unsafe_allow_html=True)

    signals = list_profile_signals(include_hidden=True)
    current_tab, hidden_tab = st.tabs(["当前画像", "已隐藏/否定"])
    with current_tab:
        _render_signal_list(signals, active=True)
    with hidden_tab:
        _render_signal_list(signals, active=False)
