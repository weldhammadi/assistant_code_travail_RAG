from src.vector_db import VectorDB


def test_create_vector_db_and_retrieve(tmp_path, mini_corpus):
	vector_db_path = str(tmp_path / "vector_db")

	vector_db = VectorDB(vector_db_path=vector_db_path, corpus_dict=mini_corpus)
	results = vector_db.retrieve("Quelle est la durée du préavis en cas de licenciement ?")

	assert len(results) > 0
	assert results[0]["num"] == "TEST-PREAVIS"
	assert "préavis" in results[0]["text"].lower()


def test_load_vector_db_reuses_persisted_data(tmp_path, mini_corpus):
	vector_db_path = str(tmp_path / "vector_db")
	VectorDB(vector_db_path=vector_db_path, corpus_dict=mini_corpus)

	reloaded_vector_db = VectorDB(vector_db_path=vector_db_path)
	results = reloaded_vector_db.retrieve("Combien de jours de congés payés par mois ?")

	assert len(results) > 0
	assert results[0]["num"] == "TEST-CONGES"
