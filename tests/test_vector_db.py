import pandas

from src.vector_db import VectorDB


def test_create_vector_db_and_retrieve(tmp_path):
	vector_db_path = str(tmp_path / "vector_db")
	corpus_df = pandas.read_csv("05_corpus_rag.csv")

	vector_db = VectorDB(vector_db_path=vector_db_path, corpus_df=corpus_df)
	documents, metadatas = vector_db.retrieve("Quelle est la couleur et le nom du chat de Bob ?")

	assert len(documents) == 3
	assert len(metadatas) == 3
	assert any("henri" in document.lower() for document in documents)


def test_load_vector_db_reuses_persisted_data(tmp_path):
	vector_db_path = str(tmp_path / "vector_db")
	corpus_df = pandas.read_csv("05_corpus_rag.csv")
	VectorDB(vector_db_path=vector_db_path, corpus_df=corpus_df)

	reloaded_vector_db = VectorDB(vector_db_path=vector_db_path)
	documents, metadatas = reloaded_vector_db.retrieve("Quelle est la couleur et le nom du chat de Bob ?")

	assert len(documents) == 3
	assert len(metadatas) == 3
