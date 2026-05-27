from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any, Dict

import streamlit as st

from services.safety import SafetyAssessment, crisis_resource_text


ACTIVE_CRISIS_ALERT_KEY = "echo_active_crisis_alert"
CRISIS_ALERT_LOG_KEY = "echo_crisis_alert_log"


def queue_crisis_alert(
    source: str,
    assessment: SafetyAssessment,
    user_text: str,
    assistant_name: str = "Echo",
) -> None:
    """Schedule a blocking crisis dialog on the next Streamlit rerun."""
    if not assessment.is_crisis:
        return

    now = datetime.now().isoformat(timespec="seconds")
    st.session_state[ACTIVE_CRISIS_ALERT_KEY] = {
        "id": f"{source}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "source": source,
        "assistant_name": assistant_name,
        "created_at": now,
        "level": assessment.level,
        "matched_terms": list(assessment.matched_terms),
        "user_text_preview": str(user_text or "").strip()[:160],
    }


def render_crisis_alert_if_needed() -> None:
    alert = st.session_state.get(ACTIVE_CRISIS_ALERT_KEY)
    if isinstance(alert, dict) and alert.get("level") == "crisis":
        _crisis_dialog(alert)


def _record_alert_action(action: str) -> None:
    alert = st.session_state.get(ACTIVE_CRISIS_ALERT_KEY)
    if not isinstance(alert, dict):
        return

    log = st.session_state.setdefault(CRISIS_ALERT_LOG_KEY, [])
    log.append(
        {
            "id": alert.get("id"),
            "source": alert.get("source"),
            "created_at": alert.get("created_at"),
            "action": action,
            "handled_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    st.session_state.pop(ACTIVE_CRISIS_ALERT_KEY, None)


@st.dialog("危机提示：请优先联系现实支持", width="large", dismissible=False)
def _crisis_dialog(alert: Dict[str, Any]) -> None:
    resources = crisis_resource_text()
    assistant_name = escape(str(alert.get("assistant_name") or "Echo"))
    preview = escape(str(alert.get("user_text_preview") or ""))

    st.markdown(
        """
        <style>
        div[data-testid="stDialog"] section[role="dialog"] {
            border-top: 8px solid #e5484d;
        }
        .echo-crisis-title {
            color: #b42318;
            font-size: 1.1rem;
            font-weight: 900;
            margin-bottom: .35rem;
        }
        .echo-crisis-box {
            border: 1px solid rgba(229,72,77,.35);
            border-radius: 8px;
            background: #fff5f5;
            padding: 14px 16px;
            color: #5f1b1f;
            line-height: 1.65;
            margin: 12px 0;
        }
        .echo-crisis-resource {
            border: 1px solid rgba(42,98,197,.25);
            border-radius: 8px;
            background: #f4f8ff;
            padding: 12px 14px;
            color: #1c3f7a;
            line-height: 1.6;
            margin: 12px 0;
        }
        .echo-crisis-preview {
            color: #7a4f52;
            font-size: .92rem;
            word-break: break-word;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="echo-crisis-title">请先把现实安全放在第一位。</div>
        <div>{assistant_name} 可以继续陪你，但这里不能替代急救、心理咨询或医疗判断。请现在联系现实中的专业人士、家人、朋友或其他可信任的人。</div>
        """,
        unsafe_allow_html=True,
    )

    if preview:
        st.markdown(
            f'<div class="echo-crisis-preview">触发内容片段：{preview}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="echo-crisis-box">
        请现在优先做一件事：联系现实中的专业人士、家人朋友或紧急支持。可以是当地紧急救援、学校心理中心、辅导员、校医院、持证心理咨询师/精神卫生专业人士，或此刻能陪在你身边的可信任联系人。<br/>
        如果你已经有具体计划、工具、地点，或担心马上会伤害自己/他人，请不要一个人待着，并尽快离开可能造成伤害的物品或地点。
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="echo-crisis-resource">{escape(resources)}</div>',
        unsafe_allow_html=True,
    )

    link_cols = st.columns([1, 1])
    with link_cols[0]:
        st.link_button("访问 988 Lifeline", "https://988lifeline.org/", use_container_width=True)
    with link_cols[1]:
        st.link_button(
            "988 多语言电话说明",
            "https://988lifeline.org/faq/calling-the-988-lifeline/faq-is-the-988-lifeline-available-in-other-languages-for-non-english-speakers/",
            use_container_width=True,
        )

    if st.button("我正在联系专业人士、家人朋友或紧急支持", type="primary", use_container_width=True):
        _record_alert_action("contacting_professional_support")
        st.rerun()

    ack_key = f"crisis_ack_{alert.get('id')}"
    acknowledged = st.checkbox(
        "我理解 Echo 不是医疗或危机干预服务；如果我正处在危险中，我会立即联系专业人士、当地紧急救援、家人朋友或其他可信任的人。",
        key=ack_key,
    )
    if st.button("确认已理解，继续使用", disabled=not acknowledged, use_container_width=True):
        _record_alert_action("acknowledged_and_continue")
        st.rerun()
