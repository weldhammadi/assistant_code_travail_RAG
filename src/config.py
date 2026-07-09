from dotenv import load_dotenv
import os
from pathlib import Path
import re

load_dotenv()

# API Key for GROQ
GROQ_API_KEY=os.environ["GROQ_API_KEY"]

# Path configuration
BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"

# DATA_DIR is overridable (DATA_DIR env var) so a persistent volume (Railway, etc.) can be mounted
# and pointed at without code changes — avoids re-downloading/re-embedding on every deploy.
DATA_DIR = Path(os.environ["DATA_DIR"]) if os.environ.get("DATA_DIR") else BASE_DIR / "data"

# Legifrance config
SOURCE_URL_TEMPLATE = (
        "https://raw.githubusercontent.com/SocialGouv/legi-data/master/data/{legi_id}.json"
    )
LEGI_TEXT_ID = "LEGITEXT000006072050"

LEGIFRANCE_ARTICLE_URL_TEMPLATE = "https://www.legifrance.gouv.fr/codes/article_lc/{id}"

CODE_NAME = "Code du travail"

SECTION_PATTERNS = [
        ("partie_racine", re.compile(r"^\s*Partie\s+(l[ée]gislative|r[ée]glementaire)", re.IGNORECASE)),
        ("partie_numerotee", re.compile(r"^\s*(Premi[èe]re|Deuxi[èe]me|Troisi[èe]me|Quatri[èe]me|Cinqui[èe]me)\s+partie\b", re.IGNORECASE)),
        ("livre", re.compile(r"^\s*Livre\b", re.IGNORECASE)),
        ("titre", re.compile(r"^\s*Titre\b", re.IGNORECASE)),
        ("chapitre", re.compile(r"^\s*Chapitre\b", re.IGNORECASE)),
        ("section", re.compile(r"^\s*Section\b", re.IGNORECASE)),
        ("sous_section", re.compile(r"^\s*Sous-section\b", re.IGNORECASE)),
    ]
# Database config
PARSED_CORPUS_PATH = DATA_DIR / "corpus_code_travail.json"

CORPUS_META_PATH = DATA_DIR / "corpus_meta.json"

RAW_CACHE_DIR = DATA_DIR / "raw"

EMBEDDING_MODEL="distiluse-base-multilingual-cased-v2"

LLM_MODEL="openai/gpt-oss-120b"

MODERATOR_MODEL="openai/gpt-oss-safeguard-20b"

MODERATOR_SYSTEM_PROMPT_PATH = PROMPTS_DIR / "moderator_system.txt"

RAG_PROMPT_SYSTEM_PATH = PROMPTS_DIR / "rag_prompt_system.txt"

# VECTOR_DB_PATH is independently overridable (VECTOR_DB_PATH env var) for the same reason as
# DATA_DIR — default unchanged (BASE_DIR / "my_vector_db") so existing local setups keep working.
VECTOR_DB_PATH = Path(os.environ["VECTOR_DB_PATH"]) if os.environ.get("VECTOR_DB_PATH") else BASE_DIR / "my_vector_db"