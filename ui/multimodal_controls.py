import hashlib
from typing import Any, Dict, Optional

import streamlit as st


def get_multimodal_manager():
    from services.multimodal_service import MultimodalManager

    if "multimodal" not in st.session_state:
        st.session_state.multimodal = MultimodalManager()
    return st.session_state.multimodal


def emotion_summary(emotion: Optional[Dict[str, Any]]) -> str:
    if not emotion:
        return ""
    text = str(emotion.get("emotion_cn") or "").strip()
    vector = emotion.get("vector") or {}
    if not vector:
        return text
    return (
        f"{text} "
        f"(愉悦度 {vector.get('valence', 0.5):.2f}, "
        f"焦虑 {vector.get('anxiety', 0.0):.2f}, "
        f"疲劳 {vector.get('fatigue', 0.0):.2f})"
    ).strip()


def build_multimodal_prompt(user_text: str, emotion: Optional[Dict[str, Any]]) -> str:
    summary = emotion_summary(emotion)
    if not summary:
        return user_text
    return (
        f"{user_text}\n\n"
        f"[多模态补充] 摄像头表情识别到的当前状态：{summary}。"
        "请把它作为共情语气的参考，不要把它当成医学诊断。"
    )


def _audio_filename_and_type(audio_file) -> tuple[str, str]:
    filename = getattr(audio_file, "name", "") or "audio.webm"
    mime_type = getattr(audio_file, "type", "") or "audio/webm"
    if "." not in filename:
        suffix = ".wav" if "wav" in mime_type else ".webm"
        filename = f"audio{suffix}"
    return filename, mime_type


def _transcribe_new_audio(scope: str, mm, audio_file) -> str:
    if audio_file is None:
        return ""

    audio_bytes = audio_file.getvalue()
    if not audio_bytes:
        return ""

    digest = hashlib.sha256(audio_bytes).hexdigest()
    digest_key = f"{scope}_last_audio_digest"
    if st.session_state.get(digest_key) == digest:
        return ""

    filename, mime_type = _audio_filename_and_type(audio_file)
    with st.spinner("正在识别录音..."):
        text = mm.transcribe_audio(audio_bytes, filename=filename, mime_type=mime_type).strip()

    st.session_state[digest_key] = digest
    if text:
        st.success(f"已识别：{text}")
    elif getattr(mm, "last_speech_error", ""):
        st.error(f"语音识别服务调用失败：{mm.last_speech_error}")
    else:
        st.warning("录音已收到，但没有识别出文字。请靠近麦克风再试一次。")
    return text


def render_multimodal_controls(scope: str) -> Dict[str, Any]:
    mm = get_multimodal_manager()
    state_key = f"{scope}_emotion_on"
    st.session_state.setdefault(state_key, False)

    result: Dict[str, Any] = {"voice_text": "", "emotion": None}
    cols = st.columns([1.4, 1, 2])

    with cols[0]:
        if hasattr(st, "audio_input"):
            audio_file = st.audio_input("语音输入", key=f"{scope}_audio_input")
            voice_clicked = False
        else:
            audio_file = st.file_uploader(
                "上传语音",
                type=["wav", "mp3", "m4a", "webm", "ogg"],
                key=f"{scope}_audio_upload",
            )
            voice_clicked = st.button("🎤 本机麦克风", key=f"{scope}_voice_input", use_container_width=True)

    with cols[1]:
        emotion_on = st.toggle(
            "表情识别",
            value=st.session_state.get(state_key, False),
            key=f"{scope}_emotion_toggle",
        )

    if emotion_on and not st.session_state.get(state_key, False):
        if mm.start_emotion_detection():
            st.session_state[state_key] = True
            st.session_state.emotion_on = True
        else:
            st.session_state[state_key] = False
            st.warning("无法打开摄像头，表情识别暂不可用。")
    elif not emotion_on and st.session_state.get(state_key, False):
        mm.stop_emotion_detection()
        st.session_state[state_key] = False
        st.session_state.emotion_on = False

    if st.session_state.get(state_key, False):
        result["emotion"] = mm.get_current_emotion()
        summary = emotion_summary(result["emotion"]) or "表情识别已开启"
        with cols[2]:
            st.caption(f"当前表情：{summary}")
    else:
        with cols[2]:
            st.caption("录音后自动识别；也可开启摄像头表情识别。")

    result["voice_text"] = _transcribe_new_audio(scope, mm, audio_file)

    if voice_clicked:
        with st.spinner("正在聆听..."):
            result["voice_text"] = mm.listen_speech(timeout=5.0)
        if result["voice_text"]:
            st.success(f"已识别：{result['voice_text']}")
        else:
            st.warning("未检测到语音，请重试。")

    return result
