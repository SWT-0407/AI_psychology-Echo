# # x1 #情绪状态
# # x2 #焦虑与压力
# # x3 #生理状态
# # x4 #行为与动力
# # x5 #社交与支持
# # x6 #认知与意义

"""
大学生心理状态全周期评估系统 - 主入口
======================================
运行方式: streamlit run main.py

模块架构:
├── main.py              # 入口文件，仅做路由分发
├── config.py             # 配置管理
├── models/
│   └── eval_net.py       # ScientificEvalNet 模型
├── utils/
│   ├── prompts.py        # prompt 管理
│   ├── visualization.py  # 可视化（雷达图等）
│   ├── status_assets.py  # 状态资源（emoji、评级等）
│   └── session_manager.py# session 状态管理
├── services/
│   ├── ai_service.py     # AI API 调用
│   ├── storage_local.py  # 本地存储
│   └── storage_cloud.py  # 云端存储（Supabase）
├── ui/
│   ├── sidebar.py        # 侧边栏
│   ├── diary_page.py     # 日记模式页面
│   ├── chat_page.py      # 对话采集页面
│   └── report_page.py    # 深度解析报告页面
└── .env                  # 环境变量（API Key 等）
"""

import streamlit as st
from config import APP_TITLE, APP_ICON, APP_LAYOUT
from utils.session_manager import init_session_state
from ui.sidebar import render_sidebar
from ui.diary_page import render_diary_page
from ui.chat_page import render_chat_page, process_ai_interaction
from ui.report_page import render_report_page
# ==========================================
# 0. 页面配置 & Session 初始化
# ==========================================
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout=APP_LAYOUT)
init_session_state()
# ==========================================
# 1. 侧边栏（始终渲染）
# ==========================================
render_sidebar()


# ==========================================
# 2. 主界面路由分发
# ==========================================
if not st.session_state.is_completed:
    # --- 第一阶段：日记 / 对话采集 ---
    is_first_turn = len(st.session_state.display_messages) <= 1

    if is_first_turn:
        # 日记模式（首轮）
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
