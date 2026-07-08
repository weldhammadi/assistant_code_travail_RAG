import chromadb
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL

import os
import pandas

class VectorDB:
	def __init__(self, vector_db_path="", corpus_df=None):
		if os.path.exists(vector_db_path):
			self.load_vector_db(vector_db_path)


		elif not corpus_df.empty:
			self.create_vector_db(vector_db_path, corpus_df)


	def load_vector_db(self, vector_db_path):
		pass



	def create_vector_db(self, vector_db_path, corpus_df):
		self.sentence_transformers_object = SentenceTransformer(EMBEDDING_MODEL)

		self.chroma_vector_db = chromadb.PersistentClient(path=vector_db_path)

		collection = self.chroma_vector_db.get_or_create_collection(
			name="rag_knowledge",
			metadata={
				"embedding_model": EMBEDDING_MODEL
			}
		)

		chuncks = list(corpus_df["text"].values)

		embeddings = self.get_embeddings(chuncks)

		collection.add(
			ids = list(corpus_df["id"].values),
			documents=chuncks,
			embeddings=embeddings,
			metadatas=[{"source": row["source"] , "category": row["categorie"]} for _, row in corpus_df.iterrows()]
			)






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
	
	corpus_df=pandas.read_csv("05_corpus_rag.csv")

	vector_db_object = VectorDB(vector_db_path, corpus_df)