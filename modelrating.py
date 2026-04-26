import streamlit as st
import torch
import torch.nn as nn
import requests
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import random


# ==========================================
# 1. 核心模型
# ==========================================
class ScientificEvalNet(nn.Module):
    def __init__(self):
        super(ScientificEvalNet, self).__init__()
        self.fc = nn.Linear(6, 1, bias=False)
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
# 2. 系统配置与变量定义
# ==========================================
st.set_page_config(page_title="大学生心理监测系统", page_icon="🎓", layout="wide")
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 维度变量 (固定值测试区) ---
x1, x2, x3, x4, x5, x6 = 7.5, 4.5, 5.0, 9.0, 6.5, 8.0
current_vals = [x1, x2, x3, x4, x5, x6]
dim_names = ["情绪积极度", "焦虑控制力", "生理活力", "行为安全度", "社交支持感", "自我认同感"]


# ==========================================
# 3. 指定 AI 生成方向的函数
# ==========================================
def get_ai_direction(score, critical_dims):
    """根据分数和短板，为 DeepSeek 指定文案创作方向"""
    if score >= 80:
        return "人设：充满活力的学长/学姐。方向：肯定、激励、分享喜悦，口吻要像阳光下的击掌。"
    elif score >= 60:
        return "人设：温和治愈的朋友。方向：认可、平衡生活、提供生活小建议，口吻要像午后的咖啡。 "
    elif score >= 45:
        return "人设：懂你的深夜树洞。方向：深度共情、缓解内耗、允许负面情绪，口吻要像柔软的毛毯。"
    else:
        return "人设：专业的校园守护者。方向：无条件接纳、紧急安抚、避风港理念，口吻要极其温柔且坚定。"


# ==========================================
# 4. 界面布局
# ==========================================
st.title("🎓 大学生心理健康智能监测系统")
st.caption("实时同步版：解决图表滞后与趋势参照偏差")
st.markdown("---")

with st.sidebar:
    st.header("🔑 系统配置")
    api_key = "sk-9286a96bcfc746dfa32d41bb19a093ac"
    st.write("---")
    st.header("📊 维度数值")
    for name, val in zip(dim_names, current_vals):
        st.info(f"**{name}**: {val}")

    submit = st.button("🚀 生成多维报告", type="primary", use_container_width=True)

# --- 主界面逻辑 ---
if submit:
    model = get_model()
    x_tensor = torch.FloatTensor([current_vals])
    with torch.no_grad():
        current_score = round(model(x_tensor).item(), 2)

    # 更新历史
    st.session_state.history.append({"score": current_score, "time": datetime.now().strftime("%H:%M:%S")})

    # 判定短板 (低于4分视为短板)
    critical = [dim_names[i] for i, v in enumerate(current_vals) if v < 4.0]

    col1, col2 = st.columns([1, 1.2], gap="large")

    with col1:
        with st.container(border=True):
            st.markdown(f"<h1 style='text-align: center; margin: 0;'>🎓</h1>", unsafe_allow_html=True)
            st.metric("综合身心指数", f"{current_score}",
                      delta=round(current_score - st.session_state.history[-2]['score'], 2) if len(
                          st.session_state.history) > 1 else None)

        # 雷达图
        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
        angles = np.linspace(0, 2 * np.pi, 6, endpoint=False).tolist()
        vals = current_vals + current_vals[:1]
        angles += angles[:1]
        ax.fill(angles, vals, color='#4A90E2', alpha=0.3)
        ax.plot(angles, vals, color='#4A90E2', marker='o', linewidth=2)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dim_names)
        ax.set_ylim(0, 10)
        st.pyplot(fig)

    with col2:
        st.write("### 📈 深度趋势与多维解析")
        st.line_chart(pd.DataFrame(st.session_state.history).set_index('time'))

        # --- 核心修改：多维结构化解析 ---
        with st.container(border=True):
            st.write("### 📝 专家级测评分析报告")
            with st.spinner("心理专家正在多维解析您的状态..."):
                # 确定解析方向
                ai_direction = get_ai_direction(current_score, critical)

                # 结构化 Prompt
                prompt = (
                    f"你是一位拥有10年临床经验的校园心理咨询专家。请针对以下测评数据进行深度、精准且富有亲和力的解析。\n"
                    f"【测评总分】：{current_score}\n"
                    f"【维度数据】：{dict(zip(dim_names, current_vals))}\n"
                    f"【历史趋势】：{'正在上升' if len(st.session_state.history) > 1 and current_score >= st.session_state.history[-2]['score'] else '有所波动'}\n"
                    f"\n要求按照以下四个维度展开深度分析：\n"
                    f"1. **维度平衡与内在张力**：分析各维度间的配合。比如高认同低社交、或低生理高焦虑背后的心理机制是什么？\n"
                    f"2. **校园生活镜像**：将数据转化为具体的场景（如：ddl压力下的反应、宿舍社交状态、课堂专注力）。\n"
                    f"3. **心理资源评估**：评估测评者当前的‘精神带宽’和复原力，是处于‘消耗期’还是‘蓄能期’？\n"
                    f"4. **处方级行动建议**：提供2条基于CBT（认知行为疗法）或正念的微小行动建议，要具体到‘去做什么’。\n"
                    f"\n【文风要求】：专业严谨但拒绝教条，多用‘精神带宽、情绪反刍、社会支撑、多巴胺补偿’等专业词汇。字数300-500字。"
                )

                try:
                    r = requests.post("https://api.deepseek.com/chat/completions",
                                      headers={"Authorization": f"Bearer {api_key}"},
                                      json={
                                          "model": "deepseek-chat",
                                          "messages": [{"role": "user", "content": prompt}],
                                          "temperature": 0.85,  # 略微降低温度以保证逻辑严密性
                                          "presence_penalty": 0.4
                                      })

                    analysis_text = r.json()['choices'][0]['message']['content']

                    # 使用 Markdown 渲染解析内容
                    st.markdown(analysis_text)

                    st.write("---")
                    # 动态生成个性化结语 (之前讨论的随机结语)
                    closing_text = get_ai_direction(current_score, critical)
                    st.caption(f"💡 温馨贴士：{closing_text}")

                except Exception as e:
                    st.error(f"深度解析生成失败，请检查 API 配置。错误详情：{e}")
