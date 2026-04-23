from openai import OpenAI

# 1️⃣ 填入你的API Key
client = OpenAI(
    api_key="sk-9286a96bcfc746dfa32d41bb19a093ac",
    base_url="https://api.deepseek.com"
)

# 2️⃣ 输入测试文本
text = "最近很累，不想学习，也不想和别人说话"

# 3️⃣ 调用模型
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "system",
            "content": "你是一个心理分析助手，请严格输出JSON"
        },
        {
            "role": "user",
            "content": f"""
请分析以下文本，并输出JSON：
{{
  "emotion": "情绪（如：积极/中性/消极）",
  "stress_level": 0-1之间的小数,
  "social_willingness": 0-1之间的小数
}}

文本：{text}
"""
        }
    ]
)

# 4️⃣ 输出结果
print(response.choices[0].message.content)