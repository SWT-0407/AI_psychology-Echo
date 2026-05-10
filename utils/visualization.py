"""
可视化工具模块
提供疗愈风格的雷达图绘制等图表生成功能。
"""
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st


def configure_chinese_font():
    """配置中文字体支持（雷达图显示中文）"""
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False


def draw_radar_chart(dimension_vals, dim_names, theme_color, figsize=(4.8, 4.8)):
    """
    绘制疗愈风格的六维雷达图

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

    # 柔和颜色映射
    fill_color = theme_color if theme_color else "#64b5f6"

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    # 背景设置
    ax.set_facecolor('#f8fbff')
    fig.patch.set_facecolor('none')

    angles = np.linspace(0, 2 * np.pi, 6, endpoint=False).tolist()
    vals = dimension_vals + dimension_vals[:1]
    angles += angles[:1]

    # 填充区域（半透明渐变）
    ax.fill(angles, vals, color=fill_color, alpha=0.12)

    # 数据线（柔和圆滑）
    ax.plot(angles, vals, color=fill_color, marker='o',
            linewidth=2, markersize=6, markerfacecolor='white',
            markeredgecolor=fill_color, markeredgewidth=1.5,
            solid_capstyle='round', alpha=0.8)

    # 刻度网格（淡色）
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dim_names, fontsize=11, color='#5a7a9a',
                       fontweight='normal')

    # 同心圆网格线（极淡）
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'],
                       fontsize=7, color='#b0c8e0', fontweight='normal')
    ax.yaxis.grid(True, color='#d9e7f5', linewidth=0.5, alpha=0.6)
    ax.xaxis.grid(True, color='#d9e7f5', linewidth=0.5, alpha=0.6)

    # 隐藏边框
    ax.spines['polar'].set_visible(False)

    # 轻微标题
    ax.set_title('', pad=15, fontsize=12, color='#4a6a8a',
                 fontweight='normal')

    return fig
