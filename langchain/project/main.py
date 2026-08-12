"""
YouTube RAG Backend
FastAPI + YouTube Transcript + HuggingFace + FAISS + Conversational Memory
"""

import time
from datetime import datetime, timezone
from operator import itemgetter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnableParallel, RunnableLambda, RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

# Configuration
HF_API_KEY = ""
START_TIME = time.time()

app = FastAPI(
    title="YouTube RAG API",
    description="RAG-based API for asking questions about YouTube videos",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for conversational history.
# Maps session_id to InMemoryChatMessageHistory.
# Note: Data is lost on server restart. Use Redis for production.
chat_store = {}

def get_session_history(session_id: str):
    """Retrieves or creates the chat history for a given session."""
    if session_id not in chat_store:
        chat_store[session_id] = InMemoryChatMessageHistory()
    return chat_store[session_id]

def format_docs(docs):
    """Combines retrieved LangChain Documents into a single context string."""
    return "\n\n".join(doc.page_content for doc in docs)

class YoutubeSchema(BaseModel):
    """Payload schema for the /ask endpoint."""
    session_id: str = Field(..., description="Unique ID for the current conversation")
    question: str = Field(..., description="The question to ask about the YouTube video")
    youtube_url: str = Field(..., description="The YouTube URL of the video")
    model: str = Field(...,description="The model to use for the RAG API")

@app.get("/")
def root():
    """Basic route to check whether the API is running."""
    return {"message": "YouTube RAG API is running"}

@app.get("/health")
def check_health():
    """Returns the health status and uptime of the API."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": time.time() - START_TIME
    }

@app.post("/ask")
def ask_youtube_video(payload: YoutubeSchema):
    """
    Main conversational RAG endpoint.
    Extracts transcript, chunks text, creates embeddings, retrieves relevant 
    context via FAISS, and queries the LLM using conversation history.
    """
    try:
        # Extract YouTube Video ID
        youtube_url = payload.youtube_url
        if "v=" not in youtube_url:
            return {"error": "Invalid YouTube URL"}
        video_id = youtube_url.split("v=")[1].split("&")[0]

        # Unique memory key per session and video
        memory_key = f"{payload.session_id}:{video_id}"

        # Fetch Transcript
        try:
            transcript = YouTubeTranscriptApi().fetch(video_id)
        except TranscriptsDisabled as e:
            return {
                "error": "Transcripts are disabled for this video",
                "details": str(e),
                "video_id": video_id
            }

        # Handle transcript objects (usually dicts with a 'text' key)
        formatted_transcript = " ".join(
            snippet["text"] if isinstance(snippet, dict) else getattr(snippet, "text", "")
            for snippet in transcript
        )

        # Split Transcript
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.create_documents([formatted_transcript])

        model = payload.model


        if model == "gemini":
            pass
        elif model == "grok":
            pass
        elif model == "free":
        # Initialize LLM and Embeddings
            llm = HuggingFaceEndpoint(
                repo_id="Qwen/Qwen2.5-7B-Instruct",
                task="text-generation",
                max_new_tokens=512,
                huggingfacehub_api_token=HF_API_KEY
            )
            model = ChatHuggingFace(llm=llm)
            embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

            # Create Vector Store and Retriever
        vector_store = FAISS.from_documents(documents=chunks, embedding=embedding)
        retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

        # Define Prompt Template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful YouTube video assistant.
Answer the user's question using the provided YouTube transcript context and conversation history.
If the answer cannot be found in the transcript, say that you don't know.
Use the conversation history to understand references like "it", "they", "that".

Video Context:
{context}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])

        # Build Retrieval Chain
        parallel_chain = RunnableParallel({
            "context": itemgetter("question") | retriever | RunnableLambda(format_docs),
            "question": itemgetter("question"),
            "chat_history": itemgetter("chat_history")
        })

        rag_chain = parallel_chain | prompt | model

        # Add Conversational Memory
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history"
        )

        # Invoke the chain
        response = conversational_rag_chain.invoke(
            {"question": payload.question},
            config={"configurable": {"session_id": memory_key}}
        )

        return {
            "answer": response.content,
            "video_id": video_id,
            "session_id": payload.session_id,
            "transcript_length": len(formatted_transcript),
            "chunks": len(chunks)
        }

    except Exception as e:
        print("Error fetching transcript or running RAG:", e)
        return {
            "error": "Failed to process video",
            "details": str(e),
            "video_id": video_id if "video_id" in locals() else None,
            "url": payload.youtube_url
        }
