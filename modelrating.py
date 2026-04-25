import streamlit as st
import torch
import torch.nn as nn
import requests
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime


# ==========================================
# 1. 核心模型：固定比例线性模型 (确保单调性)
# ==========================================
class ScientificEvalNet(nn.Module):
    def __init__(self):
        super(ScientificEvalNet, self).__init__()
        self.fc = nn.Linear(6, 1, bias=False)
        # 固定专家权重分配：认同0.25, 社交0.2, 安全0.15, 情绪0.15, 焦虑0.15, 生理0.1
        expert_weights = torch.tensor([[0.15, 0.15, 0.10, 0.15, 0.20, 0.25]])
        with torch.no_grad():
            self.fc.weight.copy_(expert_weights)

    def forward(self, x):
        # 强制权重为正并归一化
        weights = torch.abs(self.fc.weight)
        normalized_weights = weights / weights.sum()
        score = torch.matmul(x, normalized_weights.t()) * 10
        return score


@st.cache_resource
def get_model():
    return ScientificEvalNet()


# ==========================================
# 2. 系统配置
# ==========================================
st.set_page_config(page_title="大学生心理监测系统", page_icon="🎓", layout="wide")

# 中文字体处理
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 初始化 Session State
if 'history' not in st.session_state:
    st.session_state.history = []

# ==========================================
# 3. 界面布局
# ==========================================
st.title("🎓 大学生心理健康智能监测系统")
st.caption("实时同步版：解决图表滞后与趋势参照偏差")
st.markdown("---")

# --- 侧边栏 ---
with st.sidebar:
    st.header("🔑 系统配置")
    api_key = "sk-9286a96bcfc746dfa32d41bb19a093ac"  # 请确保 Key 有效

    st.write("---")
    st.header("📊 维度测评 (0-10)")
    dim_names = ["情绪积极度", "焦虑控制力", "生理活力", "行为安全度", "社交支持感", "自我认同感"]

    # 记录当前滑动条数值
    current_vals = []
    for name in dim_names:
        val = st.slider(name, 0.0, 10.0, 6.0, 0.5)
        current_vals.append(val)

    st.write("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        submit = st.button("🚀 生成报告", type="primary", use_container_width=True)
    with col_btn2:
        if st.button("清理数据", use_container_width=True):
            st.session_state.history = []
            st.rerun()

# --- 主界面逻辑 ---
if submit:
    # A. 计算得分
    model = get_model()
    x_tensor = torch.FloatTensor([current_vals])
    with torch.no_grad():
        current_score = round(model(x_tensor).item(), 2)

    # B. 【核心修正】立即更新历史记录，以便图表渲染最新点
    current_time = datetime.now().strftime("%H:%M:%S")
    st.session_state.history.append({"score": current_score, "time": current_time})

    # C. 计算趋势 delta (参照更新后的 history 倒数第二个值)
    delta = None
    if len(st.session_state.history) > 1:
        # 此时 history[-1] 是当前分，history[-2] 是上一次得分
        last_score = st.session_state.history[-2]['score']
        delta = round(current_score - last_score, 2)

    # D. 界面渲染
    col1, col2 = st.columns([1, 1.2], gap="large")

    with col1:
        with st.container(border=True):
            st.markdown(f"<h1 style='text-align: center; margin: 0;'>🎓</h1>", unsafe_allow_html=True)
            st.metric("综合身心指数", f"{current_score}", delta=delta)

            # 状态判定
            if current_score < 45:
                st.error("评级：存在高危短板 / 建议寻求辅导")
            elif current_score < 65:
                st.warning("评级：状态波动较大 / 需积极调节")
            else:
                st.success("评级：状态良好稳定 / 韧性十足")

        # 雷达图
        st.write("### 🧠 心理画像")
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
        st.write("### 📈 趋势记录")
        # 此时 DataFrame 已经包含刚 append 进去的最新数据
        df = pd.DataFrame(st.session_state.history)
        st.line_chart(df.set_index('time'))

        st.write("### 📝 AI 深度分析 (大学生版)")
        with st.spinner("AI 专家正在分析您的心理画像..."):
            prompt = (
                f"你是一位擅长大学生心理辅导的专家。测评者得分{current_score}分。维度数据：情绪{current_vals[0]}, "
                f"焦虑控制{current_vals[1]}, 生理{current_vals[2]}, 行为安全{current_vals[3]}, 社交支持{current_vals[4]}, 自我认同{current_vals[5]}。"
                f"请给出简短、针对性强的建议。"
            )
            try:
                r = requests.post("https://api.deepseek.com/chat/completions",
                                  headers={"Authorization": f"Bearer {api_key}"},
                                  json={"model": "deepseek-chat",
                                        "messages": [{"role": "user", "content": prompt}]})
                st.markdown(r.json()['choices'][0]['message']['content'])
            except:
                st.error("AI 报告生成时网络波动，请检查 API Key。")
