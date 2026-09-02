# Deep Multi-Agent Research System - FastAPI Server

A production-ready FastAPI backend for the LangGraph Multi-Agent Research System.

## Architecture

```
User Request ──► [Planner Agent]
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   [Researcher 1] [Researcher 2] [Researcher 3] (Parallel Tavily Search)
        └──────────────┬──────────────┘
                       ▼
              [Evidence Collector]
                       ▼
                  [QA Critic]
                       ▼
                [Report Writer] (Groq / 1000-1500 words)
                       ▼
               [Image Subgraph] (Qwen/Qwen-Image / HuggingFace)
                       ▼
                 [File Saver] (Saved to reports/)
```

---

## Quickstart

### 1. Configure Environment Variables
Ensure your `.env` inside `multi_research_agent/` contains your API keys:
```env
GOOGLE_API_KEY="your-google-api-key"
GOOGLE_API_KEY2="your-second-google-key-or-same"
GROQ_API_KEY="your-groq-api-key"
HF_TOKEN="your-huggingface-token"
TAVILY_API_KEY="your-tavily-api-key"
```

### 2. Run the Server
From the workspace root or inside `multi_research_agent/`:
```bash
python multi_research_agent/run_server.py --port 8000
```
Or with `uvicorn` directly:
```bash
uvicorn main:app --app-dir multi_research_agent --reload --port 8000
```

### 3. Interactive Documentation
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## API Endpoints

### 1. `POST /api/research`
Executes end-to-end research and returns the full structured response.

**Request:**
```json
{
  "question": "Optimizing Edge AI and Lightweight Computer Vision Architectures for Real-Time, Offline Accessibility Tools.",
  "thread_id": "optional_custom_thread_id"
}
```

**Response:**
```json
{
  "thread_id": "research_12345",
  "question": "...",
  "status": "completed",
  "research_topics_planned": [
    "Topic 1",
    "Topic 2",
    "Topic 3"
  ],
  "critique": "Sufficient Evidence: True ...",
  "final_report": "# Markdown report content...",
  "saved_file_path": "reports/optimizing_edge_ai...md",
  "image_specs": [...]
}
```

---

### 2. `POST /api/research/stream` (Real-Time SSE Streaming)
Streams step-by-step node execution and state changes as Server-Sent Events (SSE).

**Example cURL:**
```bash
curl -N -X POST http://localhost:8000/api/research/stream \
     -H "Content-Type: application/json" \
     -d '{"question": "Recent breakthroughs in Quantum Computing error correction in 2025"}'
```

**Python Client Example:**
```python
import httpx
import json

url = "http://localhost:8000/api/research/stream"
payload = {"question": "State of Multimodal Small Language Models in 2026"}

with httpx.stream("POST", url, json=payload, timeout=300.0) as response:
    for line in response.iter_lines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            print(f"[{event.get('event')}] Node: {event.get('node')}")
```

---

### 3. Report Management
- **`GET /api/reports`**: List all generated reports with timestamps and file sizes.
- **`GET /api/reports/{filename}`**: Get report markdown text and metadata.
- **`DELETE /api/reports/{filename}`**: Delete a report from disk.
- **`GET /reports/{filename}`**: Direct static file access to the markdown report.
- **`GET /images/{filename}`**: Direct static file access to generated diagrams/images.
