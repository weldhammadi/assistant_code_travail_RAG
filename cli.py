"""Boucle interactive en ligne de commande pour interroger l'assistant Code du travail."""
from src import config
from src.bootstrap import ensure_vector_db_built
from src.rag import Rag

EXIT_COMMANDS = {"quit", "exit", "q"}


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
