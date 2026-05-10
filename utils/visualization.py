"""
可视化工具模块
提供雷达图绘制等图表生成功能。
"""
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st


def configure_chinese_font():
    """配置中文字体支持（雷达图显示中文）"""
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False


def draw_radar_chart(dimension_vals, dim_names, theme_color, figsize=(5, 5)):
    """
    绘制六维雷达图

    Args:
        dimension_vals: list, 六维评分值
        dim_names: list, 维度名称列表
        theme_color: str, 主题颜色（十六进制）
        figsize: tuple, 图像尺寸

    Returns:
        matplotlib.figure.Figure: 雷达图对象
    """
    # 确保字体已配置
    configure_chinese_font()

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    angles = np.linspace(0, 2 * np.pi, 6, endpoint=False).tolist()
    vals = dimension_vals + dimension_vals[:1]
    angles += angles[:1]

    ax.fill(angles, vals, color=theme_color, alpha=0.3)
    ax.plot(angles, vals, color=theme_color, marker='o', linewidth=2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dim_names)
    ax.set_ylim(0, 10)

    return fig
