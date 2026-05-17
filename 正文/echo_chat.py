import os
from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# 1. API 配置
client = OpenAI(api_key="sk-40d56b4d2cca463ab08c331e1ee4c606", base_url="https://api.deepseek.com")

# 2. 数据库连接
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
vector_db = Chroma(persist_directory="./my_book_db", embedding_function=embeddings)


def get_echo_answer_debug_v2(user_input):
    # --- 【关键点 A：检索书籍内容】 ---
    docs = vector_db.similarity_search(user_input, k=3)

    print("\n" + "=" * 60)
    print("🔍 [DEBUG] 正在检查数据库匹配情况...")

    if not docs:
        print("❌ 警告：数据库没搜到任何内容！请检查 input1.md 是否已成功存入数据库。")
        return

    # 打印出代码到底从书里抓到了哪几段话
    context_list = []
    for i, d in enumerate(docs):
        snippet = d.page_content.replace('\n', ' ')
        print(f"📖 书籍原文片段 [{i + 1}]: {snippet[:150]}...")  # 打印前150字
        context_list.append(d.page_content)

    context_text = "\n".join(context_list)

    # --- 【关键点 B：确认 Prompt 组合】 ---
    # 这里把书里的内容正式塞进消息里
    prompt_messages = [
        {"role": "system", "content": f"你必须参考以下书籍原文来回答：\n{context_text}"},
        {"role": "user", "content": user_input}
    ]

    print("🚀 [DEBUG] 已将上述原文塞进 Prompt，发送给 DeepSeek...")

    # --- 【关键点 C：API 调用】 ---
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=prompt_messages,
        stream=False
    )

    print(f"📊 [DEBUG] 本次 API 调用消耗 Token: {response.usage.total_tokens}")
    print("=" * 60 + "\n")

    return response.choices[0].message.content


if __name__ == "__main__":
    while True:
        query = input("\n测试提问 (输入 quit 退出): ")
        if query.lower() == 'quit': break

        answer = get_echo_answer_debug_v2(query)
        if answer:
            print(f"🤖 [Echo 回复]:\n{answer}")