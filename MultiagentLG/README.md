#  Deep Research Agent API

A **multi-agent AI research system** powered by [LangGraph](https://github.com/langchain-ai/langgraph) and FastAPI.

Submit any research question → get back a detailed 1000–1500 word markdown report, complete with QA critique, optional AI-generated diagrams, and web search.

---

##  Architecture

```
POST /research
      │
      ▼
   Planner          ← Breaks question into 3 research sub-tasks (Gemini)
      │
      ▼ (parallel fan-out)
 Researcher ×3      ← Each agent researches one task + web search (Tavily)
      │
      ▼ (merge)
  Collector         ← Deduplicates and organizes all findings (Gemini)
      │
      ▼
    Critic          ← Quality-checks evidence, scores 0-10 (Gemini)
      │
      ▼
 Report Writer      ← Writes the final markdown report (Groq)
      │
      ▼
 Image Agent        ← Decides on and generates technical diagrams (HuggingFace)
      │
      ▼
 File Saver         ← Saves .md report to reports/ directory
```

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/kapilsingh09/Deep-Researcher.git
cd Deep-Researcher
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

| Variable | Where to get it |
|---|---|
| `HF_TOKEN` | https://huggingface.co/settings/tokens |
| `GOOGLE_API_KEY` | https://aistudio.google.com/apikey |
| `GOOGLE_API_KEY2` | https://aistudio.google.com/apikey (second key for rate limits) |
| `GROQ_API_KEY` | https://console.groq.com/keys |
| `TAVILY_API_KEY` | https://app.tavily.com |

### 3. Install dependencies

```bash
pip install -r requirements.txt
# or if using pyproject.toml:
pip install -e .
```

### 4. Run the server

```bash
python main.py
```

Server starts at **http://localhost:8000**

### 5. Test the API

Open **http://localhost:8000/docs** for the interactive Swagger UI.

Or use curl:

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"question": "How does transformer attention work?"}'
```

---

##  Project Structure

```
MultiagentLG/
├── main.py                    # FastAPI server entry point
├── .env.example               # Environment variable template
├── requirements.txt           # pip install -r requirements.txt
├── pyproject.toml             # Project metadata and dependencies
│
└── app/
    ├── config.py              # API key loading and validation
    ├── models.py              # Pydantic request/response schemas
    ├── graph.py               # LangGraph workflow assembly
    │
    ├── agents/
    │   ├── state.py           # Shared ChatState TypedDict
    │   ├── planner.py         # Planner agent
    │   ├── researcher.py      # Researcher agent + web search tool
    │   ├── collector.py       # Collector agent
    │   ├── critic.py          # Critic/QA agent
    │   ├── report_writer.py   # Report writer agent
    │   ├── image_agent.py     # Image generation subgraph
    │   └── file_saver.py      # File saver agent
    │
    └── routes/
        └── research.py        # POST /research endpoint
```

---

## API Reference

### `GET /`
Health check.

**Response:**
```json
{ "status": "ok", "message": "Deep Research Agent API is running" }
```

---

### `POST /research`
Run the full research pipeline.

**Request body:**
```json
{
  "question": "How does transformer attention work?"
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `question` | string | Yes | 10–1000 characters |

**Response:**
```json
{
  "question": "How does transformer attention work?",
  "final_report": "# Transformer Attention...",
  "saved_file_path": "reports/how_does_transformer_attention_work_report.md",
  "web_search_performed": true,
  "critique": "Sufficient Evidence: True\nOverall Score: 8/10..."
}
```

---

## Security

- API keys are loaded from `.env` — never hardcoded
- Server refuses to start if any key is missing
- Input validation: question must be 10–1000 characters
- Report filenames are sanitized to prevent path traversal
- `.env` is in `.gitignore` — won't be accidentally committed

---

## Contributing

Contributions are welcome! See [open issues](../../issues) for tasks that need help.

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

MIT
