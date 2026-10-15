"""
LangGraph workflow – ported from main_notebook.ipynb.

Graph:  START → router_node → (chat_node | rag_node | summarizer_node) → END

Markdown export is handled as a separate service call (not a graph node)
so the API can trigger it on‑demand instead of using interrupt_before.
"""
import os
import re
from typing import Annotated, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from dotenv import load_dotenv

# Load .env from the same directory as this file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── Embedding model (loaded once at import time) ─────────────────────
_embedding = None


def _get_embedding():
    global _embedding
    if _embedding is None:
        _embedding = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
        )
    return _embedding


# ── LLM ──────────────────────────────────────────────────────────────
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.2)


class RouteDecision(BaseModel):
    route: Literal["chat", "rag", "summarize"] = Field(
        description=(
            "Choose 'chat' for greetings, small talk, or general questions. "
            "Choose 'rag' for specific questions about facts, details, or topics in the video. "
            "Choose 'summarize' for summary, TL;DR, overview, or key takeaways."
        )
    )


router_llm = llm.with_structured_output(RouteDecision)

# ── Vector‑store cache (per video_id) ────────────────────────────────
_vector_store_cache: dict = {}


# ── Transcript helpers ───────────────────────────────────────────────
def get_video_id(url_or_id: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    m = re.search(
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", url_or_id
    )
    if not m:
        raise ValueError("Not a valid YouTube URL or video ID")
    return m.group(1)


def get_transcript(url_or_id: str, preferred_langs=("en", "hi")):
    """Return (full_text_with_timestamps, list_of_segment_dicts)."""
    video_id = get_video_id(url_or_id)
    try:
        transcript_list = YouTubeTranscriptApi().list(video_id)
        try:
            transcript = transcript_list.find_transcript(list(preferred_langs))
        except NoTranscriptFound:
            available = sorted(
                list(transcript_list), key=lambda t: t.is_generated
            )
            if not available:
                raise ValueError("No transcripts available for this video")
            transcript = available[0]

        fetched = transcript.fetch()
        segments = []
        text_parts = []
        for snippet in fetched:
            start_secs = int(snippet.start)
            mins, secs = divmod(start_secs, 60)
            ts = f"[{mins}:{secs:02d}]"
            segments.append(
                {
                    "text": snippet.text,
                    "start": float(snippet.start),
                    "duration": float(snippet.duration),
                    "timestamp": ts,
                }
            )
            text_parts.append(f"{ts} {snippet.text}")

        full_text = " ".join(text_parts).replace("\n", " ")
        return full_text, segments

    except TranscriptsDisabled:
        raise ValueError("Captions are disabled for this video")


# ── Vector store builder ─────────────────────────────────────────────
def build_vector_store(transcript_text: str, video_id: str):
    """Build (or return cached) FAISS vector store + MMR retriever."""
    if video_id in _vector_store_cache:
        return _vector_store_cache[video_id]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(transcript_text)
    docs = [
        Document(page_content=chunk, metadata={"chunk_id": i})
        for i, chunk in enumerate(chunks)
    ]

    vector_store = FAISS.from_documents(docs, _get_embedding())
    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 4, "fetch_k": 12, "lambda_mult": 0.7},
    )

    _vector_store_cache[video_id] = (vector_store, retriever)
    return vector_store, retriever


# ── Graph State ──────────────────────────────────────────────────────
class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    transcript: str
    route: str
    video_id: str


# ── Nodes ────────────────────────────────────────────────────────────
def router_node(state: GraphState):
    user_last_msg = state["messages"][-1].content
    system_prompt = (
        "You are an intelligent intent router for a YouTube Video Assistant.\n"
        "Analyze the user's latest input and decide which node should handle it:\n"
        "1. 'chat': Greetings, casual conversation, thanking the bot, or meta-questions.\n"
        "2. 'rag': Specific questions about facts, details, timestamps, or topics in the video.\n"
        "3. 'summarize': Requests to summarize the video, list key takeaways, or give an overview."
    )
    decision = router_llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_last_msg)]
    )
    return {"route": decision.route}


def chat_node(state: GraphState):
    video_preview = state["transcript"][:800]
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a friendly, sharp YouTube AI assistant. Handle greetings, casual chat, "
                "and follow-up conversation naturally. You have access to our full conversation "
                "history below.\nFor context, here is a preview of the loaded video transcript "
                "so you know the general topic:\n{video_preview}...",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    chain = prompt | llm
    response = chain.invoke(
        {"video_preview": video_preview, "messages": state["messages"]}
    )
    return {"messages": [response]}


def rag_node(state: GraphState):
    user_question = state["messages"][-1].content
    video_id = state.get("video_id", "default")

    if video_id in _vector_store_cache:
        _, retriever = _vector_store_cache[video_id]
    else:
        _, retriever = build_vector_store(state["transcript"], video_id)

    retrieved_docs = retriever.invoke(user_question)
    context_text = "\n\n---\n\n".join(doc.page_content for doc in retrieved_docs)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert YouTube RAG assistant. Answer the user's question "
                "accurately using ONLY the provided transcript context and our conversation "
                "history. Whenever timestamps like [MM:SS] are present in the context, cite "
                "them in your answer! If the answer is not in the transcript, say so honestly."
                "\n\nRetrieved Transcript Chunks:\n{context}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    chain = prompt | llm
    response = chain.invoke(
        {"context": context_text, "messages": state["messages"]}
    )
    return {"messages": [response]}


def summarizer_node(state: GraphState):
    transcript_for_summary = state["transcript"][:25000]
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert video summarizer. Based on the video transcript below, "
                "fulfill the user's summary request. Structure your response with:\n"
                "1. **Core Theme** (1-2 sentences)\n"
                "2. **Key Takeaways & Timestamps** (Bullet points with [MM:SS] timestamps)\n"
                "3. **Conclusion / Actionable Insight**\n\n"
                "Video Transcript:\n{transcript}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    chain = prompt | llm
    response = chain.invoke(
        {"transcript": transcript_for_summary, "messages": state["messages"]}
    )
    return {"messages": [response]}


def select_next_node(
    state: GraphState,
) -> Literal["chat_node", "rag_node", "summarizer_node"]:
    if state["route"] == "chat":
        return "chat_node"
    elif state["route"] == "summarize":
        return "summarizer_node"
    return "rag_node"


# ── Build & compile graph (done once at module load) ─────────────────
def _build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("router_node", router_node)
    builder.add_node("chat_node", chat_node)
    builder.add_node("rag_node", rag_node)
    builder.add_node("summarizer_node", summarizer_node)

    builder.add_edge(START, "router_node")
    builder.add_conditional_edges(
        "router_node",
        select_next_node,
        {
            "chat_node": "chat_node",
            "rag_node": "rag_node",
            "summarizer_node": "summarizer_node",
        },
    )
    builder.add_edge("chat_node", END)
    builder.add_edge("rag_node", END)
    builder.add_edge("summarizer_node", END)

    return builder.compile()


graph = _build_graph()
