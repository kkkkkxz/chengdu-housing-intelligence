"""
RAG 工具模块 - LangChain 0.3.x 新 API 实现
- 使用 LCEL + RunnableWithMessageHistory
- 使用 HuggingFace 镜像加速模型下载
- 支持多 session 对话历史
- 向量库持久化 (FAISS)
"""

import os
import sys
from pathlib import Path
from typing import Dict
from operator import itemgetter

# ========== 关键修复1：设置 HuggingFace 镜像（解决网络问题）==========
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# LangChain 组件
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import CSVLoader
# ========== 关键修复2：使用新的 langchain_huggingface 包 ==========
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

# ================== 配置常量（延迟获取 Django settings）==================
def get_csv_file_path():
    from django.conf import settings
    # 根据你的实际文件名调整
    return settings.BASE_DIR / 'data' / 'processed_data_with_images_cleaned.csv'

def get_faiss_index_dir():
    from django.conf import settings
    return settings.BASE_DIR / 'vectorstore' / 'faiss_houserag'

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 20
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
RETRIEVAL_K = 4

# ================== 全局缓存 ==================
_vectorstore = None
_llm = None
_session_store: Dict[str, ChatMessageHistory] = {}

# ================== 1. LLM 初始化 ==================
def get_llm():
    global _llm
    if _llm is None:
        from django.conf import settings
        _llm = ChatOpenAI(
            base_url=settings.MODELSCOPE_BASE_URL,
            api_key=settings.MODELSCOPE_API_KEY,
            model=settings.MODELSCOPE_MODEL_ID,
            temperature=0,
            max_tokens=1024,
            timeout=60
        )
    return _llm

# ================== 2. 向量库构建 / 加载 ==================
def get_vectorstore(force_rebuild: bool = False):
    global _vectorstore
    if _vectorstore is not None and not force_rebuild:
        return _vectorstore

    csv_path = get_csv_file_path()
    faiss_dir = get_faiss_index_dir()

    # 尝试从缓存加载
    index_file = faiss_dir / 'index.faiss'
    if not force_rebuild and index_file.exists():
        print(f"[RAG] 从缓存加载向量库: {faiss_dir}")
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        _vectorstore = FAISS.load_local(
            str(faiss_dir),
            embeddings,
            allow_dangerous_deserialization=True
        )
        return _vectorstore

    # 构建新索引
    print(f"[RAG] 开始构建向量库，CSV: {csv_path}")
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 文件不存在: {csv_path}")

    loader = CSVLoader(
        str(csv_path),
        encoding='utf-8',
        csv_args={'delimiter': ','}
    )
    documents = loader.load()
    print(f"[RAG] 加载了 {len(documents)} 条原始记录")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "，", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    print(f"[RAG] 文档已分为 {len(chunks)} 个文本块")

    # 使用镜像下载模型
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    _vectorstore = FAISS.from_documents(chunks, embeddings)

    faiss_dir.mkdir(parents=True, exist_ok=True)
    _vectorstore.save_local(str(faiss_dir))
    print(f"[RAG] 向量库已保存至 {faiss_dir}")

    return _vectorstore

# ================== 3. 构建 LCEL 链 ==================
def build_lcel_chain():
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的房产问答助手。请根据以下检索到的上下文和对话历史回答用户问题。\n\n上下文：\n{context}"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])

    chain = (
        {
            "context": itemgetter("question") | retriever,
            "question": itemgetter("question"),
            "history": itemgetter("history")
        }
        | prompt
        | get_llm()
        | StrOutputParser()
    )
    return chain

# ================== 4. 会话历史管理 ==================
def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in _session_store:
        _session_store[session_id] = ChatMessageHistory()
    return _session_store[session_id]

def get_rag_with_history():
    chain = build_lcel_chain()
    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history"
    )

# ================== 5. 对外接口 ==================
def ask_question(question: str, session_id: str = "default", force_rebuild: bool = False) -> str:
    if force_rebuild:
        global _vectorstore
        _vectorstore = None

    qa_with_history = get_rag_with_history()
    response = qa_with_history.invoke(
        {"question": question},
        config={"configurable": {"session_id": session_id}}
    )
    return response

def rebuild_index():
    global _vectorstore
    _vectorstore = None
    get_vectorstore(force_rebuild=True)
    print("[RAG] 向量库重建完成")

def clear_session_history(session_id: str):
    if session_id in _session_store:
        _session_store[session_id].clear()
        print(f"[RAG] 已清除会话 '{session_id}' 的历史")
