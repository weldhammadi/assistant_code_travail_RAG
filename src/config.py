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
CORPUS_PATH = BASE_DIR / "data" / "raw" / "code_travail_corpus.csv"

PARSED_CORPUS_PATH = BASE_DIR / "data" / "corpus_code_travail.json"

EMBEDDING_MODEL="distiluse-base-multilingual-cased-v2"

LLM_MODEL="openai/gpt-oss-120b"

MODERATOR_MODEL="openai/gpt-oss-safeguard-20b"

MODERATOR_SYSTEM_PROMPT_PATH = PROMPTS_DIR / "moderator_system.txt"

RAG_PROMPT_SYSTEM_PATH = PROMPTS_DIR / "rag_prompt_system.txt"

# CORPUS_PATH = BASE_DIR / "05_corpus_rag.csv"

VECTOR_DB_PATH = BASE_DIR / "my_vector_db"