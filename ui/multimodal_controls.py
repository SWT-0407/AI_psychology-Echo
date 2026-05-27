import base64
import hashlib
from html import escape
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
    status = str(emotion.get("status") or "ok").strip()
    if status != "ok":
        return text
    vector = emotion.get("vector") or {}
    if not vector:
        return text
    confidence = emotion.get("confidence")
    confidence_text = ""
    if confidence is not None:
        try:
            confidence_text = f"置信度 {float(confidence):.2f}, "
        except Exception:
            confidence_text = ""
    return (
        f"{text} "
        f"({confidence_text}愉悦度 {vector.get('valence', 0.5):.2f}, "
        f"焦虑 {vector.get('anxiety', 0.0):.2f}, "
        f"疲劳 {vector.get('fatigue', 0.0):.2f})"
    ).strip()


def build_multimodal_prompt(user_text: str, emotion: Optional[Dict[str, Any]]) -> str:
    if emotion and str(emotion.get("status") or "ok") != "ok":
        return user_text
    summary = emotion_summary(emotion)
    if not summary:
        return user_text
    return (
        f"{user_text}\n\n"
        f"[多模态补充] 摄像头表情识别到的当前状态：{summary}。"
        "请把它作为共情语气的参考，不要把它当成医学诊断。"
    )


def _emotion_frame_data_uri(frame) -> str:
    if frame is None or getattr(frame, "size", 0) == 0:
        return ""
    try:
        import cv2
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
        encoded = base64.b64encode(buffer.tobytes()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        return ""


def _render_emotion_video_popup(scope: str) -> None:
    mm = get_multimodal_manager()
    state_key = f"{scope}_emotion_on"
    if not st.session_state.get(state_key, False):
        return

    emotion = mm.get_current_emotion()
    summary = emotion_summary(emotion) or "表情识别已开启"
    stream_url = ""
    if hasattr(mm, "get_emotion_stream_url"):
        stream_url = mm.get_emotion_stream_url()

    if stream_url:
        body = f'<img src="{escape(stream_url, quote=True)}" alt="表情识别实时视频流" />'
    else:
        frame_uri = _emotion_frame_data_uri(mm.get_emotion_frame())
        if frame_uri:
            body = f'<img src="{frame_uri}" alt="表情识别视频预览" />'
        else:
            body = '<div class="emotion-video-placeholder">正在等待摄像头画面</div>'

    st.markdown(
        f"""
        <style>
        .emotion-video-overlay-root {{
            position: fixed !important;
            inset: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: transparent !important;
            pointer-events: none !important;
            z-index: 2147483647 !important;
            isolation: isolate !important;
        }}
        .emotion-video-popup {{
            position: fixed;
            right: 24px;
            bottom: 24px;
            width: 25vw;
            height: 25vh;
            min-width: 240px;
            min-height: 135px;
            background: #101216;
            border: 1px solid rgba(255,255,255,0.18);
            box-shadow: 0 14px 40px rgba(0,0,0,0.32);
            z-index: 2147483647 !important;
            overflow: hidden;
            pointer-events: none !important;
            transform: translateZ(0);
            will-change: transform;
        }}
        .emotion-video-popup img {{
            display: block;
            width: 100%;
            height: 100%;
            object-fit: contain;
            background: #101216;
        }}
        .emotion-video-status {{
            position: absolute;
            left: 8px;
            right: 8px;
            bottom: 8px;
            padding: 5px 7px;
            color: #fff;
            font-size: 12px;
            line-height: 1.35;
            background: rgba(0,0,0,0.58);
            border-radius: 6px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .emotion-video-placeholder {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: rgba(255,255,255,0.72);
            font-size: 13px;
            background: #101216;
        }}
        @media (max-width: 800px) {{
            .emotion-video-popup {{
                right: 12px;
                bottom: 12px;
                width: 42vw;
                height: 24vh;
                min-width: 200px;
            }}
        }}
        div[data-testid="stMarkdownContainer"]:has(.emotion-video-overlay-root),
        div[data-testid="stElementContainer"]:has(.emotion-video-overlay-root),
        div[data-testid="stVerticalBlock"]:has(.emotion-video-overlay-root) {{
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            pointer-events: none !important;
            z-index: 2147483647 !important;
        }}
        </style>
        <div class="emotion-video-overlay-root" aria-hidden="false">
            <div class="emotion-video-popup" role="region" aria-label="表情识别视频预览">
                {body}
                <div class="emotion-video-status">{escape(summary)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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


def render_multimodal_controls(scope: str, image_upload: bool = False) -> Dict[str, Any]:
    mm = get_multimodal_manager()
    state_key = f"{scope}_emotion_on"
    st.session_state.setdefault(state_key, False)

    result: Dict[str, Any] = {"voice_text": "", "emotion": None, "image_file": None}
    cols = st.columns([1.4, 0.34, 1, 2]) if image_upload else st.columns([1.4, 1, 2])
    audio_col = cols[0]
    image_col = cols[1] if image_upload else None
    emotion_col = cols[2] if image_upload else cols[1]
    status_col = cols[3] if image_upload else cols[2]

    with audio_col:
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

    if image_upload and image_col is not None:
        with image_col:
            st.markdown(
                f'<span class="multimodal-image-toggle-anchor {scope}-image-toggle-anchor"></span>',
                unsafe_allow_html=True,
            )
            if st.button("🖼️", key=f"{scope}_image_toggle", help="发送图片"):
                panel_key = f"{scope}_image_panel"
                st.session_state[panel_key] = not st.session_state.get(panel_key, False)
                st.rerun()

    with emotion_col:
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
        current_emotion = mm.get_current_emotion()
        if str(current_emotion.get("status") or "ok") == "ok":
            result["emotion"] = current_emotion
        summary = emotion_summary(current_emotion) or "表情识别已开启"
        with status_col:
            st.caption(f"当前表情：{summary}")
        _render_emotion_video_popup(scope)
    else:
        with status_col:
            st.caption("录音后自动识别；也可开启摄像头表情识别。")

    if image_upload and st.session_state.get(f"{scope}_image_panel", False):
        st.markdown('<div class="multimodal-image-panel">', unsafe_allow_html=True)
        result["image_file"] = st.file_uploader(
            "发送图片",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
            key=f"{scope}_image_upload",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    result["voice_text"] = _transcribe_new_audio(scope, mm, audio_file)

    if voice_clicked:
        with st.spinner("正在聆听..."):
            result["voice_text"] = mm.listen_speech(timeout=5.0)
        if result["voice_text"]:
            st.success(f"已识别：{result['voice_text']}")
        else:
            st.warning("未检测到语音，请重试。")

    return result
