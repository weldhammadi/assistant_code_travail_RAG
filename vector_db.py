import chromadb
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL

import os
import pandas

class VectorDB:
	def __init__(self, vector_db_path="", chuncks=None):
		if os.path.exists(vector_db_path):
			self.load_vector_db(vector_db_path)


		elif chuncks:
			self.create_vector_db(vector_db_path, chuncks)


	def load_vector_db(self, vector_db_path):
		pass



	def create_vector_db(self, vector_db_path, chuncks):
		self.sentence_transformers_object = SentenceTransformer(EMBEDDING_MODEL)



	def get_embeddings(self, chuncks):
		embeddings = self.sentence_transformers_object.encode(
			chuncks,
			batch_size=64,
			normalize_embeddings=True,
			show_progress_bar=True
		).tolist()
		return embeddings



	def retrieve(self, question, n=3):
		pass


if __name__ == "__main__":
	vector_db_path="my_vector_db"
	chuncks=pandas.read_csv("05_corpus_rag.csv")

	vector_db_object = VectorDB(vector_db_path, chuncks)