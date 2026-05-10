
"""
核心模型定义 (ScientificEvalNet)
固定专家权重的线性模型，用于根据六维评分计算综合心理指数。
"""
import torch
import torch.nn as nn
import streamlit as st
from config import EXPERT_WEIGHTS


class ScientificEvalNet(nn.Module):
    """
    科学评估网络
    使用固定专家权重将六维心理评分映射为综合心理指数。
    权重映射：情绪0.15, 焦虑0.15, 生理0.10, 动力0.15, 社交0.20, 意义0.25
    """

    def __init__(self):
        super(ScientificEvalNet, self).__init__()
        self.fc = nn.Linear(6, 1, bias=False)
        expert_weights = torch.tensor([EXPERT_WEIGHTS])
        with torch.no_grad():
            self.fc.weight.copy_(expert_weights)

    def forward(self, x):
        weights = torch.abs(self.fc.weight)
        normalized_weights = weights / weights.sum()
        score = torch.matmul(x, normalized_weights.t()) * 10
        return score


@st.cache_resource
def get_model():
    """获取模型单例（带缓存）"""
    return ScientificEvalNet()


def calculate_composite_score(dimension_vals):
    """
    计算综合心理指数

    Args:
        dimension_vals: list, 六维评分 [x1, x2, x3, x4, x5, x6]

    Returns:
        float: 综合心理指数（0~100）
    """
    model = get_model()
    x_tensor = torch.FloatTensor([dimension_vals])
    with torch.no_grad():
        score = round(model(x_tensor).item(), 2)
    return score
