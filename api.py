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


@app.post("/ask")
async def ask(payload: Question):
	answer, documents, metadatas = rag.ask_rag(payload.question)
	return {"answer": answer}
