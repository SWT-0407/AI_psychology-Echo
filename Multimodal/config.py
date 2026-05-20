"""
配置管理模块
集中管理所有配置信息，包括 API key、维度定义、模型参数等。
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# API 配置 - DeepSeek（语言对话）
# ==========================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL_NAME = "deepseek-chat"

# ==========================================
# API 配置 - 千问（通义，多模态视觉/语音）
# ==========================================
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_VISION_MODEL = "qwen-vl-max"         # 视觉理解，也可以用 qwen3.6-plus
QWEN_ASR_MODEL = "qwen3-asr-flash"        # 语音识别（OpenAI兼容HTTP模式）
QWEN_TTS_MODEL = "cosyvoice-v3-plus"        # 语音合成（HTTP模式，CosyVoice效果更好）
QWEN_TTS_VOICE = "longxiaochun"              # 音色：longxiaochun（知性女声）

# ==========================================
# 维度定义
# ==========================================
DIMENSIONS = {
    "x1": "情绪状态",
    "x2": "焦虑控制力",
    "x3": "生理状态",
    "x4": "行为与动力",
    "x5": "社交与支持",
    "x6": "认知与意义"
}

DIMENSION_KEYS = ["x1", "x2", "x3", "x4", "x5", "x6"]

# ==========================================
# 模型权重配置
# ==========================================
# 权重映射：情绪0.15, 焦虑0.15, 生理0.10, 动力0.15, 社交0.20, 意义0.25
EXPERT_WEIGHTS = [0.15, 0.15, 0.10, 0.15, 0.20, 0.25]

# ==========================================
# 应用配置
# ==========================================
APP_TITLE = "心聆·Echo - 大学生心理状态全周期评估系统"
APP_ICON = "🌱"
APP_LAYOUT = "wide"

# 综合评分满分
MAX_SCORE = 100

