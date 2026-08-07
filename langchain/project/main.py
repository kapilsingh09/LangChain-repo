# ============================================================
# YouTube RAG Backend
# FastAPI + YouTube Transcript + HuggingFace + FAISS
# + Conversational Memory
# ============================================================

import time
from datetime import datetime, timezone
from operator import itemgetter

from fastapi import FastAPI
from pydantic import BaseModel, Field

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled
)

from langchain_huggingface import (
    ChatHuggingFace,
    HuggingFaceEndpoint,
    HuggingFaceEmbeddings
)

from langchain_community.vectorstores import FAISS

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from langchain_core.runnables import (
    RunnableParallel,
    RunnablePassthrough,
    RunnableLambda,
    RunnableWithMessageHistory
)

from langchain_core.chat_history import InMemoryChatMessageHistory

from langchain_core.output_parsers import StrOutputParser


# CONFIGURATION

HF_API_KEY = ""

START_TIME = time.time()


# FASTAPI APPLICATION

app = FastAPI(
    title="YouTube RAG API",
    description="RAG-based API for asking questions about YouTube videos",
    version="1.0.0"
)


# NEW: CHAT MEMORY STORE

# This dictionary stores conversation history.
#
# Example:
#
# chat_store = {
#     "user123_video456": [
#         HumanMessage(...),
#         AIMessage(...)
#     ]
# }
#
# For now this lives in RAM.
#
# IMPORTANT:
# If the FastAPI server restarts,
# this memory will be lost.
#
# Later we can replace this with Redis.

chat_store = {}


# NEW: GET CHAT HISTORY
def get_session_history(session_id: str):
    """
    Return the chat history for a particular session.

    If the session does not exist yet,
    create a new conversation history.
    """

    if session_id not in chat_store:
        chat_store[session_id] = InMemoryChatMessageHistory()

    return chat_store[session_id]

# HELPER FUNCTION   

def format_docs(docs):
    """
    Convert retrieved LangChain Documents into
    one single context string.
    """

    context_text = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    return context_text


# ============================================================
# REQUEST SCHEMA
# ============================================================

class YoutubeSchema(BaseModel):
    """
    Defines the data sent by the frontend/extension.
    """

    # CHANGED:
    # Added session_id so we know which conversation
    # this question belongs to.

    session_id: str = Field(
        ...,
        description="Unique ID for the current conversation"
    )

    question: str = Field(
        ...,
        description="The question to ask about the YouTube video"
    )

    youtube_url: str = Field(
        ...,
        description="The YouTube URL of the video"
    )


# ============================================================
# ROOT ROUTE
# ============================================================

@app.get("/")
def root():
    """
    Basic route to check whether the API is running.
    """

    return {
        "message": "YouTube RAG API is running"
    }


# ============================================================
# HEALTH CHECK ROUTE
# ============================================================

@app.get("/health")
def check_health():
    """
    Returns the health status and uptime of the API.
    """

    uptime_seconds = time.time() - START_TIME

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds
    }


# ============================================================
# MAIN YOUTUBE RAG ROUTE
# ============================================================

@app.post("/ask")
def ask_youtube_video(payload: YoutubeSchema):
    """
    Main conversational RAG endpoint.

    Flow:

    YouTube URL
        ↓
    Extract Video ID
        ↓
    Fetch Transcript
        ↓
    Split Transcript
        ↓
    Create Embeddings
        ↓
    FAISS
        ↓
    Retriever
        ↓
    Retrieve Video Context
        ↓
    Get Chat History
        ↓
    Prompt
        ↓
    LLM
        ↓
    Save New Question + Answer
        ↓
    Return Answer
    """

    try:

        # ----------------------------------------------------
        # 1. Extract YouTube Video ID
        # ----------------------------------------------------

        youtube_url = payload.youtube_url

        if "v=" not in youtube_url:
            return {
                "error": "Invalid YouTube URL"
            }

        video_id = youtube_url.split("v=")[1].split("&")[0]


        # ----------------------------------------------------
        # NEW:
        # Create a memory key using BOTH session and video.
        #
        # This prevents conversation from one video
        # accidentally mixing with another video.
        # ----------------------------------------------------

        memory_key = f"{payload.session_id}:{video_id}"


        # ----------------------------------------------------
        # 2. Fetch YouTube Transcript
        # ----------------------------------------------------

        ytt_api = YouTubeTranscriptApi()

        try:

            transcript = ytt_api.fetch(video_id)

        except TranscriptsDisabled as e:

            return {
                "error": "Transcripts are disabled for this video",
                "details": str(e),
                "video_id": video_id
            }


        # ----------------------------------------------------
        # 3. Convert Transcript Objects into Text
        # ----------------------------------------------------

        formatted_transcript = " ".join(
            snippet.text
            for snippet in transcript
        )


        # ----------------------------------------------------
        # 4. Split Transcript into Chunks
        # ----------------------------------------------------

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150
        )

        chunks = splitter.create_documents(
            [formatted_transcript]
        )


        # ----------------------------------------------------
        # 5. Create HuggingFace LLM
        # ----------------------------------------------------

        llm = HuggingFaceEndpoint(
            repo_id="Qwen/Qwen2.5-7B-Instruct",
            task="text-generation",
            max_new_tokens=512,
            huggingfacehub_api_token=HF_API_KEY
        )

        model = ChatHuggingFace(
            llm=llm
        )


        # ----------------------------------------------------
        # 6. Create Embedding Model
        # ----------------------------------------------------

        embedding = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )


        # ----------------------------------------------------
        # 7. Create FAISS Vector Store
        # ----------------------------------------------------

        vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=embedding
        )


        # ----------------------------------------------------
        # 8. Create Retriever
        # ----------------------------------------------------

        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 3
            }
        )


        # ====================================================
        # CHANGED:
        # We now use ChatPromptTemplate instead of
        # PromptTemplate because we have chat history.
        # ====================================================

        prompt = ChatPromptTemplate.from_messages([

            (
                "system",
                """
You are a helpful YouTube video assistant.

Answer the user's question using the provided
YouTube transcript context and conversation history.

The transcript context is the primary source
of factual information about the video.

If the answer cannot be found in the transcript,
say that you don't know.

Use the conversation history to understand
references such as:

"it"
"they"
"that"
"the previous topic"
"why is it useful"

Video Context:
{context}
"""
            ),

            # =================================================
            # NEW:
            # This is where previous conversation messages
            # will be inserted.
            # =================================================

            MessagesPlaceholder(
                variable_name="chat_history"
            ),

            (
                "human",
                "{question}"
            )
        ])


        # ====================================================
        # CHANGED:
        # The chain now receives:
        #
        # question
        # chat_history
        #
        # The question goes to the retriever.
        # The history goes to the prompt.
        # ====================================================

        parallel_chain = RunnableParallel({

            # Current question
            # ↓
            # Retriever
            # ↓
            # Relevant video documents
            # ↓
            # Formatted context

            "context": (
                itemgetter("question")
                | retriever
                | RunnableLambda(format_docs)
            ),

            # Keep current question
            "question": itemgetter("question"),

            # NEW:
            # Pass conversation history to the prompt

            "chat_history": itemgetter("chat_history")

        })


        # ====================================================
        # CHANGED:
        # We don't use StrOutputParser here.
        #
        # Why?
        #
        # RunnableWithMessageHistory needs the AIMessage
        # so it can save the assistant's response
        # into the conversation history.
        # ====================================================

        rag_chain = (
            parallel_chain
            | prompt
            | model
        )


        # ====================================================
        # NEW:
        # Add conversation memory to our RAG chain.
        # ====================================================

        conversational_rag_chain = RunnableWithMessageHistory(

            rag_chain,

            # Function that returns the history
            get_session_history,

            # Name of the input containing user's question
            input_messages_key="question",

            # Name of the variable containing chat history
            history_messages_key="chat_history"
        )


        # ====================================================
        # NEW:
        # Invoke the conversational RAG chain.
        # ====================================================

        response = conversational_rag_chain.invoke(

            {
                "question": payload.question
            },

            config={
                "configurable": {
                    "session_id": memory_key
                }
            }
        )


        # ====================================================
        # Return Response
        # ====================================================

        return {
            "answer": response.content,
            "video_id": video_id,
            "session_id": payload.session_id,
            "transcript_length": len(formatted_transcript),
            "chunks": len(chunks)
        }


    # ========================================================
    # GLOBAL ERROR HANDLING
    # ========================================================

    except Exception as e:

        print(
            "Error fetching transcript or running RAG:",
            e
        )

        return {
            "error": "Failed to process video",
            "details": str(e),
            "video_id": video_id if "video_id" in locals() else None,
            "url": payload.youtube_url
        }
