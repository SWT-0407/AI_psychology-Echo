import streamlit as st

from services.app_storage import init_runtime_state
from services.storage_auth import render_login_page
from ui.companion_page import render_companion_page
from ui.diary_chat_page import render_psytest_diary
from ui.home_page import render_home_page
from ui.profile_page import render_profile_page
from ui.treehole_page import render_treehole_page


st.set_page_config(
    page_title="心语 Echo",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 隐藏 Streamlit 自带顶栏、菜单、Deploy 按钮和页脚
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { margin-top: -3rem; }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

init_runtime_state()

if not st.session_state.get("is_logged_in", False) and not st.session_state.get("skipped_login", False):
    login_done = render_login_page()
    if login_done:
        st.rerun()
    st.stop()

page = st.session_state.get("page", "home")

if page == "psytest":
    render_psytest_diary()
elif page == "treehole":
    render_treehole_page()
elif page == "companion":
    render_companion_page()
elif page == "profile":
    render_profile_page()
else:
    render_home_page()
