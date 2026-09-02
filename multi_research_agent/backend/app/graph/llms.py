from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from huggingface_hub import InferenceClient
from app.config import settings


def content_to_str(content: Any) -> str:
    """Normalize LLM response content (str or list of parts) to a clean string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text", str(part)))
            else:
                parts.append(str(part))
        return " ".join(parts)
    return str(content)


# Primary Google Gemini LLM (Planner, Critic, Image Planner)
google_llm = ChatGoogleGenerativeAI(
    model=settings.GOOGLE_MODEL,
    api_key=settings.GOOGLE_API_KEY,
)

# Secondary Google Gemini LLM (Evidence Collector)
google_llm_secondary = ChatGoogleGenerativeAI(
    model=settings.GOOGLE_MODEL,
    api_key=settings.GOOGLE_API_KEY2,
)

# Groq LLM (High-capacity Technical Report Writer)
groq_llm = ChatGroq(
    model=settings.GROQ_MODEL,
    temperature=0.2,
    max_retries=2,
    api_key=settings.GROQ_API_KEY,
)

# HuggingFace Client (Image/Diagram Generation)
def get_hf_client():
    if not settings.HF_TOKEN:
        return None
    return InferenceClient(api_key=settings.HF_TOKEN, provider="auto")
