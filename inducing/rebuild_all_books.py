"""
重建 FAISS 知识库：将 文本/input1.md ~ input7.md 全部导入 FAISS 向量索引
运行方式：python rebuild_all_books.py
"""
import os, shutil
from langchain_text_splitters import MarkdownHeaderTextSplitter,RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

SRC = os.path.dirname(os.path.abspath(__file__))
TEXT = os.path.join(SRC, "文本")
DB_DIR = r"E:\faiss_db"  # 使用无中文路径避免 FAISS 编码问题

all_splits = []
fx = MarkdownHeaderTextSplitter([("#","H1"),("##","H2"),("###","H3")])
tx = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100, separators=["\n\n","\n","。","！","？","，"," ",""])

for i in range(1,8):
    fp = os.path.join(TEXT, f"input{i}.md")
    if not os.path.exists(fp): continue
    c = open(fp, encoding="utf-8").read()
    m = fx.split_text(c)
    s = tx.split_documents(m)
    print(f"input{i}.md: {len(m)}标题块 -> {len(s)}知识块")
    all_splits.extend(s)

print(f"\n共{len(all_splits)}个知识块")

if os.path.exists(DB_DIR):
    shutil.rmtree(DB_DIR)
os.makedirs(DB_DIR, exist_ok=True)

emb = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
db = FAISS.from_documents(all_splits, emb)
db.save_local(DB_DIR)
print(f"完成！FAISS 索引已保存到 {DB_DIR}")

# 验证
db2 = FAISS.load_local(DB_DIR, emb, allow_dangerous_deserialization=True)
test = db2.similarity_search("情绪", k=1)
print(f"验证通过：检索到 {len(test)} 条结果")
