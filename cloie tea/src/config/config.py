import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017").strip()
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "cloie_tea").strip()
