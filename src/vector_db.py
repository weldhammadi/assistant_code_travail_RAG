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

		print("Calcul des embeddings en cours...")
		texts = [chunk["text"] for chunk in corpus_dict]
		embeddings = self.get_embeddings(texts)

		# 1. Préparation de toutes les listes
		ids = [chunk["id"] for chunk in corpus_dict]
		metadatas = [
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

		# 2. Insertion par lots (batches) pour éviter la limite de 5461 de ChromaDB
		batch_size = 5000 
		print(f"Insertion de {len(ids)} chunks dans ChromaDB par lots de {batch_size}...")
		
		for i in range(0, len(ids), batch_size):
			end_idx = i + batch_size
			collection.add(
				ids=ids[i:end_idx],
				documents=texts[i:end_idx],
				embeddings=embeddings[i:end_idx],
				metadatas=metadatas[i:end_idx]
			)
			print(f"  -> Batch inséré : {min(end_idx, len(ids))}/{len(ids)}")

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
		formatted_results = self._format_chroma_results(results)
		return formatted_results
	
	def _format_chroma_results(self, results: dict) -> list[dict]:
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
	print(vector_db_object.retrieve(
		question="Bonjour, je fais des recherches sur la réglementation du temps de travail en France. "
		"Pourriez-vous m'indiquer quelle est la durée légale hebdomadaire du travail pour un salarié "
		"à temps plein, quel est le nombre maximal d'heures supplémentaires autorisées par semaine, "
		"et quelle est la durée minimale du repos quotidien entre deux journées de travail ? "
		"Je m'intéresse aussi à la durée légale des congés payés acquis par an. Merci beaucoup.")
		)