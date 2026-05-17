import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "./my_book_db_v2")

print(f"加载数据库: {DB_PATH}")
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
vector_db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

print("\n输入问题开始检索（输入 q 退出）")
print("=" * 50)

while True:
    query = input("\n问题: ").strip()
    if query.lower() in ("q", "quit", "exit"):
        break
    if not query:
        continue
    docs = vector_db.similarity_search_with_score(query, k=5)
    print(f"\n检索到 {len(docs)} 个相关片段:\n")
    for i, (doc, score) in enumerate(docs):
        print(f"--- [{i+1}] 相关度得分: {score:.4f} ---")
        print(f"来源: {doc.metadata}")
        content_preview = doc.page_content[:200]
        if len(doc.page_content) > 200:
            content_preview += "..."
        print(f"内容: {content_preview}\n")
