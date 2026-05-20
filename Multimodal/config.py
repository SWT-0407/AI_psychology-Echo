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
QWEN_TTS_MODEL = "cosyvoice-v3-plus"       # 语音合成（HTTP模式）
QWEN_TTS_VOICE = "longxiaochun"            # 音色：longxiaochun（知性女声）

# ==========================================
# 面部情绪分析配置（精细化维度模型）
# ==========================================

# 情绪分析 prompt 模板
# {face_scale_desc} 会被替换为维度量表描述
EMOTION_ANALYSIS_PROMPT = (
    "你是一位专业的面部情绪分析专家。请分析这张照片中人物的面部微表情和整体情绪状态。\n\n"
    "请严格按照以下量表进行评分（0.0~1.0，保留两位小数）：\n"
    "{face_scale_desc}\n\n"
    "同时给出一个主情绪标签（从以下选择）："
    "happy开心, sad悲伤, angry生气, surprised惊讶, fearful恐惧, disgusted厌恶, "
    "neutral中性/平静, contempt轻蔑, anxious焦虑, tired疲惫\n\n"
    "请只返回JSON格式：\n"
    "{{\"emotion\": \"标签英文\", \"emotion_cn\": \"标签中文\", "
    "\"valence\": 0.0, \"arousal\": 0.0, "
    "\"dominance\": 0.0, \"anxiety\": 0.0, \"fatigue\": 0.0, \"engagement\": 0.0, "
    "\"analysis\": \"10字内描述\"}}"
)

# 情绪维度量表定义（每个维度名称、含义、映射到哪个心理评估维度）
# key: 返回的字段名
# label: 显示名称
# desc: 给 AI 的量表描述（0~1）
# mapping: 映射到心理评估维度（None 表示不直接映射）
FACE_EMOTION_DIMENSIONS = {
    "valence": {
        "label": "愉悦度",
        "desc": "0=极度痛苦/悲伤/愤怒, 0.3=轻微负面, 0.5=中性, 0.7=轻微积极, 1.0=极度开心/愉悦",
        "mapping": "x1",       # → 情绪状态
        "min": 0.0, "max": 1.0
    },
    "arousal": {
        "label": "唤醒度",
        "desc": "0=昏昏欲睡/无精打采, 0.3=放松/平静, 0.5=适度警觉, 0.7=紧张/兴奋, 1.0=极度激动/恐慌",
        "mapping": None,       # 辅助维度
        "min": 0.0, "max": 1.0
    },
    "dominance": {
        "label": "支配度",
        "desc": "0=完全无力/被控制/退缩, 0.3=顺从/犹豫, 0.5=中性, 0.7=自信/掌控, 1.0=主导/强势",
        "mapping": "x4",       # → 行为与动力
        "min": 0.0, "max": 1.0
    },
    "anxiety": {
        "label": "焦虑度",
        "desc": "0=完全放松无焦虑, 0.3=轻微不安, 0.5=中度焦虑, 0.7=明显焦虑, 1.0=极度惊恐/恐慌",
        "mapping": "x2",       # → 焦虑控制力（反向）
        "min": 0.0, "max": 1.0
    },
    "fatigue": {
        "label": "疲劳度",
        "desc": "0=精力充沛/精神饱满, 0.3=轻微疲惫, 0.5=中度疲劳, 0.7=明显疲惫, 1.0=精疲力竭",
        "mapping": "x3",       # → 生理状态（反向）
        "min": 0.0, "max": 1.0
    },
    "engagement": {
        "label": "参与度",
        "desc": "0=完全回避/封闭/退缩, 0.3=轻微回避/不自在, 0.5=中性/礼貌性参与, 0.7=愿意互动, 1.0=积极开放/主动投入",
        "mapping": "x5",       # → 社交与支持
        "min": 0.0, "max": 1.0
    }
}

# 构建完整的维度量表描述文本（供 prompt 使用）
def build_face_scale_description():
    """根据 FACE_EMOTION_DIMENSIONS 自动生成量表描述"""
    lines = []
    for i, (key, dim) in enumerate(FACE_EMOTION_DIMENSIONS.items(), 1):
        lines.append(f"{i}. {dim['label']}（{key}）：{dim['desc']}")
    return "\n".join(lines)

# 情绪分析 API 参数
EMOTION_ANALYSIS_TEMPERATURE = 0.1
EMOTION_ANALYSIS_MAX_TOKENS = 300

# 摄像头识别间隔（秒）
EMOTION_DETECT_INTERVAL = 3.0

# 情绪维度 → 心理评估维度 映射函数
def face_vector_to_scores(face_vector):
    """
    将面部情绪维度向量映射到心理评估 x1~x6 评分（0~10分）

    Args:
        face_vector: dict, 来自 analyze_facial_expression() 的返回值
                    包含 valence, arousal, dominance, anxiety, fatigue, engagement

    Returns:
        dict: {"x1": 0~10, "x2": 0~10, ...}，None 的维度表示无有效数据
    """
    scores = {k: None for k in DIMENSION_KEYS}

    for key, val in face_vector.items():
        dim_info = FACE_EMOTION_DIMENSIONS.get(key)
        if dim_info is None:
            continue
        target = dim_info.get("mapping")
        if target is None or target not in scores:
            continue

        raw = float(val)

        # 反向映射的维度（值越低表示越健康 → 得分越高）
        if target in ("x2", "x3"):   # 焦虑控制力、生理状态是反向的
            score = round((1.0 - raw) * 10)
        else:
            score = round(raw * 10)

        # 钳制到 0~10
        scores[target] = max(0, min(10, score))

    # x6（认知与意义）由 valence + dominance 综合得出
    v = float(face_vector.get("valence", 0.5))
    d = float(face_vector.get("dominance", 0.5))
    scores["x6"] = max(0, min(10, round((v + d) * 5)))

    return scores

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