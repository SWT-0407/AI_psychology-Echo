"""
RAG 知识检索服务（基于 FAISS）
连接 FAISS 向量索引，根据用户输入检索最相关的书籍知识片段
"""
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# 数据库路径（使用不含中文的路径，避免 FAISS 编码问题）
FAISS_DIR = r"E:\faiss_db"

# 全局单例
_vector_db = None


def get_vector_db():
    """获取向量数据库实例（懒加载）"""
    global _vector_db
    if _vector_db is None:
        embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
        _vector_db = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
    return _vector_db


def search_relevant_knowledge(query, k=3):
    """
    从知识库中检索与 query 最相关的内容
    
    Args:
        query: 用户输入或对话上下文
        k: 返回的最相关片段数量
    
    Returns:
        str: 组合后的知识上下文文本
    """
    try:
        db = get_vector_db()
        docs = db.similarity_search(query, k=k)
        if not docs:
            return ""
        
        # 组合成知识上下文
        parts = []
        for i, doc in enumerate(docs):
            content = doc.page_content.strip()
            if content:
                parts.append(f"[书籍知识 {i+1}] {content}")
        
        return "\n\n".join(parts)
    except Exception as e:
        print(f"[RAG 检索异常] {e}")
        return ""
