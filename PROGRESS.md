# Progress Log

Tracks the step-by-step integration of the **moderator** into this RAG project, following the plan in [prep.md](prep.md). Workflow: one step implemented at a time, user commits/pushes to GitHub after each step before the next one starts.

Repo structure: originally a flat layout (`agent.py`, `config.py`, `rag.py`, `vector_db.py` at root) — steps 1-5 below were built that way. A structural refactor (see bottom of log) later moved code into `src/`, prompts into `prompts/`, keeping `tests/` as-is; file links in the early log entries point at the paths as they were at the time, not necessarily where they live now.

## Plan (checklist) 

- [x] Step 1 — `MODERATOR_SYSTEM_PROMPT_PATH` constant added to `config.py` (`MODERATOR_MODEL` already existed)
- [x] Step 2 — `moderator_system.txt` prompt file, adapted to the "Bob's cat" corpus context
- [x] Step 3 — `moderator.py` with `Moderator(Agent)` class
- [x] Step 4 — Wire `Moderator` into `rag.py`'s `ask_rag`: moderate first, refuse without ever calling the main LLM
- [x] Step 5 — `tests/` folder with one test file per project module
- [x] Structural refactor — moved code/prompts into `src/` and `prompts/` (before building the UI)
- [x] Branch sync — rebased `feature/user-interface` onto `dev` to pick up the moderator work + refactor
- [x] UI — `api.py` (FastAPI), `static/index.html` (vanilla chat UI), `Procfile`, `tests/test_api.py`

## Log

### Step 1 — config constant (done)
- Added `BASE_DIR = Path(__file__).resolve().parent` and `MODERATOR_SYSTEM_PROMPT_PATH = BASE_DIR / "moderator_system.txt"` to [config.py](config.py).
- Not committed/pushed by assistant — user handles git per project convention.

### Step 2 — moderator prompt file (done)
- Created [moderator_system.txt](moderator_system.txt) at repo root (matches `MODERATOR_SYSTEM_PROMPT_PATH` from step 1).
- Copied from prep.md's template; adapted the "Contexte" paragraph to mention this project's actual corpus (fiches animalières / Bob's cat) instead of a generic one.

### Step 3 — Moderator class (done)
- Created [moderator.py](moderator.py): `Moderator(Agent)` with a `moderate(question)` method, mirroring prep.md's design but adapted to this repo's flat imports (`import config`, `from agent import Agent`) and existing `config.MODERATOR_MODEL` constant (kept its name rather than introducing prep.md's `MODERATION_MODEL`).
- Returns `{"is_prompt_injection": bool}` via Groq's `response_format={"type": "json_object"}`.
- Includes a `__main__` smoke test block (legit question vs. an injection attempt), matching the style already used in `rag.py` and `vector_db.py`.

### Step 4 — wired into rag.py (done)
- [rag.py](rag.py): `Rag.__init__` now builds `self.moderator = Moderator()`.
- Added `Rag.REFUSAL` class constant with the refusal message.
- `ask_rag` now calls `self.moderator.moderate(question)` first; if `is_prompt_injection` is true it returns `(self.REFUSAL, [], [])` immediately — the main LLM (`LLM_MODEL`) and the vector DB retrieval are never reached in that path.

### Step 5 — tests/ folder, one file per module (done)
Scope grew from prep.md's single `test_moderator.py` to full coverage: user asked for tests for every function of the project, one file per module, all under `tests/`.

- [tests/conftest.py](tests/conftest.py): inserts the repo root onto `sys.path` so flat root-level modules (`agent`, `config`, `moderator`, `rag`, `vector_db`) import cleanly regardless of pytest's invocation dir (there's no `src/` package here, unlike prep.md's reference).
- [tests/test_agent.py](tests/test_agent.py): `Agent.read_file` reads a temp file's content; `Agent()` builds a Groq client.
- [tests/test_config.py](tests/test_config.py): `BASE_DIR` is correct, `MODERATOR_SYSTEM_PROMPT_PATH` exists on disk, model constants are non-empty strings.
- [tests/test_moderator.py](tests/test_moderator.py): legitimate question → `is_prompt_injection: False`; injection attempt → `True` (real Groq call, no mocking, matching this repo's existing style).
- [tests/test_vector_db.py](tests/test_vector_db.py): builds a temp Chroma vector DB from `05_corpus_rag.csv`, retrieves and checks it finds "Henri" (Bob's cat); reloads the persisted DB and confirms retrieval still works.
- [tests/test_rag.py](tests/test_rag.py): `build_context` embeds retrieved chunks into the system prompt; `ask_rag` answers from the corpus for a legit question; `ask_rag` returns `Rag.REFUSAL` with empty `documents`/`metadatas` for an injection attempt (proves the LLM/retrieval path is skipped).
- Added `pytest` to [requirements.txt](requirements.txt).

**Verified:** ran `pytest --collect-only` — all 5 test modules import and collect correctly (no syntax/wiring errors). Full test runs require the developer's own `.env` with `GROQ_API_KEY` plus `pip install -r requirements.txt` in their environment — this sandbox has neither, so actual test execution (real Groq calls + embedding downloads) needs to happen on your machine.

### Structural refactor — src/, prompts/, tests/ (done)
Requested before starting the web UI: reorganize the flat file layout into a clean, maintainable structure — no logic changes, only file locations, imports and path constants.

New layout:
```
src/
  __init__.py
  agent.py
  config.py
  moderator.py
  rag.py
  vector_db.py
prompts/
  moderator_system.txt
  rag_prompt_system.txt
tests/
  conftest.py
  test_agent.py
  test_config.py
  test_moderator.py
  test_rag.py
  test_vector_db.py
05_corpus_rag.csv   (left at repo root — not mentioned in the ask)
```

- Moved `agent.py`, `config.py`, `moderator.py`, `rag.py`, `vector_db.py` into `src/` via `git mv` (keeps file history); added empty `src/__init__.py` to make it a real package.
- Moved `moderator_system.txt` and `rag_prompt_system.txt` into `prompts/` via `git mv`.
- [src/config.py](src/config.py): `BASE_DIR` now resolves to the **project root** (`Path(__file__).resolve().parent.parent`, since `config.py` itself moved one level deeper into `src/`); added `PROMPTS_DIR = BASE_DIR / "prompts"`; `MODERATOR_SYSTEM_PROMPT_PATH` now points under `PROMPTS_DIR`; added a new `RAG_PROMPT_SYSTEM_PATH` constant (needed because `rag.py` used to hardcode `"./rag_prompt_system.txt"` as a cwd-relative path — that had to become a real config path once the file moved, otherwise it would silently break).
- Switched all intra-package imports to relative (`from .config import ...`, `from .agent import Agent`, etc.) in `agent.py`, `moderator.py`, `rag.py`, `vector_db.py` — mirrors the exact package convention prep.md's own reference design already used (`from . import config`, `from .agent import Agent`), so this repo now matches that pattern for real instead of just documenting it.
- [src/rag.py](src/rag.py)'s `build_context` now reads the prompt via `RAG_PROMPT_SYSTEM_PATH` from config instead of the old hardcoded relative path.
- Updated all five `tests/*.py` files to import from the `src` package (`from src.agent import Agent`, `from src import config`, etc.); `tests/conftest.py` already inserted the repo root onto `sys.path`, which is what makes `src` importable as a package from there.
- Fixed `tests/test_config.py`'s `BASE_DIR` assertion, which checked for `config.py` directly under `BASE_DIR` — no longer true now that `config.py` lives in `src/`; also added a test for the new `RAG_PROMPT_SYSTEM_PATH` constant.
- Cleaned up stray `__pycache__/` and `.pytest_cache/` directories left at the repo root from before the move (both already gitignored, never tracked).

**Follow-up fix — direct script execution:** relative imports (`from .agent import Agent`) broke running these files directly (`python src/rag.py`, or VSCode's ▶ "Run Python File", both invoke the file as a plain script, not as part of the package) with `ImportError: attempted relative import with no known parent package`. Fixed by switching `agent.py`, `moderator.py`, `rag.py`, `vector_db.py` to **absolute** imports (`from src.agent import Agent`, `from src import config`, etc.) plus a small bootstrap at the top of each file:

```python
if __name__ == "__main__":
	sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

This inserts the repo root onto `sys.path` only when the file is run directly (harmless no-op otherwise — `python -m src.rag` and normal package imports already have the root on `sys.path`). Result: `python src/rag.py`, `python -m src.rag`, VSCode's ▶ button, and `from src.rag import Rag` from outside the package (e.g. the upcoming `api.py`) all work the same way now.

Also made `vector_db.py`'s `__main__` block cwd-independent: it now loads `05_corpus_rag.csv` via `BASE_DIR / "05_corpus_rag.csv"` (from `config`) instead of the relative string `"05_corpus_rag.csv"`, which would break if the script were launched from a directory other than the repo root.

**Verified:** `python src/rag.py` and `python -m src.rag` both now fail only on the sandbox's missing `pandas` install (past the import-resolution stage); `pytest --collect-only` still collects all 8 tests cleanly (2 pre-existing `pandas`-related collection errors, unrelated to this fix).

### Branch sync — feature/user-interface rebased onto dev (done)
User had created `feature/user-interface` before the moderator work + structural refactor landed on `dev` (it was still sitting at `0e72e75`, "feature: now we have a working rag" — pre-moderator). Asked user merge vs. rebase; chose rebase.

- `git checkout feature/user-interface` then `git rebase dev` — no conflicts.
- Turned out to be a pure fast-forward: `feature/user-interface` had no commits of its own yet, so rebasing just moved it to `dev`'s tip (`84b6647`) without rewriting any history. Confirmed via `git merge-base --is-ancestor origin/feature/user-interface feature/user-interface` → true, so a plain `git push` (no `--force`) is enough.
- Not pushed by the assistant — user pushes themselves, per this project's established workflow (confirmed explicitly: assistant does not run git commands beyond what's directly asked).

### UI — api.py, static/index.html, Procfile, tests/test_api.py (done)
Built on top of prep.md's steps 7-9, adapted to the now-`src/`-packaged code and to this repo's actual `Rag` class (whose `ask_rag` returns a 3-tuple `(answer, documents, metadatas)`, unlike prep.md's assumed single-return `answer_question`).

- [src/config.py](src/config.py): added `CORPUS_PATH = BASE_DIR / "05_corpus_rag.csv"` and `VECTOR_DB_PATH = BASE_DIR / "my_vector_db"` — single source of truth for both paths, now reused everywhere instead of scattered literals. Updated `src/vector_db.py`'s and `src/rag.py`'s `__main__` blocks, plus `tests/test_vector_db.py` and `tests/test_rag.py`, to use these constants instead of hardcoded `"my_vector_db"` / `"05_corpus_rag.csv"` strings.
- [api.py](api.py) (root): FastAPI app with a `lifespan` that builds `my_vector_db/` from the corpus CSV if it doesn't exist yet, then instantiates `Rag`. `GET /` serves `static/index.html`; `POST /ask` takes `{"question": str}` and returns `{"answer": str}` (moderation refusal and normal answers both flow through the same field — the contract stays a plain string either way).
- [static/index.html](static/index.html): single self-contained vanilla HTML/CSS/JS chat UI (no external dependencies, no build step) — auto-growing textarea, Enter-to-send (Shift+Enter for newline), light/dark aware via `prefers-color-scheme`, distinct bubble style reserved for client-side network errors (the API itself doesn't distinguish a moderation refusal from a normal answer at the wire level, so both render as a normal assistant bubble).
- [Procfile](Procfile): `web: uvicorn api:app --host 0.0.0.0 --port $PORT`.
- [tests/test_api.py](tests/test_api.py): real integration tests via `fastapi.testclient.TestClient` — legit question returns an answer mentioning "henri" (Bob's cat), an injection attempt returns the moderator's refusal text, and `GET /` serves HTML. Added `httpx` to [requirements.txt](requirements.txt) since `TestClient` needs it.
- **Found and fixed a gap while wiring this up:** `my_vector_db/` (the persisted Chroma DB directory) was not in [.gitignore](.gitignore) — added `/my_vector_db/` so this generated, potentially large binary data directory never gets committed.

**Verified:** `pytest --collect-only` after all of the above — 8 tests collected, only the pre-existing `pandas`-dependent modules erroring in this sandbox (no `pandas`/`.env` here); `python -m py_compile api.py` passes.
