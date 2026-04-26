import streamlit as st
from openai import OpenAI
import json
import re
import torch
import torch.nn as nn
import requests
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import random


# ==========================================
# 1. 核心模型定义 (ScientificEvalNet)
# ==========================================
class ScientificEvalNet(nn.Module):
    def __init__(self):
        super(ScientificEvalNet, self).__init__()
        self.fc = nn.Linear(6, 1, bias=False)
        # 权重映射：情绪0.15, 焦虑0.15, 生理0.10, 动力0.15, 社交0.20, 意义0.25
        expert_weights = torch.tensor([[0.15, 0.15, 0.10, 0.15, 0.20, 0.25]])
        with torch.no_grad():
            self.fc.weight.copy_(expert_weights)

    def forward(self, x):
        weights = torch.abs(self.fc.weight)
        normalized_weights = weights / weights.sum()
        score = torch.matmul(x, normalized_weights.t()) * 10
        return score


@st.cache_resource
def get_model():
    return ScientificEvalNet()


# ==========================================
# 2. 页面配置与 Session 初始化
# ==========================================
st.set_page_config(page_title="大学生心理状态全周期评估系统", page_icon="🌱", layout="wide")

# 中文字体处理（雷达图显示中文）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

if "messages" not in st.session_state:
    st.session_state.messages = []
if "display_messages" not in st.session_state:
    st.session_state.display_messages = [{"role": "assistant",
                                          "content": "你好！我是你的专属树洞助手。最近在学习和生活上感觉怎么样？有什么想跟我吐槽的吗？"}]
if "scores" not in st.session_state:
    st.session_state.scores = {"x1": None, "x2": None, "x3": None, "x4": None, "x5": None, "x6": None}
if "is_completed" not in st.session_state:
    st.session_state.is_completed = False
if 'history' not in st.session_state:
    st.session_state.history = []

# 配置信息
MY_API_KEY = "sk-9286a96bcfc746dfa32d41bb19a093ac"
DIMENSIONS = {
    "x1": "情绪状态", "x2": "焦虑与压力", "x3": "生理状态",
    "x4": "行为与动力", "x5": "社交与支持", "x6": "认知与意义"
}


# ==========================================
# 3. 功能函数：动态资源与 Prompt
# ==========================================
def get_status_assets(score, vals):
    """根据分数返回对应的 Emoji、评级、颜色和 AI 创作人设方向"""
    x3_physic = vals[2]
    if score >= 85:
        icon = random.choice(["🚀", "🔥", "⚡", "🤩", "🌈"])
        level, color = "能量迸发", "#28a745"
        direction = "人设：热血领路学长。方向：极致肯定，鼓励能量传承，文风燃且利落。"
    elif score >= 70:
        icon = random.choice(["☀️", "🌿", "😊", "✅", "🎈"])
        level, color = "稳健前行", "#17a2b8"
        direction = "人设：温和治愈系好友。方向：认可现状，提供平衡生活的智慧，文风温暖。"
    elif score >= 55:
        icon = random.choice(["🍃", "☕", "🌤️", "🌊", "🛋️"])
        level, color = "微风荡漾", "#ffc107"
        direction = "人设：懂生活的疗愈博主。方向：引导去内耗，建议‘精神断舍离’，文风细腻。"
    elif score >= 40:
        icon = "🪫" if x3_physic < 4.5 else random.choice(["🌧️", "😮‍💨", "🩹", "🌫️", "🧊"])
        level, color = "蓄势待发", "#fd7e14"
        direction = "人设：深夜电台主播。方向：允许停顿与崩溃，深度共情疲惫，文风极其温柔。"
    else:
        icon = random.choice(["🚨", "🆘", "☔", "💔", "🥀"])
        level, color = "静候天晴", "#dc3545"
        direction = "人设：专业的心理守护者。方向：无条件接纳，紧急安抚，强调保护核心自我，文风坚定有力。"
    return icon, level, color, direction


# ==========================================
# 4. 侧边栏：状态监控
# ==========================================
with st.sidebar:
    st.header("⚙️ 系统状态监控")
    st.success("API Key 已配置")
    st.divider()

    st.header("📊 实时状态追踪 (Input)")
    st.caption("0表示高风险，10表示非常健康。")

    for key, name in DIMENSIONS.items():
        score = st.session_state.scores[key]
        if score is None:
            st.info(f"{name}: 待评估")
        else:
            st.success(f"{name}: **{score}/10**")
            st.progress(score / 10.0)

    if st.session_state.is_completed:
        st.divider()
        st.warning("✅ 特征采集完毕，报告已生成。")

    st.divider()
    if st.button("🔄 重置评估系统", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ==========================================
# 5. 主界面逻辑（日记模式 + 深度学习模式）
# ==========================================

if not st.session_state.is_completed:
    # --- 日记本封面 UI ---
    st.title("📓 我的心理日记本")

    with st.container(border=True):
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            today = datetime.now()
            week_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            st.subheader(f"{today.strftime('%Y-%m-%d')} {week_map[today.weekday()]}")
        with col_t2:
            st.subheader("☀️ 天气：晴")

    # 逻辑核心：通过 display_messages 长度判断阶段
    is_first_turn = len(st.session_state.display_messages) <= 1
    prompt = None

    if is_first_turn:
        st.write("---")
        st.info("📖 **今日随笔**：请先像写日记一样，记录下你今天发生的事情、感受或身体状态。我会基于此进行初步分析。")
        diary_content = st.text_area("在此处开始撰写你的日记...", height=350,
                                     placeholder="今天过得怎么样？发生了什么特别的事吗？")
        if st.button("写好了，合上日记本"):
            if diary_content.strip():
                prompt = diary_content
            else:
                st.warning("日记还没写呢~")
    else:
        # 渲染之前的对话历史
        for msg in st.session_state.display_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        # 聊天输入框（深度交流模式）
        prompt = st.chat_input("针对刚才的内容，我们可以深入聊聊...")

    if prompt:
        # 写入对话记录
        st.session_state.display_messages.append({"role": "user", "content": prompt})
        if not is_first_turn:
            with st.chat_message("user"):
                st.markdown(prompt)

        # 强化后的 DYNAMIC_PROMPT，并处理了大括号转义
        DYNAMIC_PROMPT = f"""
你是一个针对大学生的心理状态倾听助手。你的任务是通过多轮自然的对话，评估用户的六个心理维度分数（0到10之间的整数，分数越高代表越积极健康，分数越低代表风险越高）。
六个维度如下：
x1(情绪状态): 0(严重抑郁/负面) -> 10(积极/平稳)
x2(焦虑与压力): 0(极度焦虑/压力崩溃) -> 10(放松/无压)
x3(生理状态): 0(严重失眠/躯体化症状) -> 10(睡眠饮食正常)
x4(行为与动力): 0(摆烂/逃避/丧失动力) -> 10(积极/有动力)
x5(社交与支持): 0(严重孤立/缺乏支持) -> 10(社交良好/有人倾诉)
x6(认知与意义): 0(绝望/认知扭曲/虚无主义) -> 10(充满希望/目标清晰)

【当前维度记忆】
注意：这是用户之前的评估分值，请在此基础上进行微调：{json.dumps(st.session_state.scores)}

【交互策略】
1. 首先，对用户的最新回复表达理解、共情或安慰。
2. 根据用户的描述，更新 x1 到 x6 的分数。如果描述太模糊，你可以给一个初步分数，但要在回复中追问细节以便后续微调。
3. 检查哪些维度的分数还是 null。在你的回复末尾，自然地提出 1 到 2 个问题，引导用户谈论这些尚未提及的维度。不要一次性像查户口一样问所有问题！
4. 如果你确信 6 个维度都已经获得了足够清晰的信息，可以将 status 设置为 "completed"。
5. 不必吝啬于打高分，如果用户明确提及“非常开心”等感情色彩强烈的描述，可以考虑在特定维度打到9~10分。

【强制输出格式】
你必须返回一个严格的 JSON 格式字符串。
请在每一次回复中，完整输出六个维度 x1 到 x6 的分数，即使该维度在当前对话中尚未涉及，也请在 score 中填入 null。
格式如下：
{{
  "reply_to_user": "...",
  "scores": {{
    "x1": 整数或null,
    "x2": 整数或null,
    "x3": 整数或null,
    "x4": 整数或null,
    "x5": 整数或null,
    "x6": 整数或null
  }},
  "status": "ongoing"或"completed"
}}
"""

        try:
            client = OpenAI(api_key=MY_API_KEY, base_url="https://api.deepseek.com")
            messages_for_api = [{"role": "system", "content": DYNAMIC_PROMPT}]
            for msg in st.session_state.display_messages:
                messages_for_api.append({"role": msg["role"], "content": msg["content"]})

            with st.spinner("正在品读并分析你的状态..."):
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages_for_api,
                    temperature=0.7
                )

            raw_result = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)

            if json_match:
                result_data = json.loads(json_match.group())
                reply_text = result_data.get("reply_to_user", raw_result)
                new_scores = result_data.get("scores", {})

                # --- 核心修复：更新分数必须在 if json_match 内部 ---
                for k in st.session_state.scores:
                    if k in new_scores and new_scores[k] is not None:
                        st.session_state.scores[k] = new_scores[k]

                st.session_state.display_messages.append({"role": "assistant", "content": reply_text})

                if result_data.get("status") == "completed":
                    st.session_state.is_completed = True

                # 更新完所有状态后再刷新页面
                st.rerun()
            else:
                # 如果没搜到 JSON，直接显示原始文本，防止冷场
                st.session_state.display_messages.append({"role": "assistant", "content": raw_result})
                st.rerun()

        except Exception as e:
            # 捕获所有 API 调用或解析中的错误
            st.error(f"❌ 分析失败或发生错误: {e}")

# ==========================================
# 6. 深度解析报告界面
# ==========================================
else:
    st.title("🧠 大学生心理健康深度监测报告")
    st.caption("基于深度解析架构 | 采集数据自动转化")
    st.markdown("---")

    current_vals = [st.session_state.scores[k] for k in ["x1", "x2", "x3", "x4", "x5", "x6"]]
    current_vals = [v if v is not None else 5 for v in current_vals]

    model = get_model()
    x_tensor = torch.FloatTensor([current_vals])
    with torch.no_grad():
        current_score = round(model(x_tensor).item(), 2)

    if not st.session_state.history or st.session_state.history[-1]['score'] != current_score:
        st.session_state.history.append({"score": current_score, "time": datetime.now().strftime("%H:%M:%S")})

    icon, level_name, theme_color, ai_direction = get_status_assets(current_score, current_vals)

    col1, col2 = st.columns([1, 1.3], gap="large")

    with col1:
        st.subheader("📡 综合评估")
        with st.container(border=True):
            st.markdown(f"<h1 style='text-align: center; font-size: 80px; margin: 0;'>{icon}</h1>",
                        unsafe_allow_html=True)
            st.metric("综合身心指数", f"{current_score}",
                      delta=round(current_score - st.session_state.history[-2]['score'], 2) if len(
                          st.session_state.history) > 1 else None)
            st.markdown(
                f"<div style='text-align: center; color: {theme_color}; font-weight: bold;'>【状态评级：{level_name}】</div>",
                unsafe_allow_html=True)

        st.write("### 🧠 维度画像")
        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
        angles = np.linspace(0, 2 * np.pi, 6, endpoint=False).tolist()
        vals = current_vals + current_vals[:1]
        angles += angles[:1]
        ax.fill(angles, vals, color=theme_color, alpha=0.3)
        ax.plot(angles, vals, color=theme_color, marker='o', linewidth=2)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(list(DIMENSIONS.values()))
        ax.set_ylim(0, 10)
        st.pyplot(fig)

    with col2:
        st.subheader("📈 趋势记录与深度解析")
        st.line_chart(pd.DataFrame(st.session_state.history).set_index('time'))

        with st.container(border=True):
            st.write("📝 **专家级深度解析报告**")
            with st.spinner("心理专家正在分析维度张力..."):
                prompt_report = (
                    f"请对测评得分{current_score}的学生进行解析。\n"
                    f"维度分：{dict(zip(DIMENSIONS.values(), current_vals))}。\n"
                    f"【解析架构】：1. 内在张力分析 2. 校园生活镜像 3. 资源评估 4. 处方建议。\n"
                    f"【创作方向】：{ai_direction}\n"
                    f"【文风】：专业精准，字数300-500字。"
                )
                try:
                    r = requests.post("https://api.deepseek.com/chat/completions",
                                      headers={"Authorization": f"Bearer {MY_API_KEY}"},
                                      json={
                                          "model": "deepseek-chat",
                                          "messages": [{"role": "user", "content": prompt_report}],
                                          "temperature": 0.85
                                      })
                    content = r.json()['choices'][0]['message']['content']
                    st.markdown(content)
                    st.write("---")
                    st.caption(f"💡 建议：{random.choice(['去操场散散步，看看天空。', '奖励自己一杯喜欢的饮品。', '放下手机，深呼吸三次。'])}")
                except:
                    st.error("深度解析生成失败，请检查网络。")
