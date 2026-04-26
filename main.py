# # x1 #情绪状态
# # x2 #焦虑与压力
# # x3 #生理状态
# # x4 #行为与动力
# # x5 #社交与支持
# # x6 #认知与意义

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
    "x1": "情绪状态", "x2": "焦虑控制力", "x3": "生理状态",
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


SYSTEM_PROMPT = """
你是一个针对大学生的心理状态倾听助手。你的任务是通过多轮自然的对话，评估用户的六个心理维度分数（0到10之间的整数，分数越高代表问题越严重、风险越高）。
六个维度如下：
x1(情绪状态): 0(严重抑郁/负面) -> 10(积极/平稳)
x2(焦虑与压力): 0(极度焦虑/压力崩溃) -> 10(放松/无压)
x3(生理状态): 0(严重失眠/躯体化症状) -> 10(睡眠饮食正常)
x4(行为与动力): 0(摆烂/逃避/丧失动力) -> 10(积极/有动力)
x5(社交与支持): 0(严重孤立/缺乏支持) -> 10(社交良好/有人倾诉)
x6(认知与意义): 0(绝望/认知扭曲/虚无主义) -> 10(充满希望/目标清晰)

【交互策略】
1. 首先，对用户的最新回复表达理解、共情或安慰。
2. 根据用户的描述，更新 x1 到 x6 的分数。如果描述太模糊（例如“有点焦虑”），你可以给一个初步分数，但要在回复中追问细节以便后续微调。
3. 检查哪些维度的分数还是 null。在你的回复末尾，自然地提出 1 到 2 个问题，引导用户谈论这些尚未提及的维度。**不要一次性像查户口一样问所有问题！**
4. 如果你确信 6 个维度都已经获得了足够清晰的信息，可以将 status 设置为 "completed"。
5. 不必吝啬于打高分，如果用户明确提及“非常开心”等感情色彩强烈的描述，可以考虑在特定维度打到9~10分。

【强制输出格式】
你必须返回一个严格的 JSON 格式字符串。
请在每一次回复中，完整输出六个维度 x1 到 x6 的分数，即使该维度在当前对话中尚未涉及，也请在 score 中填入 null。
不要包含任何额外的 JSON 外部内容。
格式如下：
{
  "reply_to_user": "...",
  "scores": {
    "x1": 整数或null,
    "x2": 整数或null,
    "x3": 整数或null,
    "x4": 整数或null,
    "x5": 整数或null,
    "x6": 整数或null
  },
  "status": "ongoing"或"completed"
}

【最终报告规则】
当你认为所有维度评估完毕，设置 status 为 "completed" 时，
你不需要在 reply_to_user 中写出具体的数值，
系统会自动在你的回复后面追加一份统计列表。
你只需要写一段总结性的心理健康建议或鼓励的话即可。

一旦你认为评估已经结束，你必须在 JSON 的 status 字段中明确设为 'completed'。如果你一旦输出过评估总结列表，就绝对不要在后续的对话中再次重复输出或提及总结报告，直接结束即可。
"""

# ==========================================
# 4. 侧边栏：状态监控 (保持之前的布局)
# ==========================================
with st.sidebar:
    st.header("⚙️ 系统状态监控")
    st.success("API Key 已配置")
    st.divider()

    st.header("📊 实时状态追踪 (Input)")
    st.caption("0表示良好，10表示风险极高。")

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
# 5. 主界面逻辑（分为：对话采集 / 深度报告）
# ==========================================

# --- [第一阶段] 对话采集界面 ---
if not st.session_state.is_completed:
    st.title("🌱 心理状态自适应评估助手")
    st.write("你好！随时跟我聊聊，让我更懂你。")

    # 渲染历史对话
    for msg in st.session_state.display_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 用户输入交互
    if prompt := st.chat_input("说点什么吧..."):
        st.session_state.display_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 构建对话请求
        history_for_llm = [{"role": "system", "content": SYSTEM_PROMPT}]
        history_for_llm.append({"role": "system", "content": f"目前分数：{json.dumps(st.session_state.scores)}"})
        for msg in st.session_state.display_messages:
            history_for_llm.append({"role": msg["role"], "content": msg["content"]})

        try:
            client = OpenAI(api_key=MY_API_KEY, base_url="https://api.deepseek.com")
            with st.spinner("AI 正在分析您的状态..."):
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=history_for_llm,
                    temperature=0.7
                )

            raw_result = response.choices[0].message.content

            # 正则提取 JSON
            json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
            if json_match:
                result_data = json.loads(json_match.group())
                reply_text = result_data.get("reply_to_user", raw_result)
                new_scores = result_data.get("scores", {})
                chat_status = result_data.get("status", "ongoing")

                # 更新全局分数
                for k in st.session_state.scores:
                    if k in new_scores and new_scores[k] is not None:
                        st.session_state.scores[k] = new_scores[k]

                st.session_state.display_messages.append({"role": "assistant", "content": reply_text})

                if chat_status == "completed":
                    st.session_state.is_completed = True

                st.rerun()
            else:
                # 解析失败回退
                st.session_state.display_messages.append({"role": "assistant", "content": raw_result})
                st.rerun()

        except Exception as e:
            st.error(f"API 请求失败: {str(e)}")

# --- [第二阶段] 深度解析报告界面 ---
else:
    st.title("🧠 大学生心理健康深度监测报告")
    st.caption("基于深度解析架构 | 采集数据自动转化")
    st.markdown("---")

    # A. 准备数据并进行模型计算
    current_vals = [st.session_state.scores[k] for k in ["x1", "x2", "x3", "x4", "x5", "x6"]]
    # 容错处理：如果有维度还是 None，填充为 5 (中等)
    current_vals = [v if v is not None else 5 for v in current_vals]

    model = get_model()
    x_tensor = torch.FloatTensor([current_vals])
    with torch.no_grad():
        current_score = round(model(x_tensor).item(), 2)

    # 记录历史趋势
    if not st.session_state.history or st.session_state.history[-1]['score'] != current_score:
        st.session_state.history.append({"score": current_score, "time": datetime.now().strftime("%H:%M:%S")})

    # 获取动态资源
    icon, level_name, theme_color, ai_direction = get_status_assets(current_score, current_vals)
    critical = [DIMENSIONS[k] for k, v in zip(["x1", "x2", "x3", "x4", "x5", "x6"], current_vals) if v > 7]

    # B. 渲染双列布局 (与原监测系统布局完全一致)
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
                prompt = (
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
                                          "messages": [{"role": "user", "content": prompt}],
                                          "temperature": 0.85
                                      })
                    content = r.json()['choices'][0]['message']['content']
                    st.markdown(content)
                    st.write("---")
                    st.caption(
                        f"💡 建议：{random.choice(['去操场散散步，看看天空。', '奖励自己一杯喜欢的饮品。', '放下手机，深呼吸三次。'])}")
                except:
                    st.error("深度解析生成失败，请检查网络。")

