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

def chat_with_vision(image_bytes, messages, temperature=0.7):
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
                            "url": f"data:image/jpeg;base64,{base64_image}",
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


# ==========================================
# 千问：表情分析（专用版，短 prompt 快速响应）
# ==========================================

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
    from config import (
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
                "valence": float(result.get("valence", 0.5)),
                "arousal": float(result.get("arousal", 0.5)),
                "dominance": float(result.get("dominance", 0.5)),
                "anxiety": float(result.get("anxiety", 0.0)),
                "fatigue": float(result.get("fatigue", 0.0)),
                "engagement": float(result.get("engagement", 0.5)),
                "analysis": result.get("analysis", ""),
            }
    except Exception:
        pass

    return {
        "emotion": "neutral", "emotion_cn": "平静",
        "valence": 0.5, "arousal": 0.5, "dominance": 0.5,
        "anxiety": 0.0, "fatigue": 0.0, "engagement": 0.5,
        "analysis": "",
    }

def transcribe_audio(audio_bytes):
    """
    使用千问 ASR 将语音转为文字

    千问 qwen3-asr-flash 兼容 OpenAI Whisper 的 API 格式。

    Args:
        audio_bytes: bytes, 音频二进制数据

    Returns:
        str: 识别出的文字
    """
    client = get_qwen_client()
    transcript = client.audio.transcriptions.create(
        model=QWEN_ASR_MODEL,
        file=("audio.webm", audio_bytes, "audio/webm")
    )
    return transcript.text


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
