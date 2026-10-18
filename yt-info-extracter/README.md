# YouTube Researcher

YouTube Researcher is a web app for exploring YouTube videos through their
transcripts. It fetches captions, indexes transcript segments for retrieval, and
uses a LangGraph workflow to answer questions, summarize videos, or conduct
deeper research. Answers can include timestamps that link back to the relevant
part of the video.

## Features

- Load a YouTube video by URL and fetch its available captions (English and
  Hindi are preferred when available).
- Ask questions grounded in the transcript using FAISS vector search.
- Route prompts to conversational chat, transcript Q&A, summarization, or
  research workflows.
- Optionally augment research answers with Tavily web search.
- Keep videos, chats, and messages in a local SQLite database.
- Stream chat responses, compare two chat sessions, and export messages or
  complete chats as Markdown.
- Use the built-in video player and transcript-linked timeline.

## Requirements

- Python 3.11 (the version used by the Docker image)
- A Groq API key
- Internet access to fetch YouTube captions and download the embedding model on
  first use
- Optional: a Tavily API key for web-enhanced research

## Setup

Run these commands from the `yt-info-extracter` project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create `backend/.env` and add your API keys:

```dotenv
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

`GROQ_API_KEY` is needed for AI chat and analysis. `TAVILY_API_KEY` is optional;
without it, research uses the video transcript and does not perform web search.
Markdown export can use `API_KEY_2` or `GROQ_API_KEY_2` for a separate Groq key;
if neither is set, it falls back to `GROQ_API_KEY`.

Keep `backend/.env` private and do not commit API keys.

## Run locally

From the project directory, start the API and frontend:

```powershell
python run.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive API
documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

The frontend is served by FastAPI, so it does not need a separate development
server. It loads some visual and Markdown libraries from public CDNs.

## Run with Docker

Build the image from the project directory:

```powershell
docker build -t yt-researcher .
```

With `backend/.env` configured, start the container:

```powershell
docker run --rm -p 8000:8000 --env-file backend/.env --name yt-researcher yt-researcher
```

Then open [http://localhost:8000](http://localhost:8000).

## Data and generated files

- SQLite database: `backend/youtube_researcher.db`
- Generated Markdown exports: `backend/artifacts/`
- Transcript vector indexes are built in memory and cached while the server is
  running.

The Docker build excludes `.env` files, local databases, notebooks, and generated
artifacts. Pass configuration at runtime with `--env-file`; do not bake secrets
into the image.

## API overview

The API is also documented interactively at `/docs`. Main routes include:

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/videos` | Load and index a video from its URL |
| `GET` | `/api/videos` | List loaded videos |
| `GET` | `/api/videos/{video_pk}` | Get video details and transcript segments |
| `DELETE` | `/api/videos/{video_pk}` | Delete a video |
| `POST` | `/api/chats` | Create a chat for a video |
| `GET` | `/api/chats` | List chats, optionally filtered by `video_id` |
| `GET` | `/api/chats/{chat_id}` | Get a chat and its messages |
| `POST` | `/api/chats/{chat_id}/messages/stream` | Stream a response using Server-Sent Events |
| `GET` | `/api/compare?chat_ids={id1},{id2}` | Retrieve two chats for comparison |
| `POST` | `/api/chats/{chat_id}/export-md` | Generate a Markdown report for a chat |

