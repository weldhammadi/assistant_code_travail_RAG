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

	def build_context(self, question):
		matched_chunks = self.vector_db_object.retrieve(question)
		prompt_system = Rag.read_file(RAG_PROMPT_SYSTEM_PATH)

		chunks_text = ""
		for idx, chunk in enumerate(matched_chunks):
			text = chunk["text"]
			label = f"Article {chunk['num']}" if chunk.get("num") else f"Article {idx}"
			entry = f"\n[{label}] (Source: {chunk.get('source', 'Inconnue')})"
			if chunk.get("url"):
				entry += f" ({chunk['url']})"
			entry += f"\n{text}\n"
			chunks_text += entry

		prompt_system = prompt_system.replace("{{CHUNKS}}", "\n\t".join(chunks_text))

		return prompt_system


	def ask_rag(self, question):

		if self.moderator.moderate(question)["is_prompt_injection"]:
			return self.REFUSAL, [], []

		
		prompt_system = self.build_context(question)

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

		rag_response = chat_completion.choices[0].message.content
		return rag_response, documents, metadatas


if __name__ == "__main__":
	rag_object = Rag(vector_db_path=str(VECTOR_DB_PATH))

	rag_response, documents, metadatas = rag_object.ask_rag(question="Combien d'heures de travail sont nécessaires au minimum par semaine pour un CDI?")

	print(rag_response)
	print("-"*20)
	for index_document in range(len(documents)):
		print(f"Documents {index_document}")
		print(documents[index_document])
		for key, value in metadatas[index_document].items():
			print(f"{key} : {value}")
		print("---")