import os
import shutil
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

TARGET_FILE = "../文本/input7.md"
with open(os.path.join(SCRIPT_DIR, TARGET_FILE), 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 先按标题结构切分
headers_to_split_on = [
    ("#", "H1"),
    ("##", "H2"),
    ("###", "H3"),
]
markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on
)
md_splits = markdown_splitter.split_text(content)

# 2. 再按字符长度精细切分
chunk_size = 600
chunk_overlap = 100

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    separators=["\n\n", "\n", "\u3002", "\uff01", "\uff1f", "\uff0c", " ", ""],
)
final_splits = text_splitter.split_documents(md_splits)

print(f"标题层级切分: {len(md_splits)} 个块")
print(f"精细切分后: {len(final_splits)} 个块")

# 3. 每次重建前先删旧的，保证是最新的
DB_PATH = os.path.join(SCRIPT_DIR, "./my_book_db")
if os.path.exists(DB_PATH):
    shutil.rmtree(DB_PATH)
    print("已删除旧数据库，准备重建")

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

vector_db = Chroma.from_documents(
    documents=final_splits,
    embedding=embeddings,
    persist_directory=DB_PATH
)

print(f"数据库构建完成！共 {len(final_splits)} 个块")
