import streamlit as st
import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os


# ==========================================
# 1. 模型架构：评估网络 (MLP) 与 融合网络 (CNN)
# ==========================================
class ScientificEvalNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(6, 16), nn.Tanh(),
            nn.Linear(16, 8), nn.Tanh(),
            nn.Linear(8, 1), nn.Sigmoid()
        )

    def forward(self, x):
        return self.network(x / 10.0) * 100


class WeightFusionCNN(nn.Module):
    def __init__(self, input_len):
        """
        input_len: 实际演化的代数 (动态传入)
        """
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Flatten()
        )
        # 这里的 16 是 Conv1d 的输出通道，6 是评估维度
        self.fc = nn.Linear(16 * input_len * 6, 6)

    def forward(self, x):
        x = self.conv(x)
        return torch.softmax(self.fc(x), dim=1)


# ==========================================
# 2. 自动化演化引擎 (带双重曲线记录)
# ==========================================
# 修改 run_convergent_evolution 函数中的读取部分
def run_convergent_evolution(file_path="mental_data.csv", max_gen=100, tol=5e-5):
    df = pd.read_csv(file_path)

    # 强制将数据转为数值，报错的转为 NaN 并删掉
    for col in df.columns[1:8]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna()

    # 重新提取 X 和 y
    X = torch.tensor(df.iloc[:, 1:7].values, dtype=torch.float32)
    y = torch.tensor(df.iloc[:, 7].values, dtype=torch.float32).view(-1, 1)
    # ... 后续逻辑 ...

    all_weights = []
    loss_history = []

    prog = st.progress(0)
    status = st.empty()

    for g in range(max_gen):
        model = ScientificEvalNet()
        opt = torch.optim.Adam(model.parameters(), lr=0.005)
        epoch_losses = []

        # 内部训练循环
        for _ in range(1000):
            pred = model(X)
            loss = nn.MSELoss()(pred, y)
            opt.zero_grad();
            loss.backward();
            opt.step()
            epoch_losses.append(loss.item())

        loss_history.append(np.mean(epoch_losses))

        # 敏感度分析提取权重
        with torch.no_grad():
            w = []
            base = model(torch.ones((1, 6)) * 5.0).item()
            for i in range(6):
                test = torch.ones((1, 6)) * 5.0
                test[0, i] += 1.0
                w.append(abs(model(test).item() - base))
            w_norm = np.array(w) / (sum(w) + 1e-7)
            all_weights.append(w_norm)

        # 收敛判定
        if g > 5:
            diff = np.mean(np.abs(all_weights[-1] - all_weights[-5]))
            status.text(f"演化中：第 {g + 1} 代 | 波动: {diff:.2e} | 损失: {loss_history[-1]:.4f}")
            if diff < tol:
                status.success(f"🎯 已达成数学收敛 (第 {g + 1} 代)")
                prog.progress(100)
                break
        prog.progress((g + 1) / max_gen)

    return np.array(all_weights), loss_history


# ==========================================
# 3. Streamlit 界面渲染
# ==========================================
st.set_page_config(page_title="AI 心理演化实验室", layout="wide")
st.title("🧠 心理健康监测系统：深度演化看板")

dim_names = ["情绪", "焦虑", "生理", "行为", "社交", "认同"]

with st.sidebar:
    st.header("⚙️ 实验控制")
    start_btn = st.button("🚀 启动自动化收敛演化", type="primary")

if start_btn:
    weights_hist, loss_hist = run_convergent_evolution()

    if weights_hist is not None:
        # 1. 计算 CNN 终极融合 (动态适配代数)
        actual_gen = len(weights_hist)
        cnn_in = torch.FloatTensor(weights_hist.flatten()).view(1, 1, -1)
        fusion_net = WeightFusionCNN(input_len=actual_gen)

        with torch.no_grad():
            final_w = fusion_net(cnn_in).numpy()[0]

        # 2. 绘制双曲线
        col1, col2 = st.columns(2)

        plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文显示
        plt.rcParams['axes.unicode_minus'] = False

        with col1:
            st.subheader("📉 损失函数收敛 (Loss)")

            fig_l, ax_l = plt.subplots()
            ax_l.plot(loss_hist, color='#FF4B4B', linewidth=2)
            ax_l.set_title("拟合误差随演化下降趋势")
            ax_l.set_xlabel("演化代数")
            ax_l.set_ylabel("均方误差 (MSE)")
            st.pyplot(fig_l)

        with col2:
            st.subheader("📈 维度权重收敛轨迹")

            fig_w, ax_w = plt.subplots()
            for i, name in enumerate(dim_names):
                ax_w.plot(weights_hist[:, i], label=name, alpha=0.8)
            ax_w.set_title("各维度影响力竞争平衡过程")
            ax_w.legend(loc='upper right', fontsize='small')
            st.pyplot(fig_w)

        # 3. 最终结果展示
        st.write("---")
        st.subheader("🎯 CNN 提炼终极权重")
        res_df = pd.DataFrame({
            "评估维度": dim_names,
            "最佳分配比例": [f"{w * 100:.2f}%" for w in final_w]
        })
        st.table(res_df.T)