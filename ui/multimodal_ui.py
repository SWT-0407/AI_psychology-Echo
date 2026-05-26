import streamlit as st
from ui.multimodal_controls import _transcribe_new_audio

def get_multimodal_manager():
    from services.multimodal_service import MultimodalManager
    if "multimodal" not in st.session_state:
        st.session_state.multimodal = MultimodalManager()
    return st.session_state.multimodal


def render_multimodal_tab():
    """在侧边栏渲染多模态设置面板"""
    st.subheader("🧠 多模态设置")
    mm = get_multimodal_manager()

    st.markdown("### 🎤 语音")
    col1, col2 = st.columns(2)
    with col1:
        if hasattr(st, "audio_input"):
            audio_file = st.audio_input("测试语音", key="sidebar_audio_test")
            _transcribe_new_audio("sidebar_audio_test", mm, audio_file)
        elif st.button("🎤 测试麦克风", use_container_width=True):
            with st.spinner("聆听中..."):
                text = mm.listen_speech(timeout=3.0)
            if text:
                st.success(f"识别: {text}")
            else:
                st.warning("未检测到语音")
    with col2:
        if st.button("🔊 测试扬声器", use_container_width=True):
            mm.speak_text("你好，我是你的心理助手")
            st.success("已播报测试语音")

    st.markdown("### 📷 表情识别（千问视觉 API）")
    emotion_on = st.toggle(
        "开启摄像头表情识别",
        value=mm.emotion_started,
        key="emotion_toggle_sidebar"
    )
    if emotion_on and not mm.emotion_started:
        if mm.start_emotion_detection():
            st.success("✅ 已开启")
            st.session_state.emotion_on = True
        else:
            st.error("❌ 无法打开摄像头")
    elif not emotion_on and mm.emotion_started:
        mm.stop_emotion_detection()
        st.info("🔌 已关闭")
        st.session_state.emotion_on = False

    if mm.emotion_started:
        em = mm.get_current_emotion()
        st.metric("当前情绪", em.get("emotion_cn", "😐 平静"))

        # 展示维度情绪向量
        vec = em.get("vector", {})
        if vec:
            st.markdown("**情绪维度分析：**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption(f"😊 愉悦度: {vec.get('valence', 0.5):.2f}")
                st.progress(vec.get('valence', 0.5))
                st.caption(f"⚡ 唤醒度: {vec.get('arousal', 0.5):.2f}")
                st.progress(vec.get('arousal', 0.5))
                st.caption(f"👑 支配度: {vec.get('dominance', 0.5):.2f}")
                st.progress(vec.get('dominance', 0.5))
            with col_b:
                st.caption(f"😰 焦虑度: {vec.get('anxiety', 0.0):.2f}")
                st.progress(vec.get('anxiety', 0.0))
                st.caption(f"😴 疲劳度: {vec.get('fatigue', 0.0):.2f}")
                st.progress(vec.get('fatigue', 0.0))
                st.caption(f"💬 参与度: {vec.get('engagement', 0.5):.2f}")
                st.progress(vec.get('engagement', 0.5))
