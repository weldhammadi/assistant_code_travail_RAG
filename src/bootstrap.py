import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
	sys.path.insert(0, str(REPO_ROOT))

from src import config
from src.vector_db import VectorDB


def _ensure_corpus_ingested() -> None:
	"""Lance le pipeline d'ingestion (download + parse) si le corpus JSON n'existe pas encore.

	Nécessaire pour un déploiement à partir d'un checkout git propre (data/ est gitignored) : il n'y
	a pas de shell interactif pour lancer `data_prep/code_cli.py` à la main sur un conteneur.
	"""
	if config.PARSED_CORPUS_PATH.exists():
		return

	sys.path.insert(0, str(REPO_ROOT / "data_prep"))
	from code_orchestrator import CodeOrchestrator  # noqa: E402

	orchestrator = CodeOrchestrator(
		output_path=config.PARSED_CORPUS_PATH,
		raw_cache_dir=config.RAW_CACHE_DIR,
		source_url_template=config.SOURCE_URL_TEMPLATE,
		legifrance_article_url_template=config.LEGIFRANCE_ARTICLE_URL_TEMPLATE,
		legi_id=config.LEGI_TEXT_ID,
		code_name=config.CODE_NAME,
		section_patterns=config.SECTION_PATTERNS,
	)
	orchestrator.run()


def ensure_vector_db_built() -> None:
	"""Construit my_vector_db/ depuis le corpus JSON parsé si la base n'existe pas déjà sur disque
	(télécharge et parse le corpus au préalable si besoin — voir _ensure_corpus_ingested)."""
	if config.VECTOR_DB_PATH.exists():
		return

	_ensure_corpus_ingested()

	with open(config.PARSED_CORPUS_PATH, "r", encoding="utf-8") as f:
		corpus_dict = json.load(f)
	VectorDB(vector_db_path=str(config.VECTOR_DB_PATH), corpus_dict=corpus_dict)
