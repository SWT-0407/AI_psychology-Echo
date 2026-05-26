import os
from langchain_community.document_loaders import UnstructuredEPubLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 1. 加载 EPUB 文件
file_path = "你的书名.epub"
loader = UnstructuredEPubLoader(file_path)
data = loader.load()

# 2. 文本切片 (Chunking)
# chunk_size 是每段的大小，chunk_overlap 是段落间的重叠部分，防止语义被切断
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
all_splits = text_splitter.split_documents(data)

# 3. 初始化 Embedding 模型 (推荐中文效果好的 BGE)
# 第一次运行会自动下载模型，约 400MB
model_name = "BAAI/bge-small-zh-v1.5"
encode_kwargs = {'normalize_embeddings': True}
embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    encode_kwargs=encode_kwargs
)

# 4. 创建并持久化向量数据库
# 执行完后，本地会生成一个 'db_book' 文件夹，里面存的就是向量数据
vectorstore = Chroma.from_documents(
    documents=all_splits,
    embedding=embeddings,
    persist_directory="./db_book"
)

print(f"导入成功！共切分为 {len(all_splits)} 个知识块。")