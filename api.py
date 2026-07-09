import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src import config
from src.rag import Rag
from src.vector_db import VectorDB

rag = None


@asynccontextmanager
async def lifespan(app: FastAPI):
	global rag

	if not os.path.exists(config.VECTOR_DB_PATH):
		if not config.PARSED_CORPUS_PATH.exists():
			raise RuntimeError(
				f"Corpus introuvable ({config.PARSED_CORPUS_PATH}). "
				"Lancez d'abord l'ingestion : python -m data_prep.code_cli"
			)
		with open(config.PARSED_CORPUS_PATH, "r", encoding="utf-8") as f:
			corpus_dict = json.load(f)
		VectorDB(vector_db_path=str(config.VECTOR_DB_PATH), corpus_dict=corpus_dict)

	rag = Rag(vector_db_path=str(config.VECTOR_DB_PATH))
	yield


app = FastAPI(lifespan=lifespan)


class Question(BaseModel):
	question: str


@app.get("/")
async def index():
	return FileResponse("static/index.html")


@app.post("/ask")
async def ask(payload: Question):
	answer, documents, metadatas = rag.ask_rag(payload.question)
	return {"answer": answer}
