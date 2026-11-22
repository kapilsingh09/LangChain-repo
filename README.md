# LangGraph & LLM Projects Workspace

This repository is a collection of experiments, tutorials, demos, and mini-projects built around LangChain, LangGraph, Retrieval-Augmented Generation (RAG), multi-agent systems, and AI-powered applications.

It covers a range of implementations, from notebook-based learning experiments to end-to-end AI application prototypes.

## Workspace Highlights

- Hands-on notebooks for learning LangChain, LangGraph, embeddings, and retrieval techniques
- Runnable examples of autonomous agents and multi-agent research workflows
- RAG experiments ranging from basic document retrieval to corrective and graph-enhanced approaches
- Full-stack AI prototypes with Python backends and modern frontend applications

## Overview

The projects in this workspace explore:

- LangGraph agent orchestration and workflow design
- Multi-agent collaboration and coordination patterns
- Retrieval-Augmented Generation (RAG) architectures
- YouTube and document-based question-answering systems
- AI-powered research and report generation
- FastAPI backend development and frontend integrations
- Notebook-based experimentation and tutorials
- LLM-powered tools and autonomous agents

## Project Structure

```text
LangChain-repo/
├── MA-chatbot/                # Multi-agent chatbot project
├── MultiagentLG/              # Deep research and multi-agent research API
├── RAG-YT-EXT/                # YouTube RAG Chrome extension
├── corrective-rag/            # Corrective RAG experiments
├── document-copilot/          # Document-based AI assistant
├── documents/                 # Shared and supporting documents
├── graph+rag_ad/              # Graph + RAG experiments
├── langchain/                 # LangChain tutorials and projects
├── langgraph/                 # LangGraph tutorials and examples
├── langgraph_ragchatbot_yt/   # LangGraph-based YouTube chatbot
├── self-rag/                  # Self-RAG experiments
├── stitch-export/             # Stitch-based design exports and assets
├── web-app/                   # Web application experiments
├── yt-info-extracter/         # YouTube information extraction utilities
├── one.ipynb                  # Notebook experiments
├── test.py                    # Testing and experimentation scripts
├── .gitignore                 # Git ignore configuration
├── README.md                  # Workspace documentation
└── .vscode/                   # VS Code settings
```

## Notable Projects

### 1. MultiagentLG

A LangGraph-based deep research system that uses multiple AI agents to break down complex queries, gather information, evaluate findings, and generate structured research reports.

### 2. MA-chatbot

A multi-agent conversational application focused on agent orchestration, task coordination, and chatbot interaction workflows.

### 3. RAG-YT-EXT

A YouTube-focused AI research assistant that uses video transcripts and retrieval-based techniques to answer questions about YouTube content.

### 4. document-copilot

A document-driven AI assistant designed to process, understand, and answer questions from uploaded documents.

### 5. langgraph

A learning-focused directory containing LangGraph tutorials, notebooks, graph architectures, and practical examples.

### 6. langchain

A collection of LangChain-related experiments covering chains, tools, memory, retrieval, and LLM integrations.

### 7. graph+rag_ad and self-rag

Experimental implementations exploring graph-based retrieval, adaptive retrieval strategies, and self-reflective RAG architectures.

### 8. corrective-rag

Experiments with Corrective RAG (CRAG), focusing on retrieval evaluation and improving answer quality through corrective retrieval strategies.

### 9. Embedding experiments

The root-level `one.ipynb` and `graph+rag_ad/main_one.ipynb` notebooks demonstrate local embedding setup with `BAAI/bge-small-en-v1.5` through `sentence-transformers`.

## Tech Stack

The workspace primarily uses the following technologies:

- **Programming:** Python, JavaScript
- **LLM Frameworks:** LangChain, LangGraph
- **Backend:** FastAPI
- **AI Architectures:** RAG, Agentic RAG, Multi-Agent Systems
- **Vector Search:** FAISS and other vector store integrations
- **Embeddings:** Hugging Face embedding models and API-based embedding models
- **LLM Providers:** OpenAI, Google Gemini, Groq, Hugging Face
- **Frontend:** JavaScript, React
- **Development:** Jupyter Notebook, VS Code, Git

## Getting Started

Follow these steps to run an individual project:

### 1. Clone the repository

```bash
git clone https://github.com/kapilsingh09/LangChain-repo.git
cd LangChain-repo
```

### 2. Navigate to the desired project

```bash
cd MultiagentLG
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the environment

```bash
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

For the notebook-based experiments, install Jupyter and the embedding dependencies:

```bash
pip install jupyter sentence-transformers
```

### 6. Configure environment variables

Create a `.env` file and add the API keys required by the selected project.

```env
GROQ_API_KEY=your_api_key
GOOGLE_API_KEY=your_api_key
TAVILY_API_KEY=your_api_key
HF_TOKEN=your_hugging_face_token
```

Refer to the individual project's README for its specific dependencies and configuration requirements.

### 7. Run a notebook

```bash
jupyter notebook one.ipynb
```

The Hugging Face token is optional for public models, but setting `HF_TOKEN` can increase download rate limits.

## Recommended Workflow

- **Learning LangChain and LangGraph:** Explore the `langchain/` and `langgraph/` directories.
- **Building agentic systems:** Explore `MultiagentLG/` and `MA-chatbot/`.
- **Exploring RAG architectures:** Explore `RAG-YT-EXT/`, `document-copilot/`, `corrective-rag/`, and `self-rag/`.
- **Experimenting with advanced retrieval:** Explore `graph+rag_ad/`.
- **Building AI-powered applications:** Explore `web-app/` and individual project frontend directories.

## Project Guidelines

- Each project may have its own dependencies and environment configuration.
- Check the individual README before running a project.
- Keep API keys and credentials inside environment variables.
- Some directories contain experiments and learning implementations rather than complete applications.
- The workspace is continuously evolving as new experiments and implementations are added.

## Maintainer

**Kapil Singh**

## License

This workspace does not currently have a single root-level license governing all projects. Individual subprojects may have their own licensing terms. Check the relevant project directory before using or redistributing its contents.