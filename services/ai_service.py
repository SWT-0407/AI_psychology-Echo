"""
AI 服务模块
封装与 DeepSeek API 的交互逻辑，包括多轮对话、JSON 解析等。
"""
import json
import re
from openai import OpenAI
import streamlit as st
from config import API_KEY, API_BASE_URL, MODEL_NAME


def get_ai_client():
    """
    获取 OpenAI 客户端实例

    Returns:
        OpenAI: 配置好的客户端
    """
    return OpenAI(api_key=API_KEY, base_url=API_BASE_URL)


def chat_with_ai(messages, temperature=0.7):
    """
    与 AI 进行一轮对话

    Args:
        messages: list, 消息历史（含 system prompt）
        temperature: float, 温度参数

    Returns:
        str: AI 返回的原始文本
    """
    client = get_ai_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content


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
            # JSON 解析失败，回退
            pass

    # 无有效 JSON，直接返回原文
    return raw_result, {}, "ongoing"


def generate_report(score, dimension_vals, dim_names, ai_direction, temperature=0.85, rag_context=""):
    """
    生成深度解析报告

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

    # 传入 rag_context 到 prompt 构建
    prompt = build_report_prompt(score, dimension_vals, dim_names, ai_direction, rag_context=rag_context)

    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature
            }
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"深度解析生成失败: {e}")
        return None
