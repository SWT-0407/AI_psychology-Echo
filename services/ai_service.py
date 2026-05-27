"""
AI 服务模块
封装与 DeepSeek / 千问 API 的交互逻辑
- DeepSeek: 语言对话和心理评估评分（JSON解析）
- 千问（通义）: 多模态（图片理解、语音识别、语音合成）
"""
import json
import re
from openai import OpenAI
import streamlit as st
from Multimodal.config import (
    DEEPSEEK_API_KEY, DEEPSEEK_API_BASE_URL, DEEPSEEK_MODEL_NAME,
    QWEN_API_KEY, QWEN_API_BASE_URL, QWEN_VISION_MODEL,
    QWEN_ASR_MODEL, QWEN_TTS_MODEL, QWEN_TTS_VOICE,
)


# ==========================================
# 客户端工厂
# ==========================================

def get_deepseek_client():
    """获取 DeepSeek（语言对话）客户端"""
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_BASE_URL)


def get_qwen_client():
    """获取千问（通义，多模态）客户端"""
    return OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_API_BASE_URL)


# ==========================================
# DeepSeek：语言对话
# ==========================================

def chat_with_ai(messages, temperature=0.7):
    """
    与 DeepSeek AI 进行一轮对话（纯语言）
    用于心理评估的多轮对话评分。

    Args:
        messages: list, 消息历史（含 system prompt）
        temperature: float, 温度参数

    Returns:
        str: AI 返回的原始文本
    """
    client = get_deepseek_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL_NAME,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content


# ==========================================
# 千问：图片理解（多模态视觉）
# ==========================================

def chat_with_vision(image_bytes, messages, temperature=0.7, detail="high", mime_type="image/jpeg"):
    """
    使用千问多模态模型分析图片内容

    Args:
        image_bytes: bytes, 图片二进制数据（JPEG/PNG）
        messages: list, 消息历史
        temperature: float, 温度参数

    Returns:
        str: AI 返回的文本描述
    """
    import base64

    client = get_qwen_client()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    # 构建千问兼容的多模态消息格式（与 OpenAI 格式一致）
    vision_messages = []
    for msg in messages:
        if msg["role"] == "user" and msg.get("content"):
            vision_messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": msg["content"]},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type or 'image/jpeg'};base64,{base64_image}",
                            "detail": detail
                        }
                    }
                ]
            })
        else:
            vision_messages.append(msg)

    response = client.chat.completions.create(
        model=QWEN_VISION_MODEL,
        messages=vision_messages,
        temperature=temperature,
        max_tokens=500
    )
    return response.choices[0].message.content


def analyze_user_image(image_bytes, user_text="", mime_type="image/png", detail="high"):
    """
    使用千问视觉 API 分析用户上传到聊天中的图片。

    返回一段适合放入树洞回复上下文的中文摘要；不直接作为最终回复展示。
    """
    import base64

    if not QWEN_API_KEY:
        raise RuntimeError("QWEN_API_KEY 未配置。")

    prompt = (
        "你是 AI 树洞聊天里的图片理解助手。请用自然中文客观分析用户上传的图片，"
        "包括可见内容、场景氛围、图片中文字（如有）和可能关联的情绪线索。"
        "不要做医学诊断，不要识别真实身份，不要推断敏感属性。"
        "请控制在 120 字以内，最后给出一个适合树洞回复参考的主题或情绪线索。"
    )
    if str(user_text or "").strip():
        prompt += f"\n用户随图片写下的话：{str(user_text).strip()}"

    client = get_qwen_client()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    response = client.chat.completions.create(
        model=QWEN_VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type or 'image/png'};base64,{base64_image}",
                        "detail": detail,
                    },
                },
            ],
        }],
        temperature=0.2,
        max_tokens=350,
    )
    return (response.choices[0].message.content or "").strip()


# ==========================================
# 千问：表情分析（专用版，短 prompt 快速响应）
# ==========================================

_FACE_EMOTION_CN = {
    "happy": "开心",
    "sad": "悲伤",
    "angry": "生气",
    "surprise": "惊讶",
    "fear": "恐惧",
    "disgust": "厌恶",
    "neutral": "平静",
    "contempt": "轻蔑",
    "anxious": "焦虑",
    "tired": "疲惫",
    "unknown": "未识别",
}

_FACE_EMOTION_ALIASES = {
    "surprised": "surprise",
    "fearful": "fear",
    "disgusted": "disgust",
    "calm": "neutral",
    "normal": "neutral",
    "uncertain": "unknown",
    "无法判断": "unknown",
    "未识别": "unknown",
}


def _normalize_face_emotion(label):
    raw = str(label or "unknown").strip().lower()
    return _FACE_EMOTION_ALIASES.get(raw, raw if raw in _FACE_EMOTION_CN else "unknown")


def _emotion_error_result(status, analysis, error=""):
    return {
        "emotion": "unknown",
        "emotion_cn": _FACE_EMOTION_CN["unknown"],
        "valence": 0.5,
        "arousal": 0.5,
        "dominance": 0.5,
        "anxiety": 0.0,
        "fatigue": 0.0,
        "engagement": 0.5,
        "confidence": 0.0,
        "analysis": analysis,
        "status": status,
        "error": error,
    }

def analyze_facial_expression(image_bytes, detail="low"):
    """
    使用千问视觉 API 进行精细化面部情绪分析
    基于维度情绪模型（Valence-Arousal-Dominance），输出连续量表值，
    可直接映射到心理评估的 x1~x6 维度。
    提示词模板和维度量表从 config.py 中读取，便于调参。

    Args:
        image_bytes: bytes, 摄像头拍摄的人脸图片（JPEG）

    Returns:
        dict: {
            "emotion": "主情绪标签",
            "emotion_cn": "主情绪中文名",
            "valence": 0.0~1.0,
            "arousal": 0.0~1.0,
            "dominance": 0.0~1.0,
            "anxiety": 0.0~1.0,
            "fatigue": 0.0~1.0,
            "engagement": 0.0~1.0,
            "analysis": "简短描述"
        }
    """
    import base64
    import json
    import re

    # 从 config 动态获取维度量表描述
    from Multimodal.config import (
        EMOTION_ANALYSIS_PROMPT,
        EMOTION_ANALYSIS_TEMPERATURE,
        EMOTION_ANALYSIS_MAX_TOKENS,
        build_face_scale_description,
    )

    scale_desc = build_face_scale_description()
    prompt = EMOTION_ANALYSIS_PROMPT.format(face_scale_desc=scale_desc)

    try:
        client = get_qwen_client()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model=QWEN_VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": detail
                        }
                    }
                ]
            }],
            temperature=EMOTION_ANALYSIS_TEMPERATURE,
            max_tokens=EMOTION_ANALYSIS_MAX_TOKENS
        )

        raw = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return {
                "emotion": result.get("emotion", "neutral"),
                "emotion_cn": result.get("emotion_cn", "平静"),
                "valence": _clamp01(result.get("valence", 0.5)),
                "arousal": _clamp01(result.get("arousal", 0.5)),
                "dominance": _clamp01(result.get("dominance", 0.5)),
                "anxiety": _clamp01(result.get("anxiety", 0.0)),
                "fatigue": _clamp01(result.get("fatigue", 0.0)),
                "engagement": _clamp01(result.get("engagement", 0.5)),
                "confidence": _clamp01(result.get("confidence", 0.5)),
                "analysis": result.get("analysis", ""),
            }
    except Exception:
        pass

    return {
        "emotion": "neutral", "emotion_cn": "平静",
        "valence": 0.5, "arousal": 0.5, "dominance": 0.5,
        "anxiety": 0.0, "fatigue": 0.0, "engagement": 0.5,
        "confidence": 0.0,
        "analysis": "",
    }


def _clamp01(value, default=0.5):
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return default


def transcribe_audio(audio_bytes, filename="audio.webm", mime_type="audio/webm"):
    """
    使用千问 ASR 将语音转为文字

    千问 qwen3-asr-flash 兼容 OpenAI Whisper 的 API 格式。

    Args:
        audio_bytes: bytes, 音频二进制数据

    Returns:
        str: 识别出的文字
    """
    import base64

    client = get_qwen_client()
    audio_mime_type = mime_type or "audio/webm"
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    data_uri = f"data:{audio_mime_type};base64,{audio_base64}"

    completion = client.chat.completions.create(
        model=QWEN_ASR_MODEL,
        messages=[{
            "role": "user",
            "content": [{
                "type": "input_audio",
                "input_audio": {
                    "data": data_uri
                }
            }]
        }],
        stream=False,
        extra_body={
            "asr_options": {
                "enable_itn": False
            }
        }
    )
    return completion.choices[0].message.content or ""


# ==========================================
# 千问：语音合成（TTS）
# ==========================================

def text_to_speech(text):
    """
    使用千问 TTS 将文字转为语音

    千问 qwen3-tts-flash 兼容 OpenAI TTS 的 API 格式。

    Args:
        text: str, 要转为语音的文字

    Returns:
        bytes: 音频二进制数据（MP3格式）
    """
    client = get_qwen_client()
    response = client.audio.speech.create(
        model=QWEN_TTS_MODEL,
        voice=QWEN_TTS_VOICE,
        input=text
    )
    return response.content


# ==========================================
# 通用工具函数
# ==========================================

def parse_ai_response(raw_result):
    """
    解析 AI 返回的 JSON 格式响应

    Args:
        raw_result: str, AI 返回的原始文本

    Returns:
        tuple: (reply_text, scores_dict, status)
            - reply_text: str, 回复文本
            - scores_dict: dict, 各维度评分
            - status: str, "ongoing" 或 "completed"
    """
    json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)

    if json_match:
        try:
            result_data = json.loads(json_match.group())
            reply_text = result_data.get("reply_to_user", raw_result)
            scores_dict = result_data.get("scores", {})
            status = result_data.get("status", "ongoing")
            return reply_text, scores_dict, status
        except json.JSONDecodeError:
            pass

    return raw_result, {}, "ongoing"


def generate_report(score, dimension_vals, dim_names, ai_direction, temperature=0.85, rag_context=""):
    """
    使用 DeepSeek 生成深度解析报告

    Args:
        score: float, 综合心理指数
        dimension_vals: list, 各维度评分
        dim_names: list, 维度名称列表
        ai_direction: str, AI 创作人设方向
        temperature: float, 温度参数
        rag_context: str, 从知识库检索到的书籍内容（可选）

    Returns:
        str: 生成的报告文本，失败返回 None
    """
    from utils.prompts import build_report_prompt
    import requests

    prompt = build_report_prompt(score, dimension_vals, dim_names, ai_direction, rag_context=rag_context)

    try:
        response = requests.post(
            f"{DEEPSEEK_API_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": DEEPSEEK_MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature
            }
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"深度解析生成失败: {e}")
        return None
