"""
本地存储服务模块
提供本地文件存储和读取功能，用于保存用户的历史对话记录和心理评分趋势。
"""
import json
import os
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


def save_session_data(session_id, display_messages, scores, history):
    """
    保存当前会话数据到本地

    Args:
        session_id: str, 会话标识（可用日期）
        display_messages: list, 对话记录
        scores: dict, 评分数据
        history: list, 历史趋势
    """
    _ensure_dirs()

    # 保存对话记录
    chat_file = os.path.join(HISTORY_DIR, f"{session_id}_chat.json")
    with open(chat_file, "w", encoding="utf-8") as f:
        json.dump(display_messages, f, ensure_ascii=False, indent=2)

    # 保存评分与趋势
    score_file = os.path.join(SCORES_DIR, f"{session_id}_scores.json")
    data = {
        "scores": scores,
        "history": history,
        "timestamp": datetime.now().isoformat()
    }
    with open(score_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_session_data(session_id):
    """
    从本地加载历史会话数据

    Args:
        session_id: str, 会话标识

    Returns:
        tuple: (display_messages, scores, history) 或 None
    """
    chat_file = os.path.join(HISTORY_DIR, f"{session_id}_chat.json")
    score_file = os.path.join(SCORES_DIR, f"{session_id}_scores.json")

    display_messages = None
    scores = None
    history = None

    if os.path.exists(chat_file):
        with open(chat_file, "r", encoding="utf-8") as f:
            display_messages = json.load(f)

    if os.path.exists(score_file):
        with open(score_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            scores = data.get("scores")
            history = data.get("history")

    return display_messages, scores, history


def get_all_sessions():
    """
    获取所有历史会话列表

    Returns:
        list: 会话 ID 列表（按时间排序）
    """
    _ensure_dirs()
    sessions = set()

    if os.path.exists(HISTORY_DIR):
        for f in os.listdir(HISTORY_DIR):
            if f.endswith("_chat.json"):
                session_id = f.replace("_chat.json", "")
                sessions.add(session_id)

    return sorted(list(sessions))


def get_history_trend():
    """
    获取所有历史评分趋势，用于跨日趋势图

    Returns:
        list: 所有历史评分记录 [{"score": float, "time": str, "date": str}, ...]
    """
    _ensure_dirs()
    all_trends = []

    for session_id in get_all_sessions():
        _, _, history = load_session_data(session_id)
        if history:
            for entry in history:
                entry_copy = entry.copy()
                entry_copy["date"] = session_id
                all_trends.append(entry_copy)

    return all_trends


# ==========================================
# 【请补充相应内容】功能预留
# ==========================================

def export_user_report(user_id):
    """
    导出一份用户完整报告（包含所有历史记录）

    Args:
        user_id: str, 用户标识

    Returns:
        dict: 包含所有历史数据的报告
    """
    # TODO: 实现用户报告导出功能
    # 下面是一个框架，需补充具体实现
    report = {
        "user_id": user_id,
        "generated_at": datetime.now().isoformat(),
        "total_sessions": len(get_all_sessions()),
        "trend_data": get_history_trend(),
        "summary": "请补充：生成用户心理变化摘要"
    }
    st.info("⚠️ export_user_report 功能尚待完善")
    return report


def delete_session_data(session_id):
    """
    删除指定会话的本地数据

    Args:
        session_id: str, 会话标识
    """
    import glob
    for f in glob.glob(os.path.join(HISTORY_DIR, f"{session_id}*")):
        os.remove(f)
    for f in glob.glob(os.path.join(SCORES_DIR, f"{session_id}*")):
        os.remove(f)


def auto_save_current_session():
    """
    自动保存当前会话（按日期）
    """
    from datetime import datetime
    session_id = datetime.now().strftime("%Y-%m-%d")
    save_session_data(
        session_id=session_id,
        display_messages=st.session_state.get("display_messages", []),
        scores=st.session_state.get("scores", {}),
        history=st.session_state.get("history", [])
    )
