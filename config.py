from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()


GROQ_API_KEY=os.environ["GROQ_API_KEY"]

BASE_DIR = Path(__file__).resolve().parent

EMBEDDING_MODEL="distiluse-base-multilingual-cased-v2"
LLM_MODEL="openai/gpt-oss-120b"
MODERATOR_MODEL="openai/gpt-oss-safeguard-20b"
MODERATOR_SYSTEM_PROMPT_PATH = BASE_DIR / "moderator_system.txt"