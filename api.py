import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src import config
from src.bootstrap import ensure_vector_db_built
from src.rag import Rag

rag = None


@asynccontextmanager
async def lifespan(app: FastAPI):
	global rag

	ensure_vector_db_built()
	rag = Rag(vector_db_path=str(config.VECTOR_DB_PATH))
	yield


app = FastAPI(lifespan=lifespan)


class Question(BaseModel):
	question: str


@app.get("/")
async def index():
	return FileResponse("static/index.html")


@app.get("/meta")
async def meta():
	"""Q3 (fraîcheur) : expose la date du corpus à l'interface web, comme le fait déjà la CLI."""
	if not config.CORPUS_META_PATH.exists():
		return {"generated_at": None, "chunk_count": None}
	with open(config.CORPUS_META_PATH, "r", encoding="utf-8") as f:
		corpus_meta = json.load(f)
	return {
		"generated_at": corpus_meta.get("generated_at"),
		"chunk_count": corpus_meta.get("chunk_count"),
	}


@app.post("/ask")
async def ask(payload: Question):
	answer, documents, metadatas = rag.ask_rag(payload.question)

	# Dédoublonne les articles (un article découpé en sous-blocs remonte en plusieurs chunks)
	sources = []
	seen = set()
	for meta in metadatas:
		key = (meta.get("num"), meta.get("url"))
		if key in seen:
			continue
		seen.add(key)
		sources.append({
			"num": meta.get("num"),
			"source": meta.get("source"),
			"etat": meta.get("etat"),
			"url": meta.get("url"),
		})

	return {"answer": answer, "sources": sources}
