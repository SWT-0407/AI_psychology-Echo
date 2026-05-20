import streamlit as st
import torch
import torch.nn as nn
import requests
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import random
import os
from dotenv import load_dotenv


# ==========================================
# 1. 核心模型：固定专家权重线性模型
# ==========================================
class ScientificEvalNet(nn.Module):
    def __init__(self):
        super(ScientificEvalNet, self).__init__()
        self.fc = nn.Linear(6, 1, bias=False)
        # 权重：认同0.25, 社交0.2, 安全0.15, 情绪0.15, 焦虑0.15, 生理0.1
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
# 2. 系统配置与变量定义 (在此修改数值)
# ==========================================
st.set_page_config(page_title="大学生心理多维监测系统", page_icon="🧠", layout="wide")

# 中文字体处理
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 固定数值设置区 ---
x1 = 3.5  # 情绪积极度
x2 = 2.0  # 焦虑控制力
x3 = 5.5  # 生理活力
x4 = 2.0  # 行为安全度
x5 = 6.5  # 社交支持感
x6 = 2.0  # 自我认同感

current_vals = [x1, x2, x3, x4, x5, x6]
dim_names = ["情绪积极度", "焦虑控制力", "生理活力", "行为安全度", "社交支持感", "自我认同感"]


# ==========================================
# 3. 动态资源库：Emoji池与人设方向
# ==========================================
def get_status_assets(score, vals):
    """
    根据得分和维度细节，动态匹配 Emoji 池和 AI 创作方向
    """
    x3_physic = vals[2]  # 获取生理活力

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
        # 低生理活力时强制显示低电量
        icon = "🪫" if x3_physic < 4.5 else random.choice(["🌧️", "😮‍💨", "🩹", "🌫️", "🧊"])
        level, color = "蓄势待发", "#fd7e14"
        direction = "人设：深夜电台主播。方向：允许停顿与崩溃，深度共情疲惫，文风极其温柔。"
    else:
        icon = random.choice(["🚨", "🆘", "☔", "💔", "🥀"])
        level, color = "静候天晴", "#dc3545"
        direction = "人设：专业的心理守护者。方向：无条件接纳，紧急安抚，强调保护核心自我，文风坚定有力。"

    return icon, level, color, direction


# ==========================================
# 4. 界面布局
# ==========================================
st.title("🧠 大学生心理健康深度监测系统")
st.caption("基于深度解析架构 | 固定维度测试模式")
st.markdown("---")

# --- 侧边栏 ---
with st.sidebar:
    st.header("🔑 系统配置")
    load_dotenv()
    api_key = os.getenv("API_KEY")

    st.write("---")
    st.header("📊 维度数值快照")
    for name, val in zip(dim_names, current_vals):
        st.caption(f"{name}")
        st.progress(val / 10.0)

    st.write("---")
    if st.button("🚀 生成深度解析报告", type="primary", use_container_width=True):
        st.session_state.do_submit = True
    if st.button("清理数据历史", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# --- 主界面逻辑 ---
if st.session_state.get('do_submit', False):
    # A. 模型计算
    model = get_model()
    x_tensor = torch.FloatTensor([current_vals])
    with torch.no_grad():
        current_score = round(model(x_tensor).item(), 2)

    # 更新历史记录
    st.session_state.history.append({"score": current_score, "time": datetime.now().strftime("%H:%M:%S")})

    # B. 获取动态资源
    icon, level_name, theme_color, ai_direction = get_status_assets(current_score, current_vals)
    critical = [dim_names[i] for i, v in enumerate(current_vals) if v < 4.5]

    # C. 渲染报告
    col1, col2 = st.columns([1, 1.3], gap="large")

    with col1:
        st.subheader("📡 综合评估")
        with st.container(border=True):
            # 动态大 Emoji 渲染
            st.markdown(f"<h1 style='text-align: center; font-size: 80px; margin: 0;'>{icon}</h1>",
                        unsafe_allow_html=True)
            st.metric("综合身心指数", f"{current_score}",
                      delta=round(current_score - st.session_state.history[-2]['score'], 2) if len(
                          st.session_state.history) > 1 else None)
            st.markdown(
                f"<div style='text-align: center; color: {theme_color}; font-weight: bold;'>【状态评级：{level_name}】</div>",
                unsafe_allow_html=True)

        # 雷达图渲染
        st.write("### 🧠 维度画像")
        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
        angles = np.linspace(0, 2 * np.pi, 6, endpoint=False).tolist()
        vals = current_vals + current_vals[:1]
        angles += angles[:1]
        ax.fill(angles, vals, color=theme_color, alpha=0.3)
        ax.plot(angles, vals, color=theme_color, marker='o', linewidth=2)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dim_names)
        ax.set_ylim(0, 10)
        st.pyplot(fig)

    with col2:
        st.subheader("📈 趋势记录与深度解析")
        st.line_chart(pd.DataFrame(st.session_state.history).set_index('time'))

        # --- AI 深度解析区 ---
        with st.container(border=True):
            st.write("📝 **专家级深度解析报告**")
            with st.spinner("心理专家正在分析维度张力..."):
                prompt = (
                    f"你是一位拥有10年经验的校园心理专家。请对得分{current_score}的学生进行解析。\n"
                    f"维度分：{dict(zip(dim_names, current_vals))}。\n"
                    f"【解析架构要求】：\n"
                    f"1. 内在张力分析：分析各维度搭配背后的心理机制（如：为什么自我认同高但生理活力低）。\n"
                    f"2. 校园生活镜像：描述测评者在ddl压力、宿舍社交或课堂中的典型行为表现。\n"
                    f"3. 资源评估：评估当前的‘精神带宽’与复原力，是消耗期还是蓄能期？\n"
                    f"4. 处方建议：提供2条基于CBT或正念的微小行动方案。\n"
                    f"【创作人设与方向】：{ai_direction}\n"
                    f"【文风】：专业精准，多用隐喻，严禁说教。字数300-500字。"
                )
                try:
                    r = requests.post("https://api.deepseek.com/chat/completions",
                                      headers={"Authorization": f"Bearer {api_key}"},
                                      json={
                                          "model": "deepseek-chat",
                                          "messages": [{"role": "user", "content": prompt}],
                                          "temperature": 0.85,
                                          "presence_penalty": 0.5
                                      })
                    st.markdown(r.json()['choices'][0]['message']['content'])

                    st.write("---")
                    st.caption(
                        f"💡 随机彩蛋建议：{random.choice(['去买杯奶茶吧，珍珠是生活的解药。', '今晚早睡15分钟，梦里没有ddl。', '去摸摸校园里的猫，它是免费的心理咨询师。'])}")
                except:
                    st.error("深度解析生成失败，请检查 API 配置或网络环境。")
