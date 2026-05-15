
"""
云端存储服务模块（Supabase）
在用户授权同意后，将用户数据同步到云端。
提供数据上传、拉取、连接检测、增量同步、隐私控制等功能。
"""
import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
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


def check_cloud_connection():
    """测试 Supabase 连接是否正常"""
    client = _get_client()
    if client is None:
        return False
    try:
        result = client.table("chat_history").select("count", count="exact").limit(0).execute()
        return result.count is not None
    except Exception:
        return False


# ==========================================
# 云端同步标记存储（用于增量同步）
# ==========================================
SYNC_MARKER_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", ".synced_ids.txt"
)


def _load_synced_ids() -> set:
    """加载已同步的 session_id 集合"""
    if os.path.exists(SYNC_MARKER_FILE):
        with open(SYNC_MARKER_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def _save_synced_ids(ids: set):
    """保存已同步的 session_id 集合"""
    os.makedirs(os.path.dirname(SYNC_MARKER_FILE), exist_ok=True)
    with open(SYNC_MARKER_FILE, "w", encoding="utf-8") as f:
        for sid in sorted(ids):
            f.write(sid + "\n")


# ==========================================
# 上传会话数据到云端
# ==========================================

def upload_session_to_cloud(session_id, data, upload_full_content=True):
    """
    将一次完整会话数据上传到 Supabase 云端

    Args:
        session_id: str, 唯一会话标识
        data: dict, 包含会话数据的字典
        upload_full_content: bool, 是否上传完整聊天内容

    Returns:
        bool: 是否上传成功
    """
    client = _get_client()
    if client is None:
        return False

    try:
        user_id = st.session_state.get("user_id") or st.session_state.get("user_email", "anonymous")

        record = {
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "display_messages": data.get("display_messages", []) if upload_full_content else [],
            "scores": data.get("scores", {}),
            "composite_score": data.get("composite_score", 0),
            "level_name": data.get("level_name", ""),
            "icon": data.get("icon", ""),
            "label": data.get("label", ""),
            "summary": data.get("summary", ""),
            "ai_suggestion": data.get("ai_suggestion", ""),
            "ai_direction": data.get("ai_direction", ""),
            "synced_at": datetime.now().isoformat(),
            "upload_content": upload_full_content,
        }

        res = client.table("chat_history").upsert(record).execute()
        if res.data:
            synced = _load_synced_ids()
            synced.add(session_id)
            _save_synced_ids(synced)
            return True
        return False
    except Exception as e:
        st.error(f"☁️ 云端上传失败: {e}")
        return False


# ==========================================
# 增量同步
# ==========================================

def sync_incremental(upload_full_content=True):
    """
    增量同步：只上传本地新增的、尚未同步过的会话数据

    Returns:
        tuple: (成功数, 失败数)
    """
    from services.storage_local import get_all_sessions, load_session

    if not st.session_state.get("is_logged_in", False):
        return 0, 0

    synced_ids = _load_synced_ids()
    all_sessions = get_all_sessions()
    success = 0
    failed = 0

    for session_id in all_sessions:
        if session_id in synced_ids:
            continue
        data = load_session(session_id)
        if data:
            ok = upload_session_to_cloud(session_id, data, upload_full_content)
            if ok:
                success += 1
            else:
                failed += 1
    return success, failed


# ==========================================
# 从云端拉取用户历史数据
# ==========================================

def fetch_cloud_history(user_id=None):
    """
    从 Supabase 拉取用户历史数据

    Args:
        user_id: str, 用户唯一标识

    Returns:
        list: 历史会话记录列表（按时间倒序）
    """
    client = _get_client()
    if client is None:
        return []

    if user_id is None:
        user_id = st.session_state.get("user_email") or st.session_state.get("user_id", "anonymous")

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
        st.error(f"☁️ 云端数据拉取失败: {e}")
        return []


# ==========================================
# 同步云端数据到本地缓存
# ==========================================

def sync_cloud_to_local():
    """
    从云端拉取用户历史数据并缓存到本地

    Returns:
        int: 保存的记录数
    """
    records = fetch_cloud_history()
    if not records:
        return 0

    from services.storage_local import save_complete_session
    saved = 0
    for record in records:
        session_id = record.get("session_id", "")
        if not session_id:
            continue
        data = {
            "session_id": session_id,
            "user_id": record.get("user_id"),
            "timestamp": record.get("timestamp"),
            "display_messages": record.get("display_messages", []),
            "scores": record.get("scores", {}),
            "composite_score": record.get("composite_score", 0),
            "level_name": record.get("level_name", ""),
            "icon": record.get("icon", ""),
            "label": record.get("label", ""),
            "summary": record.get("summary", ""),
            "ai_suggestion": record.get("ai_suggestion", ""),
            "ai_direction": record.get("ai_direction", ""),
            "from_cloud": True,
        }
        save_complete_session(session_id, data)
        saved += 1
    return saved


# ==========================================
# 云端摘要 & 趋势数据
# ==========================================

def get_cloud_session_summaries(user_id=None):
    """获取云端所有历史会话的摘要信息"""
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
    """获取云端所有会话的趋势数据"""
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


# ==========================================
# 用户授权 & 隐私控制
# ==========================================

def request_user_consent():
    """
    请求用户授权以存储数据到云端
    仅登录用户可见

    Returns:
        bool: 用户是否同意
    """
    if not st.session_state.get("is_logged_in", False):
        return False

    if st.session_state.get("cloud_consent", False):
        return True

    consent = st.checkbox(
        "☁️ 我已阅读并同意将我的匿名化数据存储到云端，"
        "用于改善服务质量和学术研究。数据将严格保密。"
    )
    if consent:
        connected = check_cloud_connection()
        if connected:
            st.success("✅ 感谢您的授权！云端同步已就绪。")
            st.session_state.cloud_consent = True
            success, failed = sync_incremental()
            if success > 0:
                st.info(f"☁️ 已同步 {success} 条历史记录到云端。")
        else:
            st.warning("⚠️ 已记录您的授权，但当前无法连接到云端服务器。")
    return consent


def render_privacy_settings():
    """
    渲染隐私设置 UI（在设置子栏中）
    允许用户选择是否上传聊天内容
    """
    st.markdown(
        '<div style="padding: 0.3rem 0.8rem 0.5rem 0.8rem; font-size: 0.85rem; '
        'color: #6a8aaa; font-weight: 350;">🔐 隐私设置</div>',
        unsafe_allow_html=True
    )

    upload_content = st.checkbox(
        "上传完整聊天内容",
        value=st.session_state.get("upload_full_content", True),
        key="privacy_upload_content",
        help="关闭后，云端仅存储评分和分析结果，不保存对话详细内容"
    )
    st.session_state.upload_full_content = upload_content

    if st.session_state.get("is_logged_in", False):
        st.markdown(
            f'<div style="padding: 0.2rem 0.8rem; font-size: 0.78rem; '
            f'color: #8aabca; font-weight: 300;">'
            f'🔐 当前用户：{st.session_state.get("user_email", "")}</div>',
            unsafe_allow_html=True
        )

    if st.button("🔄 手动同步到云端", use_container_width=True, key="manual_sync_btn"):
        if st.session_state.get("cloud_consent", False):
            success, failed = sync_incremental(st.session_state.get("upload_full_content", True))
            if success > 0 or failed > 0:
                st.info(f"☁️ 同步完成：成功 {success}，失败 {failed}")
            else:
                st.info("☁️ 所有数据已是最新，无需同步。")
        else:
            st.warning("⚠️ 请先在云存储授权中同意数据存储。")

    if st.button("📥 从云端恢复数据", use_container_width=True, key="cloud_restore_btn"):
        with st.spinner("从云端拉取数据..."):
            saved = sync_cloud_to_local()
        st.info(f"☁️ 已从云端恢复 {saved} 条记录到本地缓存。")


def sync_local_to_cloud():
    """批量同步本地全部数据到云端"""
    return sync_incremental(st.session_state.get("upload_full_content", True))
