from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()


GROQ_API_KEY=os.environ["GROQ_API_KEY"]

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"

EMBEDDING_MODEL="distiluse-base-multilingual-cased-v2"
LLM_MODEL="openai/gpt-oss-120b"
MODERATOR_MODEL="openai/gpt-oss-safeguard-20b"
MODERATOR_SYSTEM_PROMPT_PATH = PROMPTS_DIR / "moderator_system.txt"
RAG_PROMPT_SYSTEM_PATH = PROMPTS_DIR / "rag_prompt_system.txt"
CORPUS_PATH = BASE_DIR / "05_corpus_rag.csv"
VECTOR_DB_PATH = BASE_DIR / "my_vector_db"

SOURCE_URL_TEMPLATE = (
        "https://raw.githubusercontent.com/SocialGouv/legi-data/master/data/{legi_id}.json"
    )
LEGI_TEXT_ID = "LEGITEXT000006072050"