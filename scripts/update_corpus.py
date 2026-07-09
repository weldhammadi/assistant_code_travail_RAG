"""Met à jour le corpus depuis la source GitHub (SocialGouv/legi-data) et reconstruit la base
vectorielle en conséquence.

À lancer quand la source amont a été mise à jour et qu'on veut que l'assistant reflète la nouvelle
version du Code du travail, plutôt que d'attendre une prochaine ingestion manuelle. Contrairement à
`data_prep/code_cli.py` (qui réutilise le cache local par défaut), ce script force le
retéléchargement.
"""
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "data_prep"))

from code_orchestrator import CodeOrchestrator  # noqa: E402

from src import config  # noqa: E402
from src.vector_db import VectorDB  # noqa: E402


def main():
	orchestrator = CodeOrchestrator(
		output_path=config.PARSED_CORPUS_PATH,
		raw_cache_dir=config.BASE_DIR / "data" / "raw",
		source_url_template=config.SOURCE_URL_TEMPLATE,
		legifrance_article_url_template=config.LEGIFRANCE_ARTICLE_URL_TEMPLATE,
		legi_id=config.LEGI_TEXT_ID,
		code_name=config.CODE_NAME,
		section_patterns=config.SECTION_PATTERNS,
	)

	print("Retéléchargement depuis GitHub (force) et reparsing...")
	orchestrator.run(force_download=True)

	if config.VECTOR_DB_PATH.exists():
		print(f"Suppression de l'ancienne base vectorielle ({config.VECTOR_DB_PATH})...")
		try:
			shutil.rmtree(config.VECTOR_DB_PATH)
		except PermissionError:
			raise SystemExit(
				f"Impossible de supprimer {config.VECTOR_DB_PATH} : des fichiers sont verrouillés "
				"(un cli.py ou une api.py encore lancé ?). Fermez tout processus utilisant la base "
				"puis relancez ce script."
			)

	with open(config.PARSED_CORPUS_PATH, "r", encoding="utf-8") as f:
		corpus_dict = json.load(f)

	print(f"Reconstruction de la base vectorielle ({len(corpus_dict)} chunks)...")
	VectorDB(vector_db_path=str(config.VECTOR_DB_PATH), corpus_dict=corpus_dict)
	print("Mise à jour terminée.")


if __name__ == "__main__":
	main()
