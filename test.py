import streamlit as st
from openai import OpenAI
import json

# API
client = OpenAI(
    api_key="sk-9286a96bcfc746dfa32d41bb19a093ac",
    base_url="https://api.deepseek.com"
)

# 模型
def calculate_score(sleep, study, stress, social):
    return (6 - sleep)*0.4 + (3 - study)*0.3 + stress*0.2 + (1 - social)*0.1

def get_risk(score):
    if score > 5:
        return "高风险 ⚠️"
    elif score > 3:
        return "中风险"
    else:
        return "低风险"

# UI
st.title("心理健康预警系统")

text = st.text_area("请输入你的感受")
sleep = st.slider("睡眠时间", 0, 12, 6)
study = st.slider("学习时间", 0, 12, 3)

if st.button("开始评估"):

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是心理分析助手，输出JSON"},
            {"role": "user", "content": f"""
请分析文本：
{{
  "emotion": "",
  "stress_level": 0-1,
  "social_willingness": 0-1
}}

文本：{text}
"""}
        ]
    )

    result = response.choices[0].message.content
    data = json.loads(result)

    stress = data["stress_level"]
    social = data["social_willingness"]

    score = calculate_score(sleep, study, stress, social)
    risk = get_risk(score)

    st.write(data)
    st.write("评分：", score)
    st.write("风险：", risk)

#API

#文字 →AI→ 不同维度的评分

#f(x) 怎么写 （不能写线性）

#输出


