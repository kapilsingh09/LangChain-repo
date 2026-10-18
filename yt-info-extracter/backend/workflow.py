"""
LangGraph workflow – ported from main_notebook.ipynb.

Graph:  START → router_node → (chat_node | rag_node | summarizer_node) → END

Markdown export is handled as a separate service call (not a graph node)
so the API can trigger it on‑demand instead of using interrupt_before.
"""
import asyncio
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

from .prompts import (
    ROUTER_SYSTEM_PROMPT,
    CHAT_SYSTEM_PROMPT,
    RAG_SYSTEM_PROMPT,
    SUMMARIZER_SYSTEM_PROMPT,
    RESEARCH_SYSTEM_PROMPT,
)
from .search import (
    is_tavily_configured,
    generate_search_query,
    search_tavily,
    format_web_context,
)

# ── Embedding model (loaded once at import time) ─────────────────────
_embedding = None


def _get_embedding():
    global _embedding
    if _embedding is None:
        _embedding = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
        )
    return _embedding


# Load .env from the same directory as this file
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)

# ── LLM ──────────────────────────────────────────────────────────────
groq_key = os.getenv("GROQ_API_KEY", "").strip("'\" \t\r\n")
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2,
    api_key=groq_key if groq_key else None,
)


class RouteDecision(BaseModel):
    route: Literal["chat", "rag", "summarize", "research"] = Field(
        description=(
            "Choose 'chat' for greetings, casual small talk, or meta-questions. "
            "Choose 'summarize' for summary, TL;DR, overview, or key takeaways of the video. "
            "Choose 'research' when the user asks how to build, implement, code, or plan a project idea "
            "or technical concept mentioned in the video, or asks for external technical research/live search. "
            "Choose 'rag' for specific questions about facts, quotes, timestamps, or content directly covered in the video transcript."
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
    decision = router_llm.invoke(
        [SystemMessage(content=ROUTER_SYSTEM_PROMPT), HumanMessage(content=user_last_msg)]
    )
    return {"route": decision.route}


def chat_node(state: GraphState):
    video_preview = state["transcript"][:800]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CHAT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    chain = prompt | llm
    response = chain.invoke(
        {"video_preview": video_preview, "messages": state["messages"]}
    )
    return {"messages": [response], "route": "chat"}


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
            ("system", RAG_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    chain = prompt | llm
    response = chain.invoke(
        {"context": context_text, "messages": state["messages"]}
    )
    return {"messages": [response], "route": "rag"}


def summarizer_node(state: GraphState):
    transcript_for_summary = state["transcript"][:25000]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SUMMARIZER_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    chain = prompt | llm
    response = chain.invoke(
        {"transcript": transcript_for_summary, "messages": state["messages"]}
    )
    return {"messages": [response], "route": "summarize"}


def research_node(state: GraphState):
    """
    Deep research node that combines retrieved video chunks with
    targeted Tavily internet search to explain project ideas, build plans,
    and architecture without refusing or deflecting.
    """
    user_question = state["messages"][-1].content
    video_id = state.get("video_id", "default")

    # 1. Retrieve grounded video chunks from FAISS
    if video_id in _vector_store_cache:
        _, retriever = _vector_store_cache[video_id]
    else:
        _, retriever = build_vector_store(state["transcript"], video_id)

    retrieved_docs = retriever.invoke(user_question)
    video_context = "\n\n---\n\n".join(doc.page_content for doc in retrieved_docs)

    # 2. Intelligent Tavily web search (only if configured in .env, never crashes if empty)
    web_context = ""
    if is_tavily_configured():
        search_query = generate_search_query(llm, user_question)
        search_results = search_tavily(search_query, max_results=4)
        web_context = format_web_context(search_results, query_used=search_query)
    else:
        web_context = format_web_context([], query_used=None)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RESEARCH_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    chain = prompt | llm
    response = chain.invoke(
        {
            "video_context": video_context,
            "web_context": web_context,
            "messages": state["messages"],
        }
    )
    return {"messages": [response], "route": "research"}


def select_next_node(
    state: GraphState,
) -> Literal["chat_node", "rag_node", "summarizer_node", "research_node"]:
    route = state.get("route", "rag")
    if route == "chat":
        return "chat_node"
    elif route == "summarize":
        return "summarizer_node"
    elif route == "research":
        return "research_node"
    return "rag_node"


# ── Build & compile graph (done once at module load) ─────────────────
def _build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("router_node", router_node)
    builder.add_node("chat_node", chat_node)
    builder.add_node("rag_node", rag_node)
    builder.add_node("summarizer_node", summarizer_node)
    builder.add_node("research_node", research_node)

    builder.add_edge(START, "router_node")
    builder.add_conditional_edges(
        "router_node",
        select_next_node,
        {
            "chat_node": "chat_node",
            "rag_node": "rag_node",
            "summarizer_node": "summarizer_node",
            "research_node": "research_node",
        },
    )
    builder.add_edge("chat_node", END)
    builder.add_edge("rag_node", END)
    builder.add_edge("summarizer_node", END)
    builder.add_edge("research_node", END)

    return builder.compile()


graph = _build_graph()


# ── Streaming Generator ──────────────────────────────────────────────
async def stream_chat_response(messages: list, transcript: str, video_id: str):
    """
    Stream AI responses token-by-token for real-time frontend playback.
    Yields dicts:
      - {"type": "route", "route": route}
      - {"type": "delta", "content": chunk_text}
    """
    user_last_msg = messages[-1].content

    # 1. Routing decision
    decision = await router_llm.ainvoke(
        [SystemMessage(content=ROUTER_SYSTEM_PROMPT), HumanMessage(content=user_last_msg)]
    )
    route = decision.route
    yield {"type": "route", "route": route}

    # 2. Stream according to selected route
    if route == "chat":
        video_preview = transcript[:800]
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", CHAT_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        chain = prompt | llm
        async for chunk in chain.astream(
            {"video_preview": video_preview, "messages": messages}
        ):
            if chunk.content:
                yield {"type": "delta", "content": chunk.content}

    elif route == "summarize":
        transcript_for_summary = transcript[:25000]
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SUMMARIZER_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        chain = prompt | llm
        async for chunk in chain.astream(
            {"transcript": transcript_for_summary, "messages": messages}
        ):
            if chunk.content:
                yield {"type": "delta", "content": chunk.content}

    elif route == "research":
        if video_id in _vector_store_cache:
            _, retriever = _vector_store_cache[video_id]
        else:
            _, retriever = await asyncio.to_thread(build_vector_store, transcript, video_id)

        retrieved_docs = await asyncio.to_thread(retriever.invoke, user_last_msg)
        video_context = "\n\n---\n\n".join(doc.page_content for doc in retrieved_docs)

        web_context = ""
        if is_tavily_configured():
            search_query = await asyncio.to_thread(generate_search_query, llm, user_last_msg)
            search_results = await asyncio.to_thread(search_tavily, search_query, 4)
            web_context = format_web_context(search_results, query_used=search_query)
        else:
            web_context = format_web_context([], query_used=None)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RESEARCH_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        chain = prompt | llm
        async for chunk in chain.astream(
            {
                "video_context": video_context,
                "web_context": web_context,
                "messages": messages,
            }
        ):
            if chunk.content:
                yield {"type": "delta", "content": chunk.content}

    else:  # 'rag'
        if video_id in _vector_store_cache:
            _, retriever = _vector_store_cache[video_id]
        else:
            _, retriever = await asyncio.to_thread(build_vector_store, transcript, video_id)

        retrieved_docs = await asyncio.to_thread(retriever.invoke, user_last_msg)
        context_text = "\n\n---\n\n".join(doc.page_content for doc in retrieved_docs)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RAG_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        chain = prompt | llm
        async for chunk in chain.astream(
            {"context": context_text, "messages": messages}
        ):
            if chunk.content:
                yield {"type": "delta", "content": chunk.content}

