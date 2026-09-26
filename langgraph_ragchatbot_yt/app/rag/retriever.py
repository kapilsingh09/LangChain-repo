from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStoreRetriever

from app.rag.vector_store import create_vector_store
from app.rag.embedding import embedding_model
from app.ingestion.transcript import build_chunks

# In-memory cache: video_id -> retriever
# This avoids rebuilding FAISS on every single message for the same video
_retriever_cache: dict[str, VectorStoreRetriever] = {}


def get_retriever(video_id: str) -> VectorStoreRetriever:
    """
    Return a retriever for the given YouTube video_id.
    Builds the vector store on first call and caches it.
    """
    if video_id not in _retriever_cache:
        print(f"[Retriever] Building vector store for video: {video_id}")
        chunks = build_chunks(video_id)
        vector_store = create_vector_store(chunks, embedding_model)
        _retriever_cache[video_id] = vector_store.as_retriever(search_kwargs={"k": 3})
        print(f"[Retriever] Vector store ready — {len(chunks)} chunks indexed.")
    return _retriever_cache[video_id]