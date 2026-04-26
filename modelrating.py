import streamlit as st
import torch
import torch.nn as nn
import requests
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime


# ==========================================
# 1. 核心模型
# ==========================================
class ScientificEvalNet(nn.Module):
    def __init__(self):
        super(ScientificEvalNet, self).__init__()
        self.fc = nn.Linear(6, 1, bias=False)
        # 权重分配：情绪0.15, 焦虑0.15, 生理0.1, 安全0.15, 社交0.2, 认同0.25
        expert_weights = torch.tensor([[0.15, 0.15, 0.10, 0.15, 0.20, 0.25]])
        with torch.no_grad():
            self.fc.weight.copy_(expert_weights)

    def forward(self, x):
        weights = torch.abs(self.fc.weight)
        normalized_weights = weights / weights.sum()
        # 0-10 映射到 0-100 分制
        score = torch.matmul(x, normalized_weights.t()) * 10
        return score


@st.cache_resource
def get_model():
    return ScientificEvalNet()


# ==========================================
# 2. 系统配置与变量定义
# ==========================================
st.set_page_config(page_title="多维心理监测系统", page_icon="🧠", layout="wide")
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 固定数值设置区 ---
x1, x2, x3, x4, x5, x6 = 7.5, 4.0, 5.5, 9.0, 6.5, 8.0
current_vals = [x1, x2, x3, x4, x5, x6]
dim_names = ["情绪积极度", "焦虑控制力", "生理活力", "行为安全度", "社交支持感", "自我认同感"]


# ==========================================
# 3. 多维评价逻辑函数
# ==========================================
def get_detailed_status(score, vals):
    """根据总分和维度分返回多维评价"""
    # A. 基于总分的五段式评价
    if score >= 85:
        level = ("✨ 卓越状态", "success", "身心极度协调，具备极强的心理韧性与自我驱动力。")
    elif score >= 70:
        level = ("✅ 良好稳定", "info", "状态整体积极，能够有效应对日常生活中的压力。")
    elif score >= 55:
        level = ("⚠️ 亚健康波动", "warning", "处于平衡边缘，可能存在部分生活领域的失控感。")
    elif score >= 40:
        level = ("❗ 警示状态", "error", "心理资源消耗较大，建议主动减压并寻求社交支持。")
    else:
        level = ("🚨 高危预警", "error", "核心指标显著低落，请务必寻求专业辅导或暂停高压任务。")

    # B. 基于维度的短板/亮点检测 (木桶效应)
    critical_dims = [dim_names[i] for i, v in enumerate(vals) if v < 4.0]
    strengths = [dim_names[i] for i, v in enumerate(vals) if v > 8.5]

    return level, critical_dims, strengths


# ==========================================
# 4. 界面布局
# ==========================================
st.title("🎓 大学生心理健康多维监测系统")
st.markdown("---")

with st.sidebar:
    st.header("🔑 系统配置")
    api_key = "sk-9286a96bcfc746dfa32d41bb19a093ac"
    st.write("---")
    st.header("📊 实时输入维度")
    for name, val in zip(dim_names, current_vals):
        st.caption(f"{name}")
        st.progress(val / 10.0)

    submit = st.button("🚀 生成多维报告", type="primary", use_container_width=True)

if submit:
    # A. 模型计算
    model = get_model()
    x_tensor = torch.FloatTensor([current_vals])
    with torch.no_grad():
        current_score = round(model(x_tensor).item(), 2)

    # 更新历史
    st.session_state.history.append({"score": current_score, "time": datetime.now().strftime("%H:%M:%S")})

    # B. 获取多维评价内容
    (status_title, status_type, status_desc), critical, strengths = get_detailed_status(current_score, current_vals)

    # C. 渲染报告
    col1, col2 = st.columns([1, 1.2], gap="large")

    with col1:
        st.subheader("📡 综合评估结果")
        with st.container(border=True):
            st.metric("综合身心指数", f"{current_score}",
                      delta=round(current_score - st.session_state.history[-2]['score'], 2) if len(
                          st.session_state.history) > 1 else None)

            # 使用对应颜色渲染状态
            if status_type == "success":
                st.success(f"**{status_title}** \n\n {status_desc}")
            elif status_type == "info":
                st.info(f"**{status_title}** \n\n {status_desc}")
            elif status_type == "warning":
                st.warning(f"**{status_title}** \n\n {status_desc}")
            else:
                st.error(f"**{status_title}** \n\n {status_desc}")

        # 特色：多维亮点与短板卡片
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            if strengths:
                st.markdown("🌟 **核心优势**")
                for s in strengths: st.write(f"• {s}")
        with c_col2:
            if critical:
                st.markdown("🚩 **需关注点**")
                for c in critical: st.write(f"• {c}")

        # 雷达图
        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
        angles = np.linspace(0, 2 * np.pi, 6, endpoint=False).tolist()
        vals = current_vals + current_vals[:1]
        angles += angles[:1]
        ax.fill(angles, vals, color='#4BC0C0', alpha=0.3)
        ax.plot(angles, vals, color='#4BC0C0', marker='o')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dim_names)
        st.pyplot(fig)

    with col2:
        st.subheader("📈 状态趋势与建议")
        st.line_chart(pd.DataFrame(st.session_state.history).set_index('time'))

        with st.expander("📝 查看 AI 深度辅导建议", expanded=True):
            with st.spinner("专家分析中..."):
                prompt = (
                    f"作为校园心理专家，分析得分{current_score}（{status_title}）。"
                    f"重点关注短板：{critical if critical else '无'}。优势维度：{strengths if strengths else '中规中矩'}。"
                    f"请给出一份针对性强的行动方案。"
                )
                try:
                    r = requests.post("https://api.deepseek.com/chat/completions",
                                      headers={"Authorization": f"Bearer {api_key}"},
                                      json={"model": "deepseek-chat",
                                            "messages": [{"role": "user", "content": prompt}]})
                    st.markdown(r.json()['choices'][0]['message']['content'])
                except:
                    st.error("AI 接口未响应。")
