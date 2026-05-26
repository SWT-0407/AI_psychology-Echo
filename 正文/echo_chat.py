import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# 1. API 閰嶇疆
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# 2. 鏁版嵁搴撹繛鎺?
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
vector_db = Chroma(persist_directory="./my_book_db", embedding_function=embeddings)


def get_echo_answer_debug_v2(user_input):
    # --- 銆愬叧閿偣 A锛氭绱功绫嶅唴瀹广€?---
    docs = vector_db.similarity_search(user_input, k=3)

    print("\n" + "=" * 60)
    print("馃攳 [DEBUG] 姝ｅ湪妫€鏌ユ暟鎹簱鍖归厤鎯呭喌...")

    if not docs:
        print("鉂?璀﹀憡锛氭暟鎹簱娌℃悳鍒颁换浣曞唴瀹癸紒璇锋鏌?input1.md 鏄惁宸叉垚鍔熷瓨鍏ユ暟鎹簱銆?)
        return

    # 鎵撳嵃鍑轰唬鐮佸埌搴曚粠涔﹂噷鎶撳埌浜嗗摢鍑犳璇?
    context_list = []
    for i, d in enumerate(docs):
        snippet = d.page_content.replace('\n', ' ')
        print(f"馃摉 涔︾睄鍘熸枃鐗囨 [{i + 1}]: {snippet[:150]}...")  # 鎵撳嵃鍓?50瀛?
        context_list.append(d.page_content)

    context_text = "\n".join(context_list)

    # --- 銆愬叧閿偣 B锛氱‘璁?Prompt 缁勫悎銆?---
    # 杩欓噷鎶婁功閲岀殑鍐呭姝ｅ紡濉炶繘娑堟伅閲?
    prompt_messages = [
        {"role": "system", "content": f"浣犲繀椤诲弬鑰冧互涓嬩功绫嶅師鏂囨潵鍥炵瓟锛歕n{context_text}"},
        {"role": "user", "content": user_input}
    ]

    print("馃殌 [DEBUG] 宸插皢涓婅堪鍘熸枃濉炶繘 Prompt锛屽彂閫佺粰 DeepSeek...")

    # --- 銆愬叧閿偣 C锛欰PI 璋冪敤銆?---
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=prompt_messages,
        stream=False
    )

    print(f"馃搳 [DEBUG] 鏈 API 璋冪敤娑堣€?Token: {response.usage.total_tokens}")
    print("=" * 60 + "\n")

    return response.choices[0].message.content


if __name__ == "__main__":
    while True:
        query = input("\n娴嬭瘯鎻愰棶 (杈撳叆 quit 閫€鍑?: ")
        if query.lower() == 'quit': break

        answer = get_echo_answer_debug_v2(query)
        if answer:
            print(f"馃 [Echo 鍥炲]:\n{answer}")
