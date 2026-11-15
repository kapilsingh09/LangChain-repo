# LangGraph & LLM Projects Workspace

This folder is a collection of experiments, demos, and mini-projects built around LangChain, LangGraph, Retrieval-Augmented Generation (RAG), multi-agent systems, and AI-powered applications.

The workspace contains both learning materials and end-to-end application prototypes, ranging from notebook-based tutorials to full web apps and research agents.

## Overview

The projects in this workspace explore:

- LangGraph agent orchestration and workflows
- Multi-agent collaboration patterns
- Retrieval-augmented generation (RAG)
- YouTube and document-based Q&A systems
- AI research and report generation
- FastAPI and frontend integrations
- Notebook-based experimentation and tutorials

## Project Structure

```text
langgraph/
├── MA-chatbot/                # Multi-agent chatbot project
├── MultiagentLG/              # Deep research / multi-agent research API
├── RAG-YT-EXT/                # YouTube RAG extension project
├── corrective-rag/            # Corrective RAG experiments
├── document-copilot/         # Document AI assistant
├── documents/                # Shared/supporting documents
├── graph+rag_ad/             # Graph + RAG experiments
├── langchain/                # LangChain-related learning and project files
├── langgraph/                # LangGraph tutorials, notebooks, examples
├── langgraph_ragchatbot_yt/  # LangGraph YouTube chatbot project
├── self-rag/                 # Self-RAG experiments
├── stitch-export/            # Stitch-based export/demo assets
├── web-app/                  # General web app experiments
├── yt-info-extracter/        # YouTube info extraction utilities
├── one.ipynb                # Notebook exercise / exploration
├── test.py                  # Small test scripts or experiments
├── .gitignore               # Git ignore rules
├── README.md                # Project overview
└── .vscode/                 # Editor settings
```

## Notable folders

### MultiagentLG
A LangGraph-based deep research system using multiple AI agents to break down a question, research it, critique findings, and generate a final report.

### MA-chatbot
A multi-agent conversational project focused on chatbot orchestration and interaction flows.

### RAG-YT-EXT
A YouTube-focused retrieval and answer system that combines RAG patterns with YouTube content extraction or indexing.

### document-copilot
A document-driven AI assistant for reading, understanding, and querying document content.

### langgraph
A learning-focused area containing LangGraph tutorials, notebooks, and examples.

### langchain
A LangChain-centric workspace containing projects and utilities related to chaining, memory, retrieval, and tooling.

### graph+rag_ad and self-rag
Experimental RAG and graph-based architectures that extend the ideas of retrieval, reasoning, and adaptive generation.

## Typical Tech Stack

Most projects in this workspace use a combination of:

- Python
- LangChain
- LangGraph
- FastAPI
- RAG pipelines
- Vector stores / embedding workflows
- LLM APIs (OpenAI, Gemini, Groq, Hugging Face, etc.)
- JavaScript/React for frontends in selected projects

## Getting Started

1. Open the project folder that matches your use case.
2. Read that project's own README for specific setup instructions.
3. Create or activate a Python virtual environment.
4. Install dependencies for the chosen project.
5. Add required API keys in a `.env` file when needed.

Example:

```bash
cd MultiagentLG
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# or .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Recommended workflow

- For learning: start with the `langgraph/` and `langchain/` folders.
- For agent systems: review `MultiagentLG` and `MA-chatbot`.
- For RAG experiments: check `RAG-YT-EXT`, `document-copilot`, `corrective-rag`, and `self-rag`.
- For app prototypes: inspect `web-app` and the individual frontend folders.

## Maintainer

This workspace is maintained by kapil Singh.

## Notes

This repository is best understood as a research and experimentation workspace rather than a single production app. Some folders are self-contained projects, while others are tutorial examples or prototype experiments.

If you want to work on one project, it is usually better to open that specific subdirectory instead of the root folder.

## License

This project collection does not appear to be governed by a single root-level license file. Individual subprojects may carry their own licensing terms, so check the relevant folder before redistribution or commercial use.
