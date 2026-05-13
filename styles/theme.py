"""
统一主题样式模块
提供全局 CSS 注入、颜色常量、公共容器组件。
"""

# ==========================================
# 色板定义
# ==========================================
PRIMARY_BLUE = "#64b5f6"
MIST_WHITE = "#f8fbff"
LIGHT_BLUE_GRAY = "#d9e7f5"
SOFT_GREEN = "#a5d6a7"
DEEP_BLUE = "#4a90d9"

# 心理状态颜色（柔和版）
STATUS_COLORS = {
    85: "#81c784",  # 柔和绿
    70: "#64b5f6",  # 疗愈蓝
    55: "#ffb74d",  # 暖橙
    40: "#e57373",  # 柔红
    0: "#ba68c8",   # 淡紫
}

# ==========================================
# CSS 全局样式
# ==========================================
GLOBAL_CSS = """
<style>
    /* ===== 全局基础样式 ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', 'HarmonyOS Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }

    /* 主内容区 */
    .stApp {
        background: linear-gradient(135deg, #f8fbff 0%, #eef4fb 100%);
    }

    /* 主区块容器 - 移除默认padding，改用自定义 */
    .main > .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }

    /* ===== 标题 & 文字 ===== */
    h1, h2, h3 {
        font-weight: 400 !important;
        letter-spacing: 0.02em;
    }

    h1 {
        color: #3a5a7a !important;
        font-size: 2.2rem !important;
    }

    h2 {
        color: #4a6a8a !important;
        font-size: 1.5rem !important;
    }

    h3 {
        color: #5a7a9a !important;
        font-size: 1.2rem !important;
    }

    p, li, .stMarkdown {
        color: #4a5a6a !important;
        line-height: 1.7 !important;
    }

    /* ===== 卡片容器 ===== */
    div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div.stContainer,
    div[data-testid="stVerticalBlockBorderBox"] {
        background: rgba(255, 255, 255, 0.75) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(100, 181, 246, 0.15) !important;
        border-radius: 20px !important;
        padding: 1.5rem !important;
        box-shadow: 0 4px 20px rgba(100, 181, 246, 0.08),
                    0 1px 3px rgba(100, 181, 246, 0.05) !important;
        transition: all 0.3s ease !important;
    }

    div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div.stContainer:hover {
        box-shadow: 0 8px 30px rgba(100, 181, 246, 0.12) !important;
        transform: translateY(-1px);
    }

    /* ===== 聊天气泡 ===== */
    /* AI 消息气泡 */
    div[data-testid="chatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background: linear-gradient(135deg, rgba(100, 181, 246, 0.08), rgba(165, 214, 167, 0.05)) !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 0.8rem 1.2rem !important;
        margin: 0.8rem 2rem 0.8rem 0 !important;
        border: 1px solid rgba(100, 181, 246, 0.1) !important;
        backdrop-filter: blur(5px) !important;
    }

    /* 用户消息气泡 */
    div[data-testid="chatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background: rgba(255, 255, 255, 0.9) !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 0.8rem 1.2rem !important;
        margin: 0.8rem 0 0.8rem 2rem !important;
        border: 1px solid rgba(100, 181, 246, 0.08) !important;
        box-shadow: 0 2px 12px rgba(100, 181, 246, 0.06) !important;
    }

    /* ===== 聊天输入框 ===== */
    div[data-testid="stChatInput"] {
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(100, 181, 246, 0.2) !important;
        border-radius: 24px !important;
        padding: 0.3rem 0.3rem 0.3rem 1.2rem !important;
        box-shadow: 0 2px 20px rgba(100, 181, 246, 0.08),
                    0 0 0 1px rgba(100, 181, 246, 0.05) !important;
        transition: all 0.3s ease !important;
    }

    div[data-testid="stChatInput"]:focus-within {
        box-shadow: 0 2px 25px rgba(100, 181, 246, 0.15),
                    0 0 0 2px rgba(100, 181, 246, 0.1) !important;
        border-color: rgba(100, 181, 246, 0.3) !important;
    }

    div[data-testid="stChatInput"] input {
        font-size: 0.95rem !important;
        color: #3a5a7a !important;
    }

    div[data-testid="stChatInput"] input::placeholder {
        color: #a0b8d0 !important;
        font-weight: 300 !important;
    }

    /* ===== 侧边栏 ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(248, 251, 255, 0.95), rgba(217, 231, 245, 0.3)) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border-right: 1px solid rgba(100, 181, 246, 0.1) !important;
    }

    section[data-testid="stSidebar"] .stMarkdown {
        color: #4a6a8a !important;
    }

    /* 侧边栏分隔线 */
    section[data-testid="stSidebar"] hr {
        border-color: rgba(100, 181, 246, 0.1) !important;
        margin: 1rem 0 !important;
    }

    /* ===== 按钮 ===== */
    .stButton > button {
        background: rgba(100, 181, 246, 0.1) !important;
        color: #4a7a9a !important;
        border: 1px solid rgba(100, 181, 246, 0.15) !important;
        border-radius: 14px !important;
        padding: 0.4rem 1.2rem !important;
        font-weight: 400 !important;
        font-size: 0.9rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(5px) !important;
    }

    .stButton > button:hover {
        background: rgba(100, 181, 246, 0.2) !important;
        border-color: rgba(100, 181, 246, 0.3) !important;
        box-shadow: 0 4px 15px rgba(100, 181, 246, 0.15) !important;
        transform: translateY(-1px);
    }

    /* ===== Progress Bar ===== */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #a5d6a7, #64b5f6) !important;
        border-radius: 10px !important;
    }

    /* ===== 信息/成功/警告框 ===== */
    div[data-testid="stInfoBox"],
    div[data-testid="stSuccessBox"],
    div[data-testid="stWarningBox"] {
        background: rgba(100, 181, 246, 0.06) !important;
        border: 1px solid rgba(100, 181, 246, 0.1) !important;
        border-radius: 16px !important;
        padding: 0.8rem 1.2rem !important;
    }

    div[data-testid="stInfoBox"] {
        border-left: 3px solid #64b5f6 !important;
    }

    div[data-testid="stSuccessBox"] {
        border-left: 3px solid #a5d6a7 !important;
    }

    div[data-testid="stWarningBox"] {
        border-left: 3px solid #ffb74d !important;
    }

    /* ===== Metric ===== */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.5) !important;
        border-radius: 16px !important;
        padding: 0.5rem 1rem !important;
        border: 1px solid rgba(100, 181, 246, 0.05) !important;
    }

    div[data-testid="stMetric"] label {
        color: #6a8aaa !important;
        font-weight: 400 !important;
    }

    div[data-testid="stMetric"] > div {
        color: #3a5a7a !important;
    }

    /* ===== Spinner ===== */
    .stSpinner > div {
        border-color: #64b5f6 !important;
        border-top-color: transparent !important;
    }

    /* ===== Tab 样式 ===== */
    button[data-testid="stTab"] {
        background: transparent !important;
        border: none !important;
        color: #6a8aaa !important;
        font-weight: 400 !important;
        border-radius: 12px !important;
        padding: 0.4rem 1rem !important;
        transition: all 0.2s ease !important;
    }

    button[data-testid="stTab"]:hover {
        background: rgba(100, 181, 246, 0.08) !important;
    }

    button[data-testid="stTab"][aria-selected="true"] {
        background: rgba(100, 181, 246, 0.12) !important;
        color: #4a7a9a !important;
    }

    /* ===== Text Area ===== */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.6) !important;
        border: 1px solid rgba(100, 181, 246, 0.12) !important;
        border-radius: 18px !important;
        padding: 1rem !important;
        font-size: 0.95rem !important;
        line-height: 1.7 !important;
        color: #3a5a7a !important;
        transition: all 0.3s ease !important;
    }

    .stTextArea textarea:focus {
        border-color: rgba(100, 181, 246, 0.3) !important;
        box-shadow: 0 0 0 2px rgba(100, 181, 246, 0.08) !important;
    }

    .stTextArea textarea::placeholder {
        color: #a0b8d0 !important;
        font-weight: 300 !important;
    }

    /* ===== Checkbox ===== */
    .stCheckbox label {
        color: #5a7a9a !important;
    }

    /* ===== 标题横幅样式 ===== */
    .hero-title {
        font-size: 2.5rem !important;
        font-weight: 300 !important;
        color: #3a5a7a !important;
        line-height: 1.3 !important;
        letter-spacing: 0.02em !important;
        text-align: center !important;
        margin: 2rem 0 0.8rem 0 !important;
    }

    .hero-subtitle {
        font-size: 1rem !important;
        font-weight: 300 !important;
        color: #7a9aba !important;
        line-height: 1.8 !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
        max-width: 600px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* ===== Logo 区域 ===== */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0.5rem 0;
    }

    .logo-icon {
        font-size: 2rem;
        line-height: 1;
    }

    .logo-text {
        font-size: 1.2rem;
        font-weight: 400;
        color: #4a6a8a;
        letter-spacing: 0.05em;
    }

    /* ===== 日记模式卡片 ===== */
    .diary-card {
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(100, 181, 246, 0.12) !important;
        border-radius: 24px !important;
        padding: 2rem !important;
        box-shadow: 0 4px 25px rgba(100, 181, 246, 0.06) !important;
    }

    .diary-date {
        font-size: 0.95rem;
        color: #6a8aaa;
        font-weight: 400;
        letter-spacing: 0.03em;
    }

    /* ===== 分隔线 ===== */
    hr {
        border-color: rgba(100, 181, 246, 0.08) !important;
        margin: 1.5rem 0 !important;
    }

    /* ===== 雷达图等图片容器 ===== */
    div[data-testid="stImage"] img {
        border-radius: 16px !important;
        box-shadow: 0 2px 15px rgba(100, 181, 246, 0.06) !important;
    }

    /* ===== 情绪标签 ===== */
    .emotion-tag {
        display: inline-block;
        background: rgba(100, 181, 246, 0.1);
        color: #4a7a9a;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        border: 1px solid rgba(100, 181, 246, 0.1);
        margin: 0.15rem;
    }

    /* ===== 综合评分卡片 ===== */
    .score-card {
        text-align: center;
        padding: 1.5rem;
    }

    .score-emoji {
        font-size: 4rem;
        line-height: 1;
        margin-bottom: 0.5rem;
    }

    .score-value {
        font-size: 2.5rem;
        font-weight: 300;
        color: #3a5a7a;
        line-height: 1.2;
    }

    .score-label {
        font-size: 0.9rem;
        color: #8aabca;
        font-weight: 300;
    }

    .score-level {
        font-size: 0.95rem;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin-top: 0.5rem;
    }

    /* ===== 建议卡片 ===== */
    .tip-card {
        background: linear-gradient(135deg, rgba(100, 181, 246, 0.05), rgba(165, 214, 167, 0.05));
        border: 1px solid rgba(100, 181, 246, 0.08);
        border-radius: 16px;
        padding: 0.8rem 1.2rem;
        margin-top: 1rem;
        color: #6a8aaa;
        font-size: 0.9rem;
        font-weight: 300;
    }

    /* ===== 流式输出动画 ===== */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(8px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    div[data-testid="chatMessage"] {
        animation: fadeInUp 0.4s ease-out;
    }

    /* ===== 呼吸感动画（用于装饰） ===== */
    @keyframes breathe {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }

    .breathe {
        animation: breathe 4s ease-in-out infinite;
    }

    /* ===== 响应式调整 ===== */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 1.6rem !important;
        }
        .hero-subtitle {
            font-size: 0.9rem !important;
        }
    }

    /* ===== 隐藏 Streamlit 默认水印 ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ===== 聊天消息内容样式 ===== */
    .chat-message-content {
        line-height: 1.7;
        color: #4a5a6a;
    }

    /* ===== 历史记录子栏 ===== */
    .history-subitem {
        padding: 0.25rem 0.8rem 0.25rem 1.8rem;
        border-radius: 10px;
        transition: all 0.2s ease;
        font-size: 0.82rem;
        color: #7a9aba;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 2px solid transparent;
    }

    .history-subitem:hover {
        background: rgba(100, 181, 246, 0.05);
        border-left-color: rgba(100, 181, 246, 0.3);
    }

    .history-subitem.selected {
        background: rgba(100, 181, 246, 0.08);
        border-left-color: #64b5f6;
        color: #4a6a8a;
    }

    /* ===== 聊天气泡在历史记录中的滚动容器 ===== */
    .history-chat-scroll {
        max-height: 350px;
        overflow-y: auto;
        padding: 0.5rem;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.3);
    }

    .history-chat-scroll::-webkit-scrollbar {
        width: 3px;
    }

    .history-chat-scroll::-webkit-scrollbar-thumb {
        background: rgba(100, 181, 246, 0.1);
        border-radius: 10px;
    }

    /* ===== 历史返回按钮 ===== */
    .back-button {
        background: rgba(100, 181, 246, 0.05);
        border: 1px solid rgba(100, 181, 246, 0.1);
        border-radius: 12px;
        padding: 0.3rem 0.8rem;
        color: #5a7a9a;
        font-size: 0.82rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .back-button:hover {
        background: rgba(100, 181, 246, 0.1);
    }

    /* ===== checkbox 样式优化（用于侧边栏展开/收起） ===== */
    .stCheckbox {
        gap: 6px !important;
    }
</style>
"""


def inject_global_css():
    """注入全局 CSS 样式到 Streamlit 应用"""
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def render_logo():
    """渲染左上角 Logo"""
    import streamlit as st
    st.markdown(
        """
        <div class="logo-container">
            <span class="logo-icon">🌱</span>
            <span class="logo-text">心聆·Echo</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_hero():
    """渲染首页中央标题区"""
    import streamlit as st
    st.markdown(
        """
        <div class="hero-title">你的情绪，值得被认真倾听</div>
        <div class="hero-subtitle">
            在这里，你不需要填写冰冷的问卷，<br>
            只需要像和朋友聊天一样，慢慢说出最近的状态。
        </div>
        """,
        unsafe_allow_html=True
    )
