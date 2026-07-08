import sys
from pathlib import Path
import json

if __name__ == "__main__":
	sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb
from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL, VECTOR_DB_PATH, PARSED_CORPUS_PATH

import os

class VectorDB:
	def __init__(self, vector_db_path="", corpus_dict=None):
		if os.path.exists(vector_db_path):
			self.load_vector_db(vector_db_path)

		elif not corpus_dict:
			raise ValueError("Aucun chunk n'a été fourni pour créer la base de données vectorielle.")
		
		else:
			self.create_vector_db(vector_db_path, corpus_dict)


	def load_vector_db(self, vector_db_path):
		print("Loading Vector DB")
		self.chroma_vector_db = chromadb.PersistentClient(path=vector_db_path)
		collection = self.chroma_vector_db.get_collection(name="code_travail_rag_knowledge")

		if "embedding_model" in collection.metadata.keys():
			self.sentence_transformers_object = SentenceTransformer(collection.metadata["embedding_model"])
		else:
			raise(Exception("Error : we miss the embeddings model's name information"))

	
	def create_vector_db(self, vector_db_path, corpus_dict):
		print("Creating Vector DB")
		self.sentence_transformers_object = SentenceTransformer(EMBEDDING_MODEL)

		self.chroma_vector_db = chromadb.PersistentClient(path=vector_db_path)

		collection = self.chroma_vector_db.get_or_create_collection(
			name="code_travail_rag_knowledge",
			metadata={
				"embedding_model": EMBEDDING_MODEL
			}
		)

		chunks = [chunk["text"] for chunk in corpus_dict]
		embeddings = self.get_embeddings(chunks)

		collection.add(
    		ids=[chunk["id"] for chunk in corpus_dict],
    		documents=[chunk["text"] for chunk in corpus_dict],
    		embeddings=embeddings,
			metadatas=[
				{
					"id": chunk["id"],
					"code": chunk.get("code", "Code du travail"),
					"source": chunk.get("source", "Inconnue"),
					"categorie": chunk.get("categorie", "Inconnue"),
					"num": chunk.get("num") if chunk.get("num") is not None else "",
					"cid": chunk.get("cid") if chunk.get("cid") is not None else "",
					"etat": chunk.get("etat", "Inconnue"),
					"date_debut_vigueur": int(chunk["date_debut_vigueur"]) if chunk.get("date_debut_vigueur") is not None else 0,
					"date_fin_vigueur": int(chunk["date_fin_vigueur"]) if chunk.get("date_fin_vigueur") is not None else 0,
					"url": chunk.get("url") if chunk.get("url") is not None else ""
				}
				for chunk in corpus_dict
			]
)

	def get_embeddings(self, chuncks):
		embeddings = self.sentence_transformers_object.encode(
			chuncks,
			batch_size=64,
			normalize_embeddings=True,
			show_progress_bar=True
		).tolist()
		return embeddings
	
	def retrieve(self, question: str, n: int = 5) -> list:
		"""Encode la question et extrait les n chunks les plus proches."""
		query_vector = self.get_embeddings(question)
		collection = self.chroma_vector_db.get_collection("code_travail_rag_knowledge")
		results = collection.query(
            query_embeddings=[query_vector],
            n_results=n
        )
		formatted_results = self.format_chroma_results(results)
		return formatted_results
	
	def format_chroma_results(self, results: dict) -> list[dict]:
    	# On extrait la première liste (index 0) car Chroma renvoie une liste de listes (batch)
		documents = results.get("documents", [[]])[0] if results.get("documents") else []
		metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
		
		formatted_results = []

		for text, meta in zip(documents, metadatas):
			meta = meta or {}
			formatted_results.append({
				"text": text,
				"id": meta.get("id", "Inconnue"),
				"code": meta.get("code", "Inconnue"),
				"source": meta.get("source", "Inconnue"),
				"categorie": meta.get("categorie", "Inconnue"),
				"num": meta.get("num"),                     # Renvoie None s'il n'existe pas
				"cid": meta.get("cid"),                     # Renvoie None s'il n'existe pas
				"etat": meta.get("etat", "Inconnue"),
				"date_debut_vigueur": meta.get("date_debut_vigueur"),
				"date_fin_vigueur": meta.get("date_fin_vigueur"),
				"url": meta.get("url")
			})
		return formatted_results



if __name__ == "__main__":
	with open(PARSED_CORPUS_PATH, "r", encoding="utf-8") as f:
		corpus_dict = json.load(f)
	vector_db_object = VectorDB(str(VECTOR_DB_PATH), corpus_dict)
	print(vector_db_object.retrieve(question="De quoi parle l'article L1?"))