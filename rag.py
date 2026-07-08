from agent import Agent
from config import LLM_MODEL

from vector_db import VectorDB

class Rag(Agent):
	def __init__(self, vector_db_path):
		super().__init__()
		self.vector_db_object = VectorDB(vector_db_path=vector_db_path)



	def build_context(self, question):
		documents, metadatas = self.vector_db_object.retrieve(question)
		prompt_system = Rag.read_file("./rag_prompt_system.txt")

		prompt_system = prompt_system.replace("{{CHUNKS}}", "\n\t".join(documents))

		return prompt_system, documents, metadatas


	def ask_rag(self, question):

		prompt_system, documents, metadatas = self.build_context(question)
		
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
	vector_db_path="my_vector_db"

	rag_object = Rag(vector_db_path=vector_db_path)

	rag_response, documents, metadatas = rag_object.ask_rag(question="Quelle est la couleur et le nom du chat de Bob ?")

	print(rag_response)
	print("-"*20)
	for index_document in range(len(documents)):
		print(f"Documents {index_document}")
		print(documents[index_document])
		for key, value in metadatas[index_document].items():
			print(f"{key} : {value}")
		print("---")