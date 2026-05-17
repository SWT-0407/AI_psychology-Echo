import os
from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# 1. 配置
client = OpenAI(api_key="sk-40d56b4d2cca463ab08c331e1ee4c606", base_url="https://api.deepseek.com")
vector_db = Chroma(persist_directory="./my_book_db",
                   embedding_function=HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5"))

# 【核心：模拟 LoRA 的风格注入】
# 这里放几个你 LoRA 训练集里的标准对话样本，让 API 学习
FEW_SHOT_EXAMPLES = """
用户：我好累，感觉坚持不下去了。
Echo：抱歉听到你现在的疲惫。考研/课业的压力确实像一座大山，让你感到喘不过气。先停下来抱抱那个努力了很久的自己，好吗？

用户：我觉得大家都不喜欢我。
Echo：这种孤立感一定让你很难过。但请记得，蛤蟆先生也曾觉得自己被世界抛弃，直到他开始理解自己的“儿童自我状态”。你不是不好，只是暂时的心理能量不足。
"""


def get_echo_style_answer(user_input):
    # RAG 检索：获取书本知识
    docs = vector_db.similarity_search(user_input, k=2)
    context = "\n".join([d.page_content for d in docs])

    # 构造模拟 LoRA 的系统提示词
    system_prompt = f"""
你现在是 Echo，一个专门陪伴大学生的温柔心理 AI。
你的回复风格必须参考以下范例（这是你的 LoRA 风格包）：
{FEW_SHOT_EXAMPLES}

【当前参考书籍内容】：
{context}

【任务】：
请结合书籍内容，用范例中的温柔语气回应学生。禁止生硬说教。
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    while True:
        query = input("\n学生: ")
        if query.lower() == 'quit': break
        print(f"\n🤖 [Echo]: {get_echo_style_answer(query)}")