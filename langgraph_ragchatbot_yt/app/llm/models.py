from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
import os 
from dotenv import load_dotenv


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Main LLM
google_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    api_key=GOOGLE_API_KEY,
)

# SECONDARY LLM
groq_llm = ChatGroq(
    model="openai/gpt-oss-120b",  # or "llama-3.1-8b-instant"
    temperature=0.2,
    max_retries=2,
    api_key=GROQ_API_KEY
)

# print("Google LLM and Groq LLM initialized successfully.")