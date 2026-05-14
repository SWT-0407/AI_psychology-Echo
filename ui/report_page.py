"""
深度解析报告页面（第三阶段）
展示综合评估、雷达图、趋势记录和 AI 生成的深度解析报告。
"""
import random
import streamlit as st
import pandas as pd
from datetime import datetime
from config import DIMENSIONS, DIMENSION_KEYS
from models.eval_net import calculate_composite_score
from utils.status_assets import get_status_assets
from utils.visualization import draw_radar_chart, configure_chinese_font
from services.ai_service import generate_report
from services.storage_local import get_all_trend_data


def render_report_page():
    """
    渲染深度解析报告主页面
    包括综合评估卡片、六维雷达图、趋势图、AI 深度解析。
    """
    # 配置中文字体
    configure_chinese_font()

    st.title("🧠 大学生心理健康深度监测报告")
    st.caption("基于深度解析架构 | 采集数据自动转化")
    st.markdown("---")

    # ========== 1. 准备数据 ==========
    current_vals = [st.session_state.scores[k] for k in DIMENSION_KEYS]
    current_vals = [v if v is not None else 5 for v in current_vals]

    # 计算综合评分
    current_score = calculate_composite_score(current_vals)

    # 更新历史趋势
    if not st.session_state.history or st.session_state.history[-1]['score'] != current_score:
        st.session_state.history.append({
            "score": current_score,
            "time": datetime.now().strftime("%H:%M:%S")
        })

    # 获取动态资源
    icon, level_name, theme_color, ai_direction = get_status_assets(current_score, current_vals)

    # ========== 2. 双列布局 ==========
    col1, col2 = st.columns([1, 1.3], gap="large")

    with col1:
        # --- 综合评估卡片 ---
        st.subheader("📡 综合评估")
        with st.container(border=True):
            st.markdown(
                f"<h1 style='text-align: center; font-size: 80px; margin: 0;'>{icon}</h1>",
                unsafe_allow_html=True
            )
            st.metric(
                "综合身心指数",
                f"{current_score}",
                delta=round(current_score - st.session_state.history[-2]['score'], 2)
                if len(st.session_state.history) > 1 else None
            )
            st.markdown(
                f"<div style='text-align: center; color: {theme_color}; font-weight: bold;'>"
                f"【状态评级：{level_name}】</div>",
                unsafe_allow_html=True
            )

        # --- 六维雷达图 ---
        st.write("### 🧠 维度画像")
        fig = draw_radar_chart(
            current_vals,
            list(DIMENSIONS.values()),
            theme_color
        )
        st.pyplot(fig)

    with col2:
        # --- 趋势图（基于所有历史会话数据，每次对话一个数据点） ---
        st.subheader("📈 趋势记录与深度解析")

        all_trends = get_all_trend_data()
        if all_trends:
            # 将当前会话的分数也加入趋势
            current_label = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 检查是否已有相同 label（避免重复）
            existing_labels = {t["display_label"] for t in all_trends}
            if current_label not in existing_labels:
                trend_df = pd.DataFrame(
                    [{"会话时间": current_label, "score": current_score}] +
                    [{"会话时间": t["display_label"], "score": t["score"]} for t in all_trends]
                )
            else:
                trend_df = pd.DataFrame(
                    [{"会话时间": t["display_label"], "score": t["score"]} for t in all_trends]
                )
            st.line_chart(
                trend_df.set_index("会话时间"),
                color="#64b5f6",
                use_container_width=True,
                height=200
            )
            st.markdown(
                f'<div style="text-align: center; font-size: 0.75rem; color: #9ab0c8; '
                f'font-weight: 300;">共 {len(trend_df)} 次对话记录</div>',
                unsafe_allow_html=True
            )
        else:
            # 无历史数据时，只显示当前会话的趋势（仅有本次）
            st.line_chart(
                pd.DataFrame([{"time": "当前", "score": current_score}]).set_index("time"),
                color="#64b5f6",
                use_container_width=True,
                height=200
            )

        # --- AI 深度解析 ---
        with st.container(border=True):
            st.write("📝 **专家级深度解析报告**")
            with st.spinner("心理专家正在分析维度张力..."):
                content = generate_report(
                    score=current_score,
                    dimension_vals=current_vals,
                    dim_names=list(DIMENSIONS.values()),
                    ai_direction=ai_direction
                )

                if content:
                    st.markdown(content)
                else:
                    st.error("深度解析生成失败，请检查网络。")

                st.write("---")

                # 随机建议
                tips = [
                    "去操场散散步，看看天空。",
                    "奖励自己一杯喜欢的饮品。",
                    "放下手机，深呼吸三次。",
                    "去买杯奶茶吧，珍珠是生活的解药。",
                    "今晚早睡15分钟，梦里没有ddl。",
                    "去摸摸校园里的猫，它是免费的心理咨询师。"
                ]
                st.caption(f"💡 建议：{random.choice(tips)}")
