import json
import sys
from pathlib import Path

if __name__ == "__main__":
	sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config
from src.vector_db import VectorDB


def ensure_vector_db_built() -> None:
	"""Construit my_vector_db/ depuis le corpus JSON parsé si la base n'existe pas déjà sur disque."""
	if config.VECTOR_DB_PATH.exists():
		return

	if not config.PARSED_CORPUS_PATH.exists():
		raise RuntimeError(
			f"Corpus introuvable ({config.PARSED_CORPUS_PATH}). "
			"Lancez d'abord l'ingestion : python -m data_prep.code_cli"
		)

	with open(config.PARSED_CORPUS_PATH, "r", encoding="utf-8") as f:
		corpus_dict = json.load(f)
	VectorDB(vector_db_path=str(config.VECTOR_DB_PATH), corpus_dict=corpus_dict)
