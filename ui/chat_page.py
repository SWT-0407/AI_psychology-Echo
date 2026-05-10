"""
对话采集页面（第二阶段）
渲染多轮对话历史 + 聊天输入框，实现与 AI 的深度交流并动态评分。
"""
import json
import streamlit as st
from config import DIMENSIONS, DIMENSION_KEYS
from services.ai_service import chat_with_ai, parse_ai_response
from utils.prompts import build_dynamic_prompt
from services.storage_local import auto_save_current_session


def process_ai_interaction(user_input):
    """
    处理用户输入：调用 AI、解析响应、更新分数与状态

    Args:
        user_input: str, 用户输入的文本
    """
    if not user_input or not user_input.strip():
        return

    # 1. 写入用户消息到显示历史
    st.session_state.display_messages.append({"role": "user", "content": user_input})

    # 2. 构建动态 prompt（包含当前评分状态）
    dynamic_prompt = build_dynamic_prompt(st.session_state.scores)

    # 3. 构建消息历史
    messages_for_api = [{"role": "system", "content": dynamic_prompt}]
    for msg in st.session_state.display_messages:
        messages_for_api.append({"role": msg["role"], "content": msg["content"]})

    # 4. 调用 AI API
    with st.spinner("正在品读并分析你的状态..."):
        raw_result = chat_with_ai(messages_for_api)

    # 5. 解析响应
    reply_text, new_scores, status = parse_ai_response(raw_result)

    # 6. 更新评分
    for k in st.session_state.scores:
        if k in new_scores and new_scores[k] is not None:
            st.session_state.scores[k] = new_scores[k]

    # 7. 记录回复
    st.session_state.display_messages.append({"role": "assistant", "content": reply_text})

    # 8. 检查评估是否完成
    if status == "completed":
        st.session_state.is_completed = True
        # 自动保存当前会话到本地
        auto_save_current_session()


def render_chat_page():
    """
    渲染对话交互页面
    包括历史对话展示和聊天输入框。
    """
    st.title("📓 我的心理日记本")

    # 显示日期
    from datetime import datetime
    today = datetime.now()
    week_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    st.subheader(f"{today.strftime('%Y-%m-%d')} {week_map[today.weekday()]}")

    # 渲染历史对话
    for msg in st.session_state.display_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 聊天输入框
    prompt = st.chat_input("针对刚才的内容，我们可以深入聊聊...")

    if prompt:
        process_ai_interaction(prompt)
        st.rerun()
