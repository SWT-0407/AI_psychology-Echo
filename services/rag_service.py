"""
RAG 检索服务模块
从 ChromaDB 向量数据库中检索相关心理学知识，增强 AI 回复的专业性。
"""
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os

# 数据库路径
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "my_book_db")

# 全局单例
_embeddings = None
_vector_db = None


def _get_embeddings():
    """获取嵌入模型（单例）"""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-zh-v1.5"
        )
    return _embeddings


def _get_vector_db():
    """获取向量数据库连接（单例）"""
    global _vector_db
    if _vector_db is None:
        _vector_db = Chroma(
            collection_name="langchain",
            embedding_function=_get_embeddings(),
            persist_directory=DB_DIR
        )
    return _vector_db


def search_knowledge(query: str, k: int = 3) -> str:
    """
    根据用户输入检索相关心理学知识

    Args:
        query: 用户输入的文本
        k: 返回的相关文档数量

    Returns:
        str: 格式化的知识上下文文本
    """
    try:
        db = _get_vector_db()
        results = db.similarity_search(query, k=k)

        if not results:
            return ""

        knowledge_parts = []
        for i, doc in enumerate(results, 1):
            content = doc.page_content.strip()
            if len(content) > 500:
                content = content[:500] + "..."
            knowledge_parts.append(f"[参考{i}]\n{content}")

        return "\n\n".join(knowledge_parts)

    except Exception as e:
        print(f"[RAG] 知识检索失败: {e}")
        return ""
