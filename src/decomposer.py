import json
import sys
from pathlib import Path

if __name__ == "__main__":
	sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DECOMPOSER_SYSTEM_PROMPT_PATH, DECOMPOSER_MODEL
from src.agent import Agent


class Decomposer(Agent):
	MAX_SUB_QUESTIONS = 4

	def decompose(self, question):
		"""Découpe une question en 2-4 sous-questions atomiques.
		En cas d'échec (parsing, erreur API, réponse vide), retombe sur [question]
		pour ne jamais bloquer le pipeline RAG."""
		try:
			chat_completion = self.client.chat.completions.create(
				messages=[
					{
						"role": "system",
						"content": Agent.read_file(DECOMPOSER_SYSTEM_PROMPT_PATH),
					},
					{
						"role": "user",
						"content": question,
					},
				],
				model=DECOMPOSER_MODEL,
				response_format={"type": "json_object"},
				temperature=0,
			)
			result = json.loads(chat_completion.choices[0].message.content)
			sub_questions = result.get("hyde_statements", [])
			sub_questions = [q.strip() for q in sub_questions if isinstance(q, str) and q.strip()]

			if not sub_questions:
				return [question]

			return sub_questions[: self.MAX_SUB_QUESTIONS]

		except Exception:
			return [question]


if __name__ == "__main__":
	decomposer_object = Decomposer()
	result = decomposer_object.decompose(
		"Bonjour, j'espère que vous allez bien ! J'ai une question un peu compliquée : "
		"je suis actuellement en CDI et mon employeur me propose de passer en forfait jours, "
		"du coup je me demande si j'ai le droit de refuser, et si oui quelles sont les conséquences "
		"possibles pour moi, et est-ce que ça change quelque chose pour mes RTT ? "
		"Merci d'avance pour votre aide !"
	)
	print(result)

	result_2 = decomposer_object.decompose(
		"Bonjour, savez-vous combien de jours de congés payés j'ai droit par mois, merci beaucoup ?"
	)
	print(result_2)