"""Boucle interactive en ligne de commande pour interroger l'assistant Code du travail."""
import json
from datetime import date

from src import config
from src.bootstrap import ensure_vector_db_built
from src.rag import Rag

EXIT_COMMANDS = {"quit", "exit", "q"}
STALE_AFTER_DAYS = 180


def print_freshness_banner() -> None:
	"""Q3 (fraîcheur) : prévient l'utilisateur de la date du corpus et du risque d'obsolescence,
	plutôt que de laisser croire que les réponses sont à jour du droit en vigueur aujourd'hui."""
	if not config.CORPUS_META_PATH.exists():
		print("Date du corpus inconnue (corpus_meta.json absent).\n")
		return

	with open(config.CORPUS_META_PATH, "r", encoding="utf-8") as f:
		meta = json.load(f)

	generated_at = date.fromisoformat(meta["generated_at"])
	age_days = (date.today() - generated_at).days
	print(f"Corpus du Code du travail téléchargé le {generated_at.strftime('%d/%m/%Y')} ({meta['chunk_count']} articles).")
	if age_days > STALE_AFTER_DAYS:
		print(
			f"Attention : ce corpus a {age_days} jours. Le droit du travail évolue "
			"(lois, ordonnances) ; pour un sujet sensible, vérifiez qu'aucune réforme récente "
			"n'a modifié les articles cités."
		)
	print()


def format_sources(metadatas: list) -> list:
	lines = []
	for meta in metadatas:
		num = meta.get("num")
		label = f"Article {num}" if num else "Article inconnu"
		source = meta.get("source") or ""
		url = meta.get("url") or ""

		line = f"  - {label}"
		if source:
			line += f" ({source})"
		if url:
			line += f" — {url}"
		lines.append(line)
	return lines


def main():
	print("Assistant Code du travail — posez votre question, ou tapez 'quit' pour quitter.\n")
	print_freshness_banner()

	ensure_vector_db_built()
	rag = Rag(vector_db_path=str(config.VECTOR_DB_PATH))

	while True:
		try:
			question = input("Question > ").strip()
		except (EOFError, KeyboardInterrupt):
			print("\nAu revoir.")
			break

		if not question:
			continue
		if question.lower() in EXIT_COMMANDS:
			print("Au revoir.")
			break

		answer, documents, metadatas = rag.ask_rag(question)

		print(f"\n{answer}\n")
		if metadatas:
			print("Sources :")
			for line in format_sources(metadatas):
				print(line)
			print()


if __name__ == "__main__":
	main()
