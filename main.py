import streamlit as st
from config import APP_TITLE, APP_ICON, APP_LAYOUT
from utils.session_manager import init_session_state
from ui.sidebar import render_sidebar
from ui.diary_page import render_diary_page
from ui.chat_page import render_chat_page, process_ai_interaction
from ui.report_page import render_report_page
from ui.history_page import render_history_detail_page
from styles.theme import inject_global_css, render_logo, render_hero
from services.storage_auth import render_login_page
# ==========================================
# 0. 页面配置 & Session 初始化
# ==========================================
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout=APP_LAYOUT)
init_session_state()

# ==========================================
# 0.5 登录/注册页面（优先级最高）
# 用户未登录且未选择跳过时显示
# ==========================================
if not st.session_state.get("is_logged_in", False) and not st.session_state.get("skipped_login", False):
    # 注入全局样式（仅注入样式）
    inject_global_css()
    # 渲染登录页面，返回是否已完成登录流程
    login_done = render_login_page()
    if login_done:
        st.rerun()
    # 登录页面渲染后直接停止，不显示其他内容
    st.stop()

# ==========================================
# 1. 注入全局样式
# ==========================================
inject_global_css()
# ==========================================
# 2. 侧边栏（始终渲染）
# ==========================================
render_sidebar()


# ==========================================
# 3. 主界面路由分发
# ==========================================
# 优先级1：历史记录详情页
if st.session_state.get("viewing_history") and st.session_state.get("selected_session"):
    render_history_detail_page(st.session_state.selected_session)
# 优先级2：评估流程
elif not st.session_state.is_completed:
    # --- 第一阶段：日记 / 对话采集 ---
    is_first_turn = len(st.session_state.display_messages) <= 1

    if is_first_turn:
        # 日记模式（首轮）— 首页内置了 Logo + Hero
        diary_content = render_diary_page()
        if diary_content:
            process_ai_interaction(diary_content)
            st.rerun()
    else:
        # 对话模式（后续多轮）
        render_chat_page()
else:
    # --- 第二阶段：深度解析报告 ---
    render_report_page()
