import os
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# 1. 读取并切片
with open("input1.md", 'r', encoding='utf-8') as f:
    content = f.read()

splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("#", "H1"), ("##", "H2")])
splits = splitter.split_text(content)
print(f"✅ 准备存入 {len(splits)} 个知识块")

# 2. 构建并强制保存
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

# 使用 from_documents 会自动触发向量化
vector_db = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    persist_directory="./my_book_db"
)

# 这一步非常关键：确保数据写进了硬盘
print("💾 正在将数据持久化到硬盘...")
# 如果是新版 LangChain，其实这一步是自动的，但我们要确保看到 my_book_db 文件夹里有文件生成
print("🎉 数据库构建完成！")