"""
对话采集页面（第二阶段）
渲染多轮对话历史 + 聊天输入框，实现与 AI 的深度交流并动态评分。
"""
import streamlit as st
from services.ai_service import chat_with_ai, parse_ai_response
from utils.prompts import build_dynamic_prompt
from utils.rag_service import search_relevant_knowledge
from services.storage_local import auto_save_current_session


def process_ai_interaction(user_input):
    """
    处理用户输入：调用 AI、解析响应、更新分数与状态
    【纯功能函数，不涉及 UI 渲染】

    Args:
        user_input: str, 用户输入的文本
    """
    if not user_input or not user_input.strip():
        return

    # 1. 写入用户消息到显示历史
    st.session_state.display_messages.append({"role": "user", "content": user_input})

    # 1.5 RAG 知识检索：根据用户输入从书籍知识库中检索相关内容
    rag_context = search_relevant_knowledge(user_input, k=3)

    # 2. 构建动态 prompt（包含当前评分状态 + RAG 知识）
    dynamic_prompt = build_dynamic_prompt(st.session_state.scores, rag_context=rag_context)

    # 3. 构建消息历史
    messages_for_api = [{"role": "system", "content": dynamic_prompt}]
    for msg in st.session_state.display_messages:
        messages_for_api.append({"role": msg["role"], "content": msg["content"]})

    # 4. 调用 AI API
    with st.spinner(""):
        # 自定义 spinner 文本为空，使用 CSS 动画替代
        status_placeholder = st.empty()
        status_placeholder.markdown(
            '<div style="text-align: center; padding: 0.5rem;">'
            '<span style="color: #a0b8d0; font-weight: 300; font-size: 0.9rem;">'
            '📖 正在用心品读...</span></div>',
            unsafe_allow_html=True
        )
        raw_result = chat_with_ai(messages_for_api)
        status_placeholder.empty()

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
    渲染疗愈风格的对话交互页面
    包括 Logo、标题、历史对话展示和底部聊天输入框。
    """
    from styles.theme import render_logo

    # Logo
    render_logo()
    # 显示日期（简洁版）
    from datetime import datetime
    today = datetime.now()
    week_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = week_map[today.weekday()]

    st.markdown(
        f'<div style="text-align: center; margin-bottom: 0.5rem;">'
        f'<span style="color: #8aabca; font-size: 0.85rem; font-weight: 300;">'
        f'{today.strftime("%Y-%m-%d")} {weekday}  ·  继续聊聊吧</span></div>',
        unsafe_allow_html=True
    )

    # 渲染历史对话（只显示 AI 初始消息以来的内容）
    # display_messages[0] 是初始问候语，跳过 avatar 展示
    for i, msg in enumerate(st.session_state.display_messages):
        with st.chat_message(msg["role"]):
            st.markdown(
                f'<div class="chat-message-content">{msg["content"]}</div>',
                unsafe_allow_html=True
            )

    # 聊天输入框（底部固定）
    # ---- 多模态输入区域 ----
    from services.multimodal_service import MultimodalManager
    mm = MultimodalManager()
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        voice_btn = st.button('🎤 语音输入', key='voice_input_btn', use_container_width=True)
    with col2:
        if st.session_state.get('emotion_on', False):
            em = mm.get_current_emotion()
            emotion_text = em.get("emotion_cn", "😐 平静")
            st.markdown(f'<div style="text-align:center;font-size:0.85rem;color:#8aabca;">{emotion_text}</div>', unsafe_allow_html=True)
    with col3:
        if st.session_state.get('emotion_on', False):
            vec = em.get("vector", {})
            if vec:
                anxiety = vec.get("anxiety", 0.0)
                valence = vec.get("valence", 0.5)
                fatigue = vec.get("fatigue", 0.0)
                # 用颜色条简单指示风险
                risk_color = "#4CAF50" if valence > 0.6 and anxiety < 0.3 else "#FF9800" if valence > 0.3 else "#f44336"
                st.markdown(
                    f'<div style="text-align:center;font-size:0.75rem;color:{risk_color};font-weight:300;">'
                    f'V:{valence:.2f} A:{anxiety:.2f} F:{fatigue:.2f}</div>',
                    unsafe_allow_html=True
                )

    if voice_btn:
        with st.spinner('🎤 正在聆听...'):
            speech_text = mm.listen_speech(timeout=5.0)
        if speech_text:
            process_ai_interaction(speech_text)
            st.rerun()
        else:
            st.warning('未检测到语音，请重试')

    # 聊天输入框（底部固定）
    prompt = st.chat_input(
        placeholder='你可以和我聊聊最近的状态...（或点击🎤语音输入）'
    )

    if prompt:
        process_ai_interaction(prompt)
        st.rerun()
