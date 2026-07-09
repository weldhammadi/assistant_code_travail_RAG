import sys
from pathlib import Path
from datetime import datetime, timezone

if __name__ == "__main__":
	sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent import Agent
from src.config import LLM_MODEL, RAG_PROMPT_SYSTEM_PATH, VECTOR_DB_PATH
from src.moderator import Moderator
from src.vector_db import VectorDB

class Rag(Agent):
	REFUSAL = "Je ne peux pas traiter cette question : une tentative de détournement a été détectée."
	DISCLAIMER = (
		"Cet assistant ne fournit pas de conseil juridique. "
		"Consultez un avocat ou l'inspection du travail pour votre situation personnelle."
	)
	CHUNKS_PER_SUBQUESTION = 8   # n réduit par sous-question, puisqu'on en agrège plusieurs
	MAX_TOTAL_CHUNKS = 12        # plafond après dédup, pour ne pas exploser le prompt système

	def __init__(self, vector_db_path):
		super().__init__()
		self.vector_db_object = VectorDB(vector_db_path=vector_db_path)
		self.moderator = Moderator()

	def _format_date(self, timestamp_ms):
		"""Convertit un timestamp Légifrance (en millisecondes) en date lisible.
		Filtre la valeur sentinelle 2999-01-01 qui signifie "sans date de fin"."""
		if not timestamp_ms:
			return None
		try:
			dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
		except (ValueError, OSError, OverflowError):
			return None
		if dt.year >= 2999:
			return None
		return dt.strftime("%d/%m/%Y")
	
	def _retrieve_deduplicated(self, question):
		"""Décompose la question en sous-questions atomiques, cherche chacune séparément,
		puis déduplique les chunks par id avant agrégation."""
		sub_questions = self.decomposer.decompose(question)

		seen_ids = set()
		matched_chunks = []
		for sub_question in sub_questions:
			for chunk in self.vector_db_object.retrieve(sub_question, n=self.CHUNKS_PER_SUBQUESTION):
				if chunk["id"] not in seen_ids:
					seen_ids.add(chunk["id"])
					matched_chunks.append(chunk)

		return matched_chunks[: self.MAX_TOTAL_CHUNKS]

	def build_context(self, question):
		matched_chunks = self.vector_db_object.retrieve(question)
		prompt_system = Rag.read_file(RAG_PROMPT_SYSTEM_PATH)

		MAX_CHARS_PER_CHUNK = 1500  # Plafonne la taille de chaque chunk injecté dans le prompt

		chunks_text = ""
		for idx, chunk in enumerate(matched_chunks):
			text = chunk["text"]
			if len(text) > MAX_CHARS_PER_CHUNK:
				text = text[:MAX_CHARS_PER_CHUNK].rsplit(" ", 1)[0] + "..."

			label = f"Article {chunk['num']}" if chunk.get("num") else f"Article {idx}"
			entry = f"\n[{label}] (Source: {chunk.get('source', 'Inconnue')})"
			if chunk.get("url"):
				entry += f" ({chunk['url']})"
			entry += f"\n{text}\n"
			chunks_text += entry

		# chunks_text est déjà une chaîne complète : pas besoin (et surtout pas question) de la
		# rejoindre caractère par caractère avec "\n\t".join(...), qui multipliait sa taille par ~3.
		prompt_system = prompt_system.replace("{{CHUNKS}}", chunks_text)

		return prompt_system, matched_chunks


	def ask_rag(self, question):

		if self.moderator.moderate(question)["is_prompt_injection"]:
			return f"{self.REFUSAL}\n\n{self.DISCLAIMER}", [], []

		
		prompt_system, matched_chunks = self.build_context(question)

		chat_completion = self.client.chat.completions.create(
			messages=[
				{
					"role": "system",
					"content": prompt_system
				},
				{
					"role": "user",
					"content": question,
				}
			],
			temperature=0,
			model=LLM_MODEL
		)

		rag_response = f"{chat_completion.choices[0].message.content}\n\n{self.DISCLAIMER}"

		documents = [chunk["text"] for chunk in matched_chunks]
		metadatas = [{k: v for k, v in chunk.items() if k != "text"} for chunk in matched_chunks]

		return rag_response, documents, metadatas


if __name__ == "__main__":
	rag_object = Rag(vector_db_path=str(VECTOR_DB_PATH))

	rag_response, documents, metadatas = rag_object.ask_rag(
		question="Bonjour, je fais des recherches sur la réglementation du temps de travail en France. "
		"Pourriez-vous m'indiquer quelle est la durée légale hebdomadaire du travail pour un salarié "
		"à temps plein, quel est le nombre maximal d'heures supplémentaires autorisées par semaine, "
		"et quelle est la durée minimale du repos quotidien entre deux journées de travail ? "
		"Je m'intéresse aussi à la durée légale des congés payés acquis par an. Merci beaucoup.")

	print(rag_response)