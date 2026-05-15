"""
本地存储服务模块
提供本地持久化存储和读取功能，用于保存用户的历史对话记录、心理评分趋势及 AI 建议。
每次完整对话独立存储，永久保留。
"""
import json
import os
import glob
from datetime import datetime
import streamlit as st

# 本地数据存储目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
SCORES_DIR = os.path.join(DATA_DIR, "scores")


def _ensure_dirs():
    """确保数据目录存在"""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    os.makedirs(SCORES_DIR, exist_ok=True)


def generate_session_id():
    """
    生成唯一的会话 ID（按时间，支持同一天多次对话）

    Returns:
        str: 会话 ID，格式为 YYYY-MM-DD_HHMMSS
    """
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


# ==========================================
# 保存完整会话记录
# ==========================================

def save_complete_session(session_id, data):
    """
    保存一次完整对话的所有数据到本地。
    每次保存创建独立文件，不会覆盖旧文件。

    Args:
        session_id: str, 唯一会话标识
        data: dict, 包含以下字段：
            - display_messages: list, 完整聊天记录
            - scores: dict, 六维评分 {x1~x6}
            - composite_score: float, 综合总分
            - level_name: str, 状态评级
            - ai_suggestion: str, AI 生成的建议文本
            - timestamp: str, ISO 格式时间
            - summary: str, 本次状态摘要
            - label: str, 心理状态标签
    """
    _ensure_dirs()

    # 保存完整记录到一个 JSON 文件
    record_file = os.path.join(HISTORY_DIR, f"{session_id}.json")
    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==========================================
# 加载单条会话记录
# ==========================================

def load_session(session_id):
    """
    加载指定会话的完整记录

    Args:
        session_id: str, 会话标识（文件名不含.json）

    Returns:
        dict or None: 完整会话数据
    """
    record_file = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(record_file):
        with open(record_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 兼容旧版：如果 data 是 list 格式（旧版纯消息记录），转换为新版 dict 格式
        if isinstance(data, list):
            data = {
                "session_id": session_id,
                "timestamp": session_id.replace("_", "T") + ":00",
                "display_messages": data,
                "scores": {},
                "composite_score": 0,
                "level_name": "未知",
                "icon": "📝",
                "label": "旧版记录",
                "summary": "早期对话记录",
                "ai_suggestion": "",
                "ai_direction": "",
            }
        return data
    return None


# ==========================================
# 获取所有会话列表
# ==========================================

def get_all_sessions():
    """
    获取所有历史会话列表，按时间倒序排列（最新在前）

    Returns:
        list: 会话 ID 列表
    """
    _ensure_dirs()
    sessions = []
    if os.path.exists(HISTORY_DIR):
        for f in os.listdir(HISTORY_DIR):
            if f.endswith(".json"):
                session_id = f.replace(".json", "")
                sessions.append(session_id)
    return sorted(sessions, reverse=True)


# ==========================================
# 获取所有历史总分趋势
# ==========================================

def get_all_trend_data():
    """
    获取所有历史记录中的总分趋势，用于长期趋势图
    每次对话作为一个独立数据点，横坐标显示 YYYY-MM-DD HH:MM:SS

    Returns:
        list: [{"session_id": "...", "display_label": "...", "score": 72.5, ...}, ...]
    """
    all_trends = []
    for session_id in get_all_sessions():
        data = load_session(session_id)
        if data and "composite_score" in data:
            # 使用会话中保存的时间戳（完整到秒）
            timestamp = data.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    display_label = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    display_label = session_id.replace("_", " ")
            else:
                # 从 session_id 解析（兼容旧数据）
                parts = session_id.split("_")
                date_part = parts[0]
                time_part = parts[1] if len(parts) > 1 else "000000"
                if len(time_part) >= 6:
                    time_str = f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                elif len(time_part) >= 4:
                    time_str = f"{time_part[:2]}:{time_part[2:4]}:00"
                else:
                    time_str = "00:00:00"
                display_label = f"{date_part} {time_str}"

            all_trends.append({
                "display_label": display_label,
                "session_id": session_id,
                "score": data.get("composite_score", 0),
                "label": data.get("level_name", "未知"),
                "summary": data.get("summary", ""),
            })
    # 按时间从旧到新排列（用于趋势图）
    all_trends.sort(key=lambda x: x["display_label"])
    return all_trends


# ==========================================
# 获取历史记录摘要列表（侧边栏用）
# ==========================================

def get_session_summaries():
    """
    获取所有历史会话的摘要信息，用于侧边栏展示

    Returns:
        list: [{"session_id": str, "display_date": str, "score": float, "label": str, "summary": str}, ...]
    """
    summaries = []
    for session_id in get_all_sessions():
        data = load_session(session_id)
        if data is None:
            continue
        # 解析显示名
        parts = session_id.split("_")
        date_part = parts[0]
        time_part = parts[1] if len(parts) > 1 else ""
        if time_part and len(time_part) >= 4:
            display = f"{date_part} {time_part[:2]}:{time_part[2:4]}"
        else:
            display = date_part
        summaries.append({
            "session_id": session_id,
            "display_date": display,
            "score": data.get("composite_score"),
            "label": data.get("level_name", ""),
            "summary": data.get("summary", ""),
        })
    # 按时间从旧到新排列（侧边栏从左到右）
    summaries.reverse()
    return summaries


# ==========================================
# 删除单条会话
# ==========================================

def delete_session(session_id):
    """删除指定会话的本地数据"""
    for f in glob.glob(os.path.join(HISTORY_DIR, f"{session_id}.json")):
        os.remove(f)


# ==========================================
# 自动保存当前会话（完成评估时调用）
# ==========================================

def auto_save_current_session():
    """
    自动保存当前会话到本地。
    每次完成评估后调用，创建独立存储文件。
    """
    from models.eval_net import calculate_composite_score
    from config import DIMENSION_KEYS
    from utils.status_assets import get_status_assets

    session_id = generate_session_id()
    display_messages = st.session_state.get("display_messages", [])
    scores = st.session_state.get("scores", {})

    # 计算综合评分
    current_vals = [scores.get(k, 5) for k in DIMENSION_KEYS]
    current_vals = [v if v is not None else 5 for v in current_vals]
    composite_score = calculate_composite_score(current_vals)

    # 获取状态标签
    icon, level_name, theme_color, ai_direction = get_status_assets(composite_score, current_vals)

    # 生成摘要
    summary = _generate_summary(composite_score, scores)

    # 获取建议（从最后的 AI 回复中提取）
    ai_suggestion = _extract_last_ai_reply(display_messages)

    record_data = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "display_messages": display_messages,
        "scores": scores,
        "composite_score": composite_score,
        "level_name": level_name,
        "icon": icon,
        "label": level_name,
        "summary": summary,
        "ai_suggestion": ai_suggestion,
        "ai_direction": ai_direction,
    }

    save_complete_session(session_id, record_data)

    # 如果用户已授权云端存储，同步到 Supabase
    if st.session_state.get("cloud_consent", False):
        try:
            from services.storage_cloud import upload_session_to_cloud
            upload_full = st.session_state.get("upload_full_content", True)
            upload_session_to_cloud(session_id, record_data, upload_full)
        except Exception:
            pass  # 云端同步失败不影响本地保存


def _generate_summary(score, scores):
    """根据评分生成简短摘要"""
    if score >= 85:
        return "状态极佳，充满能量"
    elif score >= 70:
        return "状态良好，保持稳定"
    elif score >= 55:
        return "状态一般，有轻微波动"
    elif score >= 40:
        return "状态需关注，建议留意情绪变化"
    else:
        return "状态偏低，建议寻求支持"


def _extract_last_ai_reply(messages):
    """从对话记录中提取最后一条 AI 回复作为建议"""
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            return msg.get("content", "")
    return ""


# ==========================================
# 兼容旧版：保留旧函数签名
# ==========================================

def save_session_data(session_id, display_messages, scores, history):
    """兼容旧版调用"""
    auto_save_current_session()


def load_session_data(session_id):
    """兼容旧版调用"""
    data = load_session(session_id)
    if data:
        return (
            data.get("display_messages"),
            data.get("scores"),
            [{"score": data.get("composite_score"), "time": "00:00:00"}]
        )
    return None, None, None


def has_history():
    """检查是否存在任何历史记录"""
    return len(get_all_sessions()) > 0
