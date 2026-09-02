import os
from pathlib import Path
from dotenv import load_dotenv

# Path resolution
BACKEND_DIR = Path(__file__).resolve().parent.parent
PARENT_DIR = BACKEND_DIR.parent

# Load .env from backend/ or parent directory
if (BACKEND_DIR / ".env").exists():
    load_dotenv(dotenv_path=BACKEND_DIR / ".env")
elif (PARENT_DIR / ".env").exists():
    load_dotenv(dotenv_path=PARENT_DIR / ".env")
else:
    load_dotenv()


class Settings:
    PROJECT_NAME: str = "Deep Multi-Agent Research System API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_API_KEY2: str = os.getenv("GOOGLE_API_KEY2") or os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "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")

    # Storage Paths
    STORAGE_DIR: Path = BACKEND_DIR / "storage"
    IMAGES_DIR: Path = STORAGE_DIR / "images"
    REPORTS_DIR: Path = STORAGE_DIR / "reports"

    # Model configurations
    GOOGLE_MODEL: str = "gemini-2.5-flash"
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    IMAGE_MODEL: str = "Qwen/Qwen-Image"


settings = Settings()

# Ensure storage directories exist
settings.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
