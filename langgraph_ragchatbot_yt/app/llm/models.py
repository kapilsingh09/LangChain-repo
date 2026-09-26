import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env relative to this file so it works regardless of CWD
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# GOOGLE_MODEL = os.getenv("GOOGLE_LLM_MODEL", "gemini-3.8-flash")
# GROQ_MODEL = os.getenv("GROQ_LLM_MODEL", "openai/gpt-oss-20b")

# Main LLM — Google Gemini
google_llm = ChatGoogleGenerativeAI(
    model='gemini-3.8-flash',
    api_key=GOOGLE_API_KEY,
)

# Secondary LLM — Groq (fast router / rewriter)
groq_llm = ChatGroq(
    model='openai/gpt-oss-20b',
    temperature=0.2,
    max_retries=2,
    api_key=GROQ_API_KEY,
)

# print("Google LLM and Groq LLM initialized successfully.")