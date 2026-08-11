# YouTube RAG API

This project provides a **Conversational RAG (Retrieval-Augmented Generation) API** built with FastAPI and LangChain. It allows users to ask questions about a YouTube video's content, maintaining context over a conversational session.

## Features

- **YouTube Transcript Extraction**: Automatically fetches transcripts from YouTube videos using `youtube-transcript-api`.
- **RAG Pipeline**: Splits the transcript, creates vector embeddings (using `sentence-transformers/all-MiniLM-L6-v2`), and stores them in a FAISS vector database.
- **Conversational Memory**: Maintains chat history for each session in memory, allowing users to ask follow-up questions with proper context.
- **HuggingFace Integration**: Uses the `Qwen/Qwen2.5-7B-Instruct` model via HuggingFace for intelligent, context-aware answers.

## Prerequisites

1. Python 3.8+
2. A HuggingFace API Token (you will need to insert this in `main.py` where `HF_API_KEY` is defined).

## Installation

Install the required dependencies:

```bash
pip install fastapi uvicorn pydantic youtube-transcript-api langchain-huggingface langchain-community langchain-core langchain-text-splitters faiss-cpu sentence-transformers
```

## Running the API

Start the FastAPI server using `uvicorn`:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

### 1. `GET /`
Health check to verify the API is running.

### 2. `GET /health`
Returns the health status and uptime of the API.

### 3. `POST /ask`
Main endpoint to ask questions about a video.

**Request Payload:**
```json
{
  "session_id": "unique-session-id-123",
  "question": "What is this video about?",
  "youtube_url": "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
}
```

**Response:**
```json
{
  "answer": "The generated answer from the AI...",
  "video_id": "YOUR_VIDEO_ID",
  "session_id": "unique-session-id-123",
  "transcript_length": 5432,
  "chunks": 6
}
```

## Project Structure

- `main.py`: Contains the entire FastAPI application, including the LangChain conversational retrieval chain.
- `frontend/`: (Optional) A Chrome Extension frontend designed to interact with this API.
