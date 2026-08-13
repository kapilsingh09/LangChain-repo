"""
YouTube RAG Backend
FastAPI + YouTube Transcript + HuggingFace + FAISS + Conversational Memory
"""

import os
import time
from datetime import datetime, timezone
from operator import itemgetter

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

from langchain_huggingface import (
    ChatHuggingFace,
    HuggingFaceEndpoint,
    HuggingFaceEmbeddings,
)

from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_openai import ChatOpenAI

from langchain_community.vectorstores import FAISS

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.runnables import (
    RunnableParallel,
    RunnableLambda,
    RunnableWithMessageHistory,
)

from langchain_core.chat_history import InMemoryChatMessageHistory


HF_API_KEY = os.getenv("HF_API_KEY")

START_TIME = time.time()


app = FastAPI(
    title="YouTube RAG API",
    description="RAG-based API for asking questions about YouTube videos",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


chat_store = {}

# ─────────────────────────────────────────────
#  CACHE LAYER
#  transcript_cache : video_id → formatted transcript string
#  summary_cache    : video_id → precomputed summary string
# ─────────────────────────────────────────────
transcript_cache: dict[str, str] = {}
summary_cache: dict[str, str] = {}
# ─────────────────────────────────────────────


def get_session_history(session_id: str):
    if session_id not in chat_store:
        chat_store[session_id] = InMemoryChatMessageHistory()
    return chat_store[session_id]


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# ─────────────────────────────────────────────
#  INTENT CLASSIFIER
#  Returns "summary" if query is a summarization request,
#  else returns "qa" for normal RAG flow
# ─────────────────────────────────────────────
SUMMARY_KEYWORDS = [
    "summarize", "summary", "tl;dr", "tldr", "overview",
    "what is this video about", "what's this video about",
    "explain the video", "gist", "brief", "short description",
    "main points", "key points", "what does this video cover",
    "video mein kya hai", "video ka summary", "summary do",
    "summary de", "bata kya hai", "kya bol raha hai video mein",
]

def classify_intent(query: str) -> str:
    query_lower = query.lower().strip()
    for keyword in SUMMARY_KEYWORDS:
        if keyword in query_lower:
            return "summary"
    return "qa"
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
#  SUMMARY GENERATOR
#  Handles short and long transcripts via map-reduce
#  Short  → direct single LLM call
#  Long   → chunk → mini summaries → combine
# ─────────────────────────────────────────────
SUMMARY_CHUNK_SIZE = 4000
DIRECT_SUMMARY_LIMIT = 6000

def generate_summary_stream(transcript: str, llm, video_id: str):
    """Stream summary generation and cache the complete result."""
    token_estimate = len(transcript.split())
    full_response = ""

    if token_estimate < DIRECT_SUMMARY_LIMIT:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Summarize the following YouTube video transcript clearly and concisely, covering all key points."),
            ("human", "{transcript}"),
        ])
        chain = prompt | llm
        for chunk in chain.stream({"transcript": transcript}):
            if hasattr(chunk, "content") and chunk.content:
                full_response += chunk.content
                yield chunk.content
    else:
        words = transcript.split()
        text_chunks = [
            " ".join(words[i: i + SUMMARY_CHUNK_SIZE])
            for i in range(0, len(words), SUMMARY_CHUNK_SIZE)
        ]

        mini_prompt = ChatPromptTemplate.from_messages([
            ("system", "Summarize this section of a YouTube video transcript in 3-4 sentences. Be concise."),
            ("human", "{chunk}"),
        ])
        mini_chain = mini_prompt | llm

        mini_summaries = []
        for text_chunk in text_chunks:
            result = mini_chain.invoke({"chunk": text_chunk})
            mini_summaries.append(result.content)

        combined = "\n\n".join(mini_summaries)

        final_prompt = ChatPromptTemplate.from_messages([
            ("system", "Combine these section summaries into one coherent, well-structured summary of the full YouTube video."),
            ("human", "{combined}"),
        ])
        final_chain = final_prompt | llm
        for chunk in final_chain.stream({"combined": combined}):
            if hasattr(chunk, "content") and chunk.content:
                full_response += chunk.content
                yield chunk.content

    summary_cache[video_id] = full_response


def generate_rag_stream(question, memory_key, conversational_rag_chain):
    """Stream RAG chain response, yielding text chunks progressively."""
    for chunk in conversational_rag_chain.stream(
        {"question": question},
        config={"configurable": {"session_id": memory_key}},
    ):
        if hasattr(chunk, "content") and chunk.content:
            yield chunk.content
# ─────────────────────────────────────────────


class YoutubeSchema(BaseModel):

    session_id: str = Field(
        ...,
        description="Unique ID for the current conversation",
    )

    question: str = Field(
        ...,
        description="Question about the YouTube video",
    )

    youtube_url: str = Field(
        ...,
        description="YouTube video URL",
    )

    model: str = Field(
        ...,
        description="LLM provider/model to use",
    )

    api_key: str | None = Field(
        default=None,
        description="API key for the selected model",
    )


@app.get("/")
def root():
    return {"message": "YouTube RAG API is running"}


@app.get("/health")
def check_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": time.time() - START_TIME,
    }


def get_model(model_name: str, api_key: str | None = None):

    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    if model_name == "free":
        if not HF_API_KEY:
            raise ValueError("HF_API_KEY is not configured.")

        llm_endpoint = HuggingFaceEndpoint(
            repo_id="Qwen/Qwen2.5-7B-Instruct",
            task="text-generation",
            max_new_tokens=512,
            huggingfacehub_api_token=HF_API_KEY,
        )
        llm = ChatHuggingFace(llm=llm_endpoint)
        return llm, embedding

    elif model_name == "gemini":
        if not api_key:
            raise ValueError("API Key is required for Gemini model.")
        print("API Key : ", api_key)
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
        )
        return llm, embedding

    elif model_name == "grok":
        if not api_key:
            raise ValueError("API Key is required for Grok model.")
        print("API Key : ", api_key)
        llm = ChatOpenAI(
            base_url="https://api.x.ai/v1",
            api_key=api_key,
            model="grok-4.5",
        )
        return llm, embedding

    else:
        raise ValueError(f"Unsupported model: {model_name}")


@app.post("/ask")
def ask_youtube_video(payload: YoutubeSchema):

    try:

        youtube_url = payload.youtube_url

        if "v=" not in youtube_url:
            return {"error": "Invalid YouTube URL"}

        video_id = youtube_url.split("v=")[1].split("&")[0]
        memory_key = f"{payload.session_id}:{video_id}"

        # ─────────────────────────────────────────────
        #  TRANSCRIPT FETCH (with cache)
        #  First call fetches from YouTube API and stores in cache.
        #  Subsequent calls for same video skip the API entirely.
        # ─────────────────────────────────────────────
        if video_id in transcript_cache:
            formatted_transcript = transcript_cache[video_id]
        else:
            try:
                transcript = YouTubeTranscriptApi().fetch(video_id)
            except TranscriptsDisabled as e:
                return {
                    "error": "Transcripts are disabled for this video",
                    "details": str(e),
                    "video_id": video_id,
                }

            formatted_transcript = " ".join(
                snippet["text"]
                if isinstance(snippet, dict)
                else getattr(snippet, "text", "")
                for snippet in transcript
            )

            if not formatted_transcript.strip():
                return {"error": "Transcript is empty", "video_id": video_id}

            transcript_cache[video_id] = formatted_transcript
        # ─────────────────────────────────────────────

        llm, embedding = get_model(payload.model, payload.api_key)

        # ─────────────────────────────────────────────
        #  INTENT ROUTING
        #  "summary" intent → return cached/generated summary directly
        #  "qa" intent      → normal RAG retrieval pipeline
        # ─────────────────────────────────────────────
        intent = classify_intent(payload.question)

        if intent == "summary":
            if video_id in summary_cache:
                return StreamingResponse(
                    iter([summary_cache[video_id]]),
                    media_type="text/plain",
                )

            return StreamingResponse(
                generate_summary_stream(formatted_transcript, llm, video_id),
                media_type="text/plain",
            )
        # ─────────────────────────────────────────────

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
        )

        chunks = splitter.create_documents([formatted_transcript])

        vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=embedding,
        )

        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3},
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
You are a helpful YouTube video assistant.

Answer the user's question using the provided
YouTube transcript context and conversation history.

If the answer cannot be found in the transcript,
say that you don't know.

Use the conversation history to understand
references such as "it", "they", "that", etc.

Video Context:

{context}
""",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ])

        parallel_chain = RunnableParallel({
            "context": itemgetter("question") | retriever | RunnableLambda(format_docs),
            "question": itemgetter("question"),
            "chat_history": itemgetter("chat_history"),
        })

        rag_chain = parallel_chain | prompt | llm

        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )

        return StreamingResponse(
            generate_rag_stream(
                payload.question, memory_key, conversational_rag_chain
            ),
            media_type="text/plain",
        )

    except Exception as e:
        print("Error fetching transcript or running RAG:", e)
        return {
            "error": "Failed to process video",
            "details": str(e),
            "video_id": video_id if "video_id" in locals() else None,
            "url": payload.youtube_url,
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8000, reload=True)