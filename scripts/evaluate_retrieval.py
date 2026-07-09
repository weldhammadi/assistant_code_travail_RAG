"""Jalon 3 — validation du retrieval, avant tout appel au LLM.

Pour chaque question de test, on vérifie que l'article attendu (identifié manuellement dans le
corpus réel) remonte bien dans le top-k de la recherche vectorielle. Si un article attendu ne
remonte pas, le problème vient du chunking, de l'embedding ou du corpus — pas du LLM, qui n'est
jamais appelé ici.

Ces questions constituent aussi le jeu d'évaluation gardé pour la suite (cf. pf.md, Jalon 3).
"""
import sys
from pathlib import Path

if __name__ == "__main__":
	sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import VECTOR_DB_PATH
from src.vector_db import VectorDB

TEST_CASES = [
	("Quelle est la durée du préavis en cas de licenciement pour un salarié en CDI ?", "L1234-1"),
	("Quelle est la durée maximale hebdomadaire de travail ?", "L3121-20"),
	("Qu'est-ce qu'un licenciement pour motif économique ?", "L1233-3"),
	("Comment fonctionne la rupture conventionnelle ?", "L1237-11"),
	("Ai-je droit à des congés payés tous les ans ?", "L3141-1"),
]


def evaluate(top_k: int = 5) -> bool:
	vector_db = VectorDB(vector_db_path=str(VECTOR_DB_PATH))

	all_passed = True
	for question, expected_article in TEST_CASES:
		results = vector_db.retrieve(question, n=top_k)
		found_articles = [r["num"] for r in results]
		passed = expected_article in found_articles

		status = "OK  " if passed else "FAIL"
		print(f"[{status}] {question}")
		print(f"       attendu : {expected_article} | trouvés (top-{top_k}) : {found_articles}")

		all_passed = all_passed and passed

	return all_passed


if __name__ == "__main__":
	success = evaluate()
	print("\nTous les articles attendus remontent dans le top-k." if success
		  else "\nCertains articles attendus ne remontent pas — revoir chunking/embedding/corpus.")
	raise SystemExit(0 if success else 1)
