import streamlit as st
import json
import random
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
import re

load_dotenv()

# API
client = OpenAI(
    api_key="sk-9286a96bcfc746dfa32d41bb19a093ac",
    base_url="https://api.deepseek.com"
)

st.set_page_config(page_title="AI 心理陪伴助手", layout="wide")

# ---------- 初始化 session_state ----------
defaults = {
    "step": "questionnaire",
    "responses": {},
    "final_score": 0,
    "conversation_history": [],
    "emotion_timeline": [],
    "conversation_started": False,
    "turn_count": 0,
    "api_key_manual": "",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------- 9 维度定义（评分0-4） ----------
DIMENSIONS = [
    {"name": "情绪低落", "weight": 15},
    {"name": "焦虑紧张", "weight": 10},
    {"name": "学业压力", "weight": 10},
    {"name": "社交与人际关系", "weight": 12},
    {"name": "睡眠问题", "weight": 8},
    {"name": "精力与动力", "weight": 10},
    {"name": "自我价值感", "weight": 12},
    {"name": "未来与意义感", "weight": 13},
    {"name": "外部连接与支持", "weight": 10},
]
SCORE_OPTIONS = ["0 - 完全没有", "1 - 很少/轻微", "2 - 有时/中度", "3 - 经常/较重", "4 - 总是/严重"]
SCORE_MAP = {opt: i for i, opt in enumerate(SCORE_OPTIONS)}

# ---------- 辅助函数 ----------
def compute_questionnaire_score():
    weighted_sum = 0
    for dim in DIMENSIONS:
        name = dim["name"]
        weight = dim["weight"]
        score = SCORE_MAP[st.session_state.responses.get(name, "0 - 完全没有")]
        weighted_sum += score * weight
    return round((weighted_sum / 400.0) * 100, 1)

def get_high_risk_dimensions():
    high = []
    for dim in DIMENSIONS:
        name = dim["name"]
        score = SCORE_MAP[st.session_state.responses.get(name, "0 - 完全没有")]
        if score >= 3:
            high.append((name, score))
    return high

def call_llm(system_prompt, user_prompt, temperature=0.7):
    """调用大模型 API，兼容 OpenAI 和 DeepSeek"""
    # 尝试从环境变量或手动输入获取 client
    global client
    if client is None:
        if st.session_state.api_key_manual:
            client = OpenAI(api_key=st.session_state.api_key_manual)
            # 如果用户输入的是 deepseek key，自动切换 base_url
            if "deepseek" in st.session_state.api_key_manual.lower():
                client.base_url = "https://api.deepseek.com"
        else:
            return "❌ 请在侧边栏输入 API Key"

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"API 调用失败：{e}")
        return "我暂时无法回应，请稍后再试。"

def analyze_emotion_and_generate_response(user_input, history, questionnaire_score, high_dims):
    """使用大模型分析情感强度并生成共情回应"""
    history_str = ""
    for h in history[-6:]:
        history_str += f"用户：{h[0]}\n助手：{h[1]}\n"

    system_prompt = """你是一位温暖、专业的大学生心理陪伴助手。你的任务：
1. 分析用户输入的情感强度（负面/正面），给出0-100的分数（0=极度负面，100=极度正面）。
2. 生成一段共情、鼓励的回应，语气自然、真诚，适当提问引导深入交流。
3. 如果用户表达自伤/自杀念头，必须优先强调“请立即联系心理援助热线”，并给予关怀。
4. 输出格式必须为 JSON：{"score": 整数, "response": "你的回应内容"}"""

    user_prompt = f"""用户问卷总分（0-100）：{questionnaire_score}，高分困扰维度：{high_dims}。
对话历史：
{history_str}
用户当前输入：{user_input}
请输出 JSON。"""

    result = call_llm(system_prompt, user_prompt, temperature=0.7)
    try:
        # 提取 JSON 部分（处理可能的前后文字）
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("score", 50), data.get("response", result)
        else:
            return 50, result
    except:
        return 50, result

# ---------- 侧边栏：API 设置与状态 ----------
with st.sidebar:
    st.header("⚙️ 设置")
    if not client:
        st.session_state.api_key_manual = st.text_input(
            "输入 OpenAI 或 DeepSeek API Key",
            type="password",
            value=st.session_state.api_key_manual
        )
        if st.session_state.api_key_manual:
            st.success("API Key 已加载")
    else:
        st.success("API 已就绪 (环境变量)")

    st.divider()
    if st.session_state.step == "chat":
        st.subheader("📊 当前状态")
        st.metric("问卷总分", f"{st.session_state.final_score}/100")
        high = get_high_risk_dimensions()
        if high:
            st.warning(f"⚠️ 较高风险维度：{', '.join([h[0] for h in high])}")
        st.divider()
        st.subheader("📈 情感波动趋势")
        if st.session_state.emotion_timeline:
            chart_data = {
                "时间": [t[0] for t in st.session_state.emotion_timeline],
                "情感分数": [t[1] for t in st.session_state.emotion_timeline]
            }
            st.line_chart(chart_data, x="时间", y="情感分数")

# ---------- 主界面 ----------
st.title("🧠 大学生心理陪伴助手")
st.markdown("本工具仅供自我觉察与情绪舒缓，**不能替代专业心理咨询**。如需帮助，请勇敢求助。")

# --- 阶段一：问卷 ---
if st.session_state.step == "questionnaire":
    st.header("📋 情绪状态自评（请根据过去两周情况作答）")
    with st.form("questionnaire_form"):
        for dim in DIMENSIONS:
            name = dim["name"]
            st.session_state.responses[name] = st.radio(
                f"**{name}**",
                SCORE_OPTIONS,
                index=0,
                key=f"q_{name}",
                horizontal=True
            )
        submitted = st.form_submit_button("提交并进入对话")
        if submitted:
            st.session_state.final_score = compute_questionnaire_score()
            st.session_state.step = "chat"
            st.session_state.conversation_started = False
            st.rerun()

# --- 阶段二：对话 ---
elif st.session_state.step == "chat":
    # 显示欢迎语（仅一次）
    if not st.session_state.conversation_started:
        high = get_high_risk_dimensions()
        welcome_msg = f"你好，我已经了解你最近的整体状态（自评得分 {st.session_state.final_score}）。"
        if high:
            welcome_msg += f" 我注意到你在 {', '.join([h[0] for h in high])} 方面困扰较多。"
        welcome_msg += " 愿意和我多聊聊吗？我会用心倾听。"
        st.session_state.conversation_history.append(("assistant", welcome_msg))
        st.session_state.conversation_started = True

    # 展示对话历史
    chat_container = st.container()
    with chat_container:
        for role, msg in st.session_state.conversation_history:
            if role == "user":
                st.chat_message("user").write(msg)
            else:
                st.chat_message("assistant").write(msg)

    # 输入框
    user_input = st.chat_input("在这里输入你想说的话...")
    if user_input:
        st.session_state.conversation_history.append(("user", user_input))
        st.session_state.turn_count += 1

        with st.spinner("思考中..."):
            high_dims = get_high_risk_dimensions()
            emotion_score, response = analyze_emotion_and_generate_response(
                user_input,
                st.session_state.conversation_history,
                st.session_state.final_score,
                high_dims
            )
            # 记录情感分数
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.emotion_timeline.append((timestamp, emotion_score))
            # 保存助手回复
            st.session_state.conversation_history.append(("assistant", response))

        st.rerun()

    # 重置按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 重新填写问卷"):
            for key in ["step", "responses", "final_score", "conversation_history",
                        "emotion_timeline", "conversation_started", "turn_count"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    with col2:
        if st.button("💾 导出对话记录"):
            export = {
                "timestamp": datetime.now().isoformat(),
                "final_score": st.session_state.final_score,
                "conversation": st.session_state.conversation_history,
                "emotion_timeline": st.session_state.emotion_timeline
            }
            st.download_button(
                "下载 JSON",
                data=json.dumps(export, ensure_ascii=False, indent=2),
                file_name="mental_chat_log.json"
            )
