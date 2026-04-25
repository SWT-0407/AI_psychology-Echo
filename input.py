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

# ==========================================
# 1. 页面配置与初始化
# ==========================================
st.set_page_config(page_title="大学生心理状态动态评估系统", page_icon="🌱", layout="wide")

# 初始化 Session State
if "messages" not in st.session_state:
    # messages 用于存储给大模型看的完整历史记录
    st.session_state.messages = []
if "display_messages" not in st.session_state:
    # display_messages 用于存储在界面上展示给用户看的对话记录
    st.session_state.display_messages = [{"role": "assistant",
                                          "content": "你好！我是你的专属树洞助手。最近在学习和生活上感觉怎么样？有什么开心的或者烦心的事情，都可以跟我吐槽一下哦。"}]
if "scores" not in st.session_state:
    # 初始化六个维度的分数，None 表示未评估
    st.session_state.scores = {"x1": None, "x2": None, "x3": None, "x4": None, "x5": None, "x6": None}
if "is_completed" not in st.session_state:
    st.session_state.is_completed = False

# 维度名称映射（仅用于前端展示）
DIMENSIONS = {
    "x1": "情绪状态", "x2": "焦虑与压力", "x3": "生理状态",
    "x4": "行为与动力", "x5": "社交与支持", "x6": "认知与意义"
}

# ==========================================
# 2. 界面侧边栏：API配置与实时分数监控
# ==========================================

api_key = "sk-9286a96bcfc746dfa32d41bb19a093ac"  # 请替换为你真实的 DeepSeek API Key
MY_API_KEY = "sk-9286a96bcfc746dfa32d41bb19a093ac"

# with st.sidebar:
#     st.header("⚙️ 系统状态")
#     # 隐藏手动输入框，直接使用预设的变量
#     st.success("API Key 已配置")
#
#     st.divider()
#
#     st.header("📊 实时状态追踪 (Model Input)")
#     st.caption("这里的数值会在对话过程中动态更新。0表示良好，10表示风险极高。")
#
#     # 动态展示当前分数
#     for key in DIMENSIONS:
#         score = st.session_state.scores[key]
#         if score is None:
#             st.info(f"{key} ({DIMENSIONS[key]}): 待评估")
#         else:
#             st.success(f"{key} ({DIMENSIONS[key]}): **{score}/10**")
#
#     if st.session_state.is_completed:
#         st.divider()
#         st.warning("✅ 特征向量提取完毕，可传入下游评估模型。")
#         st.code(
#             f"Input Vector:\n[x1, x2, x3, x4, x5, x6] = \n[{st.session_state.scores['x1']}, {st.session_state.scores['x2']}, {st.session_state.scores['x3']}, {st.session_state.scores['x4']}, {st.session_state.scores['x5']}, {st.session_state.scores['x6']}]",
#             language="python")
#
#     st.divider()
#     st.caption("⚠️ 声明：本系统为高校竞赛 Demo，仅作行为数据辅助分析，不提供医疗诊断。")

# ==========================================
# 3. 大模型 System Prompt 定义
# ==========================================
SYSTEM_PROMPT = """
你是一个针对大学生的心理状态倾听助手。你的任务是通过多轮自然的对话，评估用户的六个心理维度分数（0到10之间的整数，分数越高代表问题越严重、风险越高）。
六个维度如下：
x1(情绪状态): 0(严重抑郁/负面) -> 10(积极/平稳)
x2(焦虑与压力): 0(放松/无压) -> 10(极度焦虑/压力崩溃)
x3(生理状态): 0(严重失眠/躯体化症状) -> 10(睡眠饮食正常)
x4(行为与动力): 0(摆烂/逃避/丧失动力) -> 10(积极/有动力)
x5(社交与支持): 0(严重孤立/缺乏支持) -> 10(社交良好/有人倾诉)
x6(认知与意义): 0(绝望/认知扭曲/虚无主义) -> 10(充满希望/目标清晰)

【交互策略】
1. 首先，对用户的最新回复表达理解、共情或安慰。
2. 根据用户的描述，更新 x1 到 x6 的分数。如果描述太模糊（例如“有点焦虑”），你可以给一个初步分数，但要在回复中追问细节以便后续微调。
3. 检查哪些维度的分数还是 null。在你的回复末尾，自然地提出 1 到 2 个问题，引导用户谈论这些尚未提及的维度。**不要一次性像查户口一样问所有问题！**
4. 如果你确信 6 个维度都已经获得了足够清晰的信息，可以将 status 设置为 "completed"。

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
# 4. 主界面对话展示
# ==========================================
st.title("🌱 心理状态自适应评估助手")
st.write("你好！随时跟我聊聊，让我更懂你。")

# 渲染对话历史
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 5. 用户输入与交互逻辑 (重写版)
# ==========================================
if not st.session_state.is_completed:
    if prompt := st.chat_input("说点什么吧..."):
        # 1. 记录用户输入并展示
        st.session_state.display_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 构建给大模型的历史记录
        history_for_llm = [{"role": "system", "content": SYSTEM_PROMPT}]
        history_for_llm.append({
            "role": "system",
            "content": f"目前评估状态为：{json.dumps(st.session_state.scores)}。请继续引导。"
        })
        for msg in st.session_state.display_messages:
            history_for_llm.append({"role": msg["role"], "content": msg["content"]})

        # # 2. 调用 DeepSeek API
        # try:
        #     client = OpenAI(api_key=MY_API_KEY, base_url="https://api.deepseek.com")
        #
        #     with st.spinner("AI 正在分析您的状态..."):
        #         response = client.chat.completions.create(
        #             model="deepseek-chat",
        #             messages=history_for_llm,
        #             temperature=0.7
        #         )
        #
        #     raw_result = response.choices[0].message.content
        #
        #     # 尝试从返回的原始文本中提取 JSON
        #     try:
        #         json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
        #         if json_match:
        #             result_data = json.loads(json_match.group())
        #             reply_text = result_data.get("reply_to_user", raw_result)
        #             new_scores = result_data.get("scores", {})
        #             chat_status = result_data.get("status", "ongoing")
        #         else:
        #             raise ValueError("未匹配到 JSON")
        #     except Exception:
        #         # 解析失败时的回退逻辑：直接显示 AI 的原始回复，不更新分数
        #         reply_text = raw_result
        #         new_scores = {}
        #         chat_status = "ongoing"
        #         st.warning("注：系统正在尝试获取深度评估数据...")

        # 2. 调用 DeepSeek API
        try:
            client = OpenAI(api_key=MY_API_KEY, base_url="https://api.deepseek.com")

            with st.spinner("AI 正在分析您的状态..."):
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=history_for_llm,
                    temperature=0.7
                )

            raw_result = response.choices[0].message.content

            # 初始化解析变量
            new_scores = {}
            chat_status = "ongoing"

            # 【关键改进】在解析 JSON 之前，先检查 AI 是否输出过总结性的文本
            # 或者通过一个标志位来决定是否显示后续追加的总结列表
            if chat_status == "completed" or "心理状态评估报告总结" in raw_result:
                # 如果模型已经自己写了总结，或者状态已经是 completed
                # 我们可以通过设置一个变量，只在这一轮渲染分数，后续锁死对话框
                st.session_state.is_completed = True

            # 【修复点】提取 JSON 并赋值
            try:
                json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
                if json_match:
                    result_data = json.loads(json_match.group())
                    reply_text = result_data.get("reply_to_user", raw_result)
                    new_scores = result_data.get("scores", {})
                    chat_status = result_data.get("status", "ongoing")
                else:
                    reply_text = raw_result
            except Exception:
                reply_text = raw_result
                st.warning("注：系统正在尝试获取深度评估数据...")

                # 3. 更新界面与状态
                # 【修复点】确保 here 更新了 state 中的值
                for k in st.session_state.scores:
                    # 如果模型返回了某个维度的分数，且不为 null，则更新
                    if k in new_scores and new_scores[k] is not None:
                        st.session_state.scores[k] = new_scores[k]

                # 显示 AI 回复
                st.session_state.display_messages.append({"role": "assistant", "content": reply_text})
                with st.chat_message("assistant"):
                    st.markdown(reply_text)

                # 检查是否完成
                if chat_status == "completed":
                    st.session_state.is_completed = True
                    st.toast("🎉 六个维度的特征采集已完成！", icon="✅")
                    st.rerun()
                else:
                    st.rerun()

            # 3. 更新界面与状态
            # 更新分数 (仅在解析成功且有值时更新)
            # for k in st.session_state.scores:
            #     if k in new_scores and new_scores[k] is not None:
            #         st.session_state.scores[k] = new_scores[k]

            # 【优化点】只更新模型明确返回了数值（非 null）的维度
            for k, val in new_scores.items():
                if k in st.session_state.scores and val is not None:
                    st.session_state.scores[k] = val

            # 显示 AI 回复
            st.session_state.display_messages.append({"role": "assistant", "content": reply_text})
            with st.chat_message("assistant"):
                st.markdown(reply_text)

            # 检查是否完成
            # if chat_status == "completed":
            #     st.session_state.is_completed = True
            #     st.toast("🎉 六个维度的特征采集已完成！", icon="✅")
            #     st.rerun()
            # else:
            #     st.rerun()
                # 检查是否完成
            if chat_status == "completed" or "评估报告总结" in reply_text:
                st.session_state.is_completed = True

                # 【去重逻辑】如果 AI 已经自己输出过列表了，就不要再追加一份，防止重复
                if "📋" not in reply_text:
                    score_summary = "\n\n### 📋 心理状态评估报告总结\n"
                    for k, v in st.session_state.scores.items():
                        score_summary += f"- **{DIMENSIONS.get(k, k)}**: {v}/10\n"
                    st.session_state.display_messages.append(
                        {"role": "assistant", "content": reply_text + score_summary})
                else:
                    # 如果 AI 已经输出过，就直接 append 原文
                    st.session_state.display_messages.append({"role": "assistant", "content": reply_text})

                st.rerun()

        except Exception as e:
            st.error(f"API 请求失败: {str(e)}")
else:
    # 采集完毕后的提示
    st.info("💡 信息收集完毕！系统已将您的特征参数传递给综合评估模型。")
    if st.button("重新开始评估"):
        # 清空状态
        st.session_state.messages = []
        st.session_state.display_messages = [
            {"role": "assistant", "content": "你好！我是你的专属树洞助手。最近在学习和生活上感觉怎么样？"}]
        st.session_state.scores = {"x1": None, "x2": None, "x3": None, "x4": None, "x5": None, "x6": None}
        st.session_state.is_completed = False
        st.rerun()

