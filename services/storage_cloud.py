
"""
云端存储服务模块（Supabase）
在用户授权同意后，将用户数据同步到云端。
提供数据上传、拉取、连接检测等功能。
"""
import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# 加载环境变量
load_dotenv()

# Supabase 连接配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# 延迟初始化（首次使用时才创建连接）
_supabase_client = None


def _get_client():
    """获取 Supabase 客户端（惰性初始化）"""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            st.error("Supabase 配置缺失，请在 .env 文件中设置 SUPABASE_URL 和 SUPABASE_ANON_KEY")
            return None
        try:
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            st.error(f"Supabase 客户端创建失败: {e}")
            return None
    return _supabase_client


def upload_session_to_cloud(session_id, data):
    """
    将一次完整会话数据上传到 Supabase 云端

    Args:
        session_id: str, 唯一会话标识（用于 upsert 去重）
        data: dict, 包含会话数据的字典

    Returns:
        bool: 是否上传成功
    """
    client = _get_client()
    if client is None:
        return False

    try:
        record = {
            "session_id": session_id,
            "user_id": st.session_state.get("user_id", "anonymous"),
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "display_messages": data.get("display_messages", []),
            "scores": data.get("scores", {}),
            "composite_score": data.get("composite_score", 0),
            "level_name": data.get("level_name", ""),
            "icon": data.get("icon", ""),
            "label": data.get("label", ""),
            "summary": data.get("summary", ""),
            "ai_suggestion": data.get("ai_suggestion", ""),
            "ai_direction": data.get("ai_direction", ""),
        }

        res = client.table("chat_history").upsert(record).execute()

        if res.data:
            return True
        else:
            st.warning("云端上传返回为空，请检查")
            return False

    except Exception as e:
        st.error(f"云端上传失败: {e}")
        return False


def fetch_cloud_history(user_id=None):
    """
    从 Supabase 拉取用户历史数据

    Args:
        user_id: str, 用户唯一标识（默认为当前 session 中的 user_id）

    Returns:
        list: 历史会话记录列表（按时间倒序）
    """
    client = _get_client()
    if client is None:
        return []

    if user_id is None:
        user_id = st.session_state.get("user_id", "anonymous")

    try:
        res = (
            client.table("chat_history")
            .select("*")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)
            .execute()
        )
        return res.data if res.data else []

    except Exception as e:
        st.error(f"云端数据拉取失败: {e}")
        return []


def check_cloud_connection():
    """
    测试 Supabase 连接是否正常

    Returns:
        bool: 连接是否成功
    """
    client = _get_client()
    if client is None:
        return False

    try:
        result = client.table("chat_history").select("count", count="exact").limit(0).execute()
        return result.count is not None
    except Exception:
        return False


def get_cloud_session_summaries(user_id=None):
    """
    获取云端所有历史会话的摘要信息

    Args:
        user_id: str, 用户唯一标识

    Returns:
        list: 摘要列表
    """
    records = fetch_cloud_history(user_id)
    summaries = []
    for record in records:
        session_id = record.get("session_id", "")
        timestamp = record.get("timestamp", "")
        try:
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                display_date = dt.strftime("%Y-%m-%d %H:%M")
            else:
                display_date = session_id.replace("_", " ")
        except:
            display_date = session_id.replace("_", " ")

        summaries.append({
            "session_id": session_id,
            "display_date": display_date,
            "score": record.get("composite_score"),
            "label": record.get("level_name", ""),
            "summary": record.get("summary", ""),
        })
    summaries.reverse()
    return summaries


def get_cloud_trend_data(user_id=None):
    """
    获取云端所有会话的趋势数据

    Args:
        user_id: str, 用户唯一标识

    Returns:
        list: 趋势数据列表
    """
    records = fetch_cloud_history(user_id)
    trends = []
    for record in records:
        timestamp = record.get("timestamp", "")
        try:
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                display_label = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                display_label = record.get("session_id", "").replace("_", " ")
        except:
            display_label = record.get("session_id", "").replace("_", " ")

        trends.append({
            "display_label": display_label,
            "session_id": record.get("session_id", ""),
            "score": record.get("composite_score", 0),
            "label": record.get("level_name", ""),
            "summary": record.get("summary", ""),
        })
    trends.sort(key=lambda x: x["display_label"])
    return trends


def request_user_consent():
    """
    请求用户授权以存储数据到云端

    Returns:
        bool: 用户是否同意
    """
    consent = st.checkbox(
        "我已阅读并同意将我的匿名化数据存储到云端，"
        "用于改善服务质量和学术研究。数据将严格保密。"
    )
    if consent:
        connected = check_cloud_connection()
        if connected:
            st.success("感谢您的授权！云端同步已就绪。")
        else:
            st.warning("已记录您的授权，但当前无法连接到云端服务器。")
    return consent


def sync_local_to_cloud():
    """
    将本地所有未同步的会话数据上传到云端

    Returns:
        tuple: (成功数, 失败数)
    """
    from services.storage_local import get_all_sessions, load_session

    if not st.session_state.get("cloud_consent", False):
        return 0, 0

    sessions = get_all_sessions()
    success = 0
    failed = 0

    for session_id in sessions:
        data = load_session(session_id)
        if data:
            ok = upload_session_to_cloud(session_id, data)
            if ok:
                success += 1
            else:
                failed += 1
    return success, failed
