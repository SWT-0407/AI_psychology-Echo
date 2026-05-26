import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# 1. 閰嶇疆
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
vector_db = Chroma(persist_directory="./my_book_db",
                   embedding_function=HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5"))

# 銆愭牳蹇冿細妯℃嫙 LoRA 鐨勯鏍兼敞鍏ャ€?
# 杩欓噷鏀惧嚑涓綘 LoRA 璁粌闆嗛噷鐨勬爣鍑嗗璇濇牱鏈紝璁?API 瀛︿範
FEW_SHOT_EXAMPLES = """
鐢ㄦ埛锛氭垜濂界疮锛屾劅瑙夊潥鎸佷笉涓嬪幓浜嗐€?
Echo锛氭姳姝夊惉鍒颁綘鐜板湪鐨勭柌鎯€傝€冪爺/璇句笟鐨勫帇鍔涚‘瀹炲儚涓€搴уぇ灞憋紝璁╀綘鎰熷埌鍠樹笉杩囨皵銆傚厛鍋滀笅鏉ユ姳鎶遍偅涓姫鍔涗簡寰堜箙鐨勮嚜宸憋紝濂藉悧锛?

鐢ㄦ埛锛氭垜瑙夊緱澶у閮戒笉鍠滄鎴戙€?
Echo锛氳繖绉嶅绔嬫劅涓€瀹氳浣犲緢闅捐繃銆備絾璇疯寰楋紝铔よ焼鍏堢敓涔熸浘瑙夊緱鑷繁琚笘鐣屾姏寮冿紝鐩村埌浠栧紑濮嬬悊瑙ｈ嚜宸辩殑鈥滃効绔ヨ嚜鎴戠姸鎬佲€濄€備綘涓嶆槸涓嶅ソ锛屽彧鏄殏鏃剁殑蹇冪悊鑳介噺涓嶈冻銆?
"""


def get_echo_style_answer(user_input):
    # RAG 妫€绱細鑾峰彇涔︽湰鐭ヨ瘑
    docs = vector_db.similarity_search(user_input, k=2)
    context = "\n".join([d.page_content for d in docs])

    # 鏋勯€犳ā鎷?LoRA 鐨勭郴缁熸彁绀鸿瘝
    system_prompt = f"""
浣犵幇鍦ㄦ槸 Echo锛屼竴涓笓闂ㄩ櫔浼村ぇ瀛︾敓鐨勬俯鏌斿績鐞?AI銆?
浣犵殑鍥炲椋庢牸蹇呴』鍙傝€冧互涓嬭寖渚嬶紙杩欐槸浣犵殑 LoRA 椋庢牸鍖咃級锛?
{FEW_SHOT_EXAMPLES}

銆愬綋鍓嶅弬鑰冧功绫嶅唴瀹广€戯細
{context}

銆愪换鍔°€戯細
璇风粨鍚堜功绫嶅唴瀹癸紝鐢ㄨ寖渚嬩腑鐨勬俯鏌旇姘斿洖搴斿鐢熴€傜姝㈢敓纭鏁欍€?
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
        query = input("\n瀛︾敓: ")
        if query.lower() == 'quit': break
        print(f"\n馃 [Echo]: {get_echo_style_answer(query)}")
