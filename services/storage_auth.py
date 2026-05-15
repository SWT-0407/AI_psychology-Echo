"""
云端用户认证模块（Supabase Auth）
提供登录、注册、退出登录等功能。
"""
import os
import hashlib
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
            return None
        try:
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            return None
    return _supabase_client


def _hash_password(password: str) -> str:
    """对密码进行 SHA-256 哈希"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(email: str, password: str, nickname: str = "") -> bool:
    """
    注册新用户

    Args:
        email: 邮箱
        password: 密码（明文，将哈希后存储）
        nickname: 昵称

    Returns:
        bool: 是否注册成功
    """
    client = _get_client()
    if client is None:
        st.error("无法连接到云端服务器，请检查网络。")
        return False

    if not email or not password:
        st.warning("邮箱和密码不能为空。")
        return False

    if len(password) < 6:
        st.warning("密码长度至少为6位。")
        return False

    try:
        password_hash = _hash_password(password)
        res = client.table("users").insert({
            "email": email,
            "password_hash": password_hash,
            "nickname": nickname,
            "last_login": datetime.now().isoformat()
        }).execute()
        return bool(res.data)
    except Exception as e:
        error_msg = str(e)
        if "duplicate key" in error_msg.lower() or "already exists" in error_msg.lower():
            st.warning("该邮箱已被注册，请直接登录。")
        else:
            st.error(f"注册失败: {e}")
        return False


def login_user(email: str, password: str) -> bool:
    """
    用户登录验证

    Args:
        email: 邮箱
        password: 密码（明文）

    Returns:
        bool: 登录是否成功
    """
    client = _get_client()
    if client is None:
        st.error("无法连接到云端服务器，请检查网络。")
        return False

    if not email or not password:
        st.warning("请输入邮箱和密码。")
        return False

    try:
        password_hash = _hash_password(password)
        res = client.table("users") \
            .select("*") \
            .eq("email", email) \
            .eq("password_hash", password_hash) \
            .limit(1) \
            .execute()

        if res.data and len(res.data) > 0:
            user = res.data[0]
            # 更新最后登录时间
            client.table("users") \
                .update({"last_login": datetime.now().isoformat()}) \
                .eq("id", user["id"]) \
                .execute()
            # 保存用户信息到 session
            st.session_state.user_id = email
            st.session_state.user_email = email
            st.session_state.user_nickname = user.get("nickname", "")
            st.session_state.is_logged_in = True
            return True
        else:
            st.warning("邮箱或密码错误。")
            return False
    except Exception as e:
        st.error(f"登录失败: {e}")
        return False


def logout_user():
    """退出登录，清除用户相关的 session 状态"""
    st.session_state.is_logged_in = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.user_nickname = None
    st.session_state.cloud_consent = False
    # 保留其他状态（如聊天记录、评分等）以免丢失当前会话
    # 但清除历史记录查看状态
    st.session_state.viewing_history = False
    st.session_state.selected_session = None


# ==========================================
# 登录/注册 UI 组件
# ==========================================

def render_login_page():
    """
    渲染登录/注册弹窗界面
    用户可选择登录、注册或跳过（使用本地存储）
    只有当用户未登录时显示

    Returns:
        bool: 用户是否已完成登录流程（登录成功或选择跳过）
    """
    # 如果已经登录，直接返回
    if st.session_state.get("is_logged_in", False):
        return True

    # 如果选择跳过，也不显示
    if st.session_state.get("skipped_login", False):
        return True

    # 使用占位符来渲染登录界面（覆盖主内容区）
    login_placeholder = st.empty()

    with login_placeholder.container():
        # 居中卡片
        col1, col2, col3 = st.columns([1, 2.5, 1])
        with col2:
            st.markdown(
                '<div style="background: rgba(255, 255, 255, 0.85); '
                'backdrop-filter: blur(15px); border: 1px solid rgba(100, 181, 246, 0.15); '
                'border-radius: 24px; padding: 2.5rem 2rem; margin-top: 2rem; '
                'box-shadow: 0 8px 30px rgba(100, 181, 246, 0.08);">',
                unsafe_allow_html=True
            )

            # Logo & 标题
            st.markdown(
                '<div style="text-align: center; margin-bottom: 1.5rem;">'
                '<span style="font-size: 3rem; line-height: 1;">🌱</span>'
                '<h2 style="color: #3a5a7a; font-weight: 300; margin: 0.5rem 0 0.2rem 0;">心聆 · Echo</h2>'
                '<p style="color: #8aabca; font-size: 0.85rem; font-weight: 300; margin: 0;">'
                '大学生心理状态全周期评估系统</p></div>',
                unsafe_allow_html=True
            )

            # Tab 切换：登录 / 注册
            tab_login, tab_register = st.tabs(["🔑 登录", "📝 注册"])

            with tab_login:
                with st.form("login_form", clear_on_submit=False):
                    login_email = st.text_input("邮箱", placeholder="请输入邮箱", key="login_email")
                    login_password = st.text_input(
                        "密码", placeholder="请输入密码", type="password", key="login_password"
                    )
                    col_sub1, col_sub2, _ = st.columns([1, 1, 1])
                    with col_sub1:
                        login_submit = st.form_submit_button("登  录", use_container_width=True)
                    with col_sub2:
                        skip_login = st.form_submit_button("跳过 → 本地使用", use_container_width=True)

                    if login_submit:
                        if login_user(login_email, login_password):
                            # 登录成功，从云端同步数据
                            _sync_cloud_data_on_login(login_email)
                            login_placeholder.empty()
                            st.rerun()
                    if skip_login:
                        st.session_state.skipped_login = True
                        st.session_state.user_id = "local_user"
                        login_placeholder.empty()
                        st.rerun()

            with tab_register:
                with st.form("register_form", clear_on_submit=False):
                    reg_email = st.text_input("邮箱", placeholder="请输入邮箱", key="reg_email")
                    reg_nickname = st.text_input("昵称（选填）", placeholder="给自己取个名字", key="reg_nickname")
                    reg_password = st.text_input(
                        "密码", placeholder="至少6位", type="password", key="reg_password"
                    )
                    reg_password_confirm = st.text_input(
                        "确认密码", placeholder="再次输入密码", type="password", key="reg_password_confirm"
                    )
                    reg_submit = st.form_submit_button("注  册", use_container_width=True)

                    if reg_submit:
                        if reg_password != reg_password_confirm:
                            st.warning("两次输入的密码不一致。")
                        elif register_user(reg_email, reg_password, reg_nickname):
                            st.success("注册成功！请切换到登录页面进行登录。")
                        # 注册成功后不清空，让用户手动切换到登录页

            st.markdown(
                '<div style="text-align: center; margin-top: 1rem; font-size: 0.75rem; '
                'color: #b0c8e0; font-weight: 300;">'
                '数据将加密存储，仅用于本次评估服务</div>',
                unsafe_allow_html=True
            )

            st.markdown('</div>', unsafe_allow_html=True)

    return False


def _sync_cloud_data_on_login(email: str):
    """
    登录后从云端同步用户数据到本地缓存

    Args:
        email: 用户邮箱（作为 user_id）
    """
    try:
        from services.storage_cloud import fetch_cloud_history
        records = fetch_cloud_history(email)
        # 连接状态已就绪
        st.session_state.cloud_consent = True
        st.success(f"✅ 欢迎回来！已从云端同步 {len(records)} 条历史记录。")
    except Exception:
        # 同步失败不影响登录
        pass


def render_user_status():
    """
    在侧边栏渲染当前登录状态
    显示用户邮箱和退出按钮
    """
    if st.session_state.get("is_logged_in", False):
        email = st.session_state.get("user_email", "")
        st.markdown(
            f'<div style="display: flex; align-items: center; gap: 6px; padding: 0.3rem 0.8rem;">'
            f'<span style="color: #a5d6a7; font-size: 0.8rem;">🔒</span>'
            f'<span style="color: #8aabca; font-size: 0.78rem; font-weight: 300;">{email}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        if st.button("🚪 退出登录", key="logout_btn", use_container_width=True):
            logout_user()
            st.rerun()
    elif not st.session_state.get("skipped_login", False):
        # 未登录且不是跳过状态
        pass
    else:
        # 跳过登录，本地模式
        st.markdown(
            '<div style="display: flex; align-items: center; gap: 6px; padding: 0.3rem 0.8rem;">'
            '<span style="color: #ffe082; font-size: 0.8rem;">📁</span>'
            '<span style="color: #8aabca; font-size: 0.78rem; font-weight: 300;">本地模式</span>'
            '</div>',
            unsafe_allow_html=True
        )
