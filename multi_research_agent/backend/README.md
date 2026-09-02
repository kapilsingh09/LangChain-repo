# Multi-Agent Research System - Modular Backend

A professional, modular FastAPI backend powered by LangGraph, Google Gemini, Groq, Tavily, and HuggingFace.

---

## 📂 Project Structure

```
multi_research_agent/
├── backend/
│   ├── .env                      # API keys & environment configuration
│   ├── run_server.py             # CLI application entrypoint
│   ├── test_api.py               # Test suite for FastAPI endpoints
│   ├── README.md                 # Backend documentation
│   │
│   ├── app/                      # Application source package
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI instance, CORS, static mounts
│   │   ├── config.py             # Settings, storage paths, model definitions
│   │   │
│   │   ├── schemas/              # Pydantic data contracts
│   │   │   ├── __init__.py
│   │   │   ├── research.py       # ResearchRequest, ResearchResponse, StreamEvent
│   │   │   └── reports.py        # ReportMetadata, ReportDetailResponse, HealthResponse
│   │   │
│   │   ├── graph/                # LangGraph Multi-Agent Engine
│   │   │   ├── __init__.py
│   │   │   ├── state.py          # ChatState, CriticState, PlannerState, ImageState
│   │   │   ├── llms.py           # Gemini, Groq, and HuggingFace client wrappers
│   │   │   ├── tools.py          # Tavily search tool definitions
│   │   │   ├── nodes.py          # Planner, researcher, collector, critic, writer, file_saver
│   │   │   ├── image_nodes.py    # Diagram decision & Qwen generation subgraph
│   │   │   └── workflow.py       # Main LangGraph assembly & checkpointer
│   │   │
│   │   ├── routers/              # Modular API routes
│   │   │   ├── __init__.py
│   │   │   ├── general.py        # GET / and GET /health
│   │   │   ├── research.py       # POST /api/research & POST /api/research/stream
│   │   │   └── reports.py        # GET /api/reports, GET /api/reports/{filename}
│   │   │
│   │   └── storage/              # Persistent data directory
│   │       ├── images/           # Generated architecture diagrams (.png)
│   │       └── reports/          # Markdown research reports (.md)
│   │
└── try2.ipynb                    # Original experimental notebook
```

---

## ⚡ How to Run

### 1. Launch the Server
From the `multi_research_agent/backend` directory:
```bash
python run_server.py --port 8000
```
Or from the project root:
```bash
uvicorn app.main:app --app-dir multi_research_agent/backend --reload --port 8000
```

### 2. Interactive Swagger Docs
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API welcome metadata and available routes |
| `GET` | `/health` | Health check & API key readiness status |
| `POST` | `/api/research` | Synchronous deep research execution |
| `POST` | `/api/research/stream` | Real-time Server-Sent Events (SSE) streaming |
| `GET` | `/api/reports` | List all generated research reports with metadata |
| `GET` | `/api/reports/{filename}` | Retrieve specific Markdown report content |
| `DELETE` | `/api/reports/{filename}` | Delete a report from disk |
| `GET` | `/images/{filename}` | Direct static access to generated diagram images |
| `GET` | `/reports/{filename}` | Direct static access to markdown report files |

---

## 🧪 Running Tests
```bash
python test_api.py
```
