# Project State — Assistant Code du travail (RAG)

This file is the source of truth for where the project stands. Read this instead of re-deriving
project state from scratch each session. The spec is [pf.md](pf.md) (M2 MD5 assignment, 2026).

## What this project is

A RAG assistant answering French labour-law ("Code du travail") questions, citing article numbers,
refusing to answer outside its corpus, and always appending a legal disclaimer. Built without
LangChain/LlamaIndex (forbidden by the assignment) — every brick (chunking, embeddings, vector store,
prompt, LLM call) is hand-rolled.

Note: this repo started life as a smaller "mini-TP" demo project (fictional corpus about "Bob's cat" —
`05_corpus_rag.csv`, still present at repo root but unused/dead). It was pivoted to the real Code du
travail project via the `feature/integrate-new-data` branch (data_prep/ pipeline + real vector_db.py
rewrite). The historical log below (from the mini-TP phase) is kept for context but paths/behavior it
describes may no longer match current code.

## Architecture

```
data_prep/              # Jalon 1 — ingestion pipeline (not a package import path at runtime; run as scripts)
  code_downloader.py     CodeTravailDownloader: downloads+caches raw Légifrance JSON (SocialGouv/legi-data mirror)
  code_parser.py          CodeTravailParser: walks the JSON tree -> flat list of Chunk (one per article,
                           split on paragraph boundaries if > max_chars). Builds breadcrumb hierarchy,
                           infers categorie (legislatif/reglementaire/autre), dedupes ids.
  chunk_structure.py      Chunk dataclass: id, text, code, source, categorie, num, cid, etat,
                           date_debut_vigueur, date_fin_vigueur, url
  code_orchestrator.py    CodeOrchestrator: download -> parse -> write JSON corpus + summary print
  code_cli.py              CLI entrypoint (argparse) -> python -m data_prep.code_cli (or run directly)
                           writes to data/corpus_code_travail.json by default (data/ is gitignored)

src/                     # package (absolute imports `from src.x import y`, sys.path bootstrap for direct run)
  config.py               env (GROQ_API_KEY), paths (BASE_DIR, PROMPTS_DIR, CORPUS_PATH [dead/unused],
                           PARSED_CORPUS_PATH, VECTOR_DB_PATH), Légifrance constants (SOURCE_URL_TEMPLATE,
                           LEGI_TEXT_ID, SECTION_PATTERNS...), model names (EMBEDDING_MODEL,
                           LLM_MODEL="openai/gpt-oss-120b", MODERATOR_MODEL="openai/gpt-oss-safeguard-20b")
  agent.py                 Agent: thin Groq client wrapper + static read_file helper
  moderator.py              Moderator(Agent): prompt-injection classifier, JSON output {is_prompt_injection}
  vector_db.py              VectorDB: create_vector_db (embed+persist to Chroma, batched inserts,
                           embedding model name stored in collection metadata) / load_vector_db
                           (reload without reindexing — checked via os.path.exists(vector_db_path), NOTE:
                           a pre-created-but-empty directory will wrongly look "existing" — see tests/test_rag.py
                           fixture workaround). retrieve(question, n=5) -> list[dict] (NOT a tuple).
  rag.py                    Rag(Agent): build_context() formats retrieved chunks with [Article N] labels
                           into the system prompt; ask_rag() moderates first (refuses+disclaimer, no LLM/
                           retrieval call if flagged), else retrieves -> LLM call (temp=0) -> appends
                           Rag.DISCLAIMER to every response path. Rag.REFUSAL / Rag.DISCLAIMER are class
                           constants.

prompts/
  rag_prompt_system.txt    Code-du-travail-specific: citation obligation, refusal wording ("je ne trouve
                           pas cette information dans ma base"), multi-part question handling, conditional
                           answer caveats (Q4), legal-advice boundary (Q5), explicitly told NOT to
                           self-append a disclaimer (code guarantees it instead).
  moderator_system.txt     Code-du-travail-specific injection-detection prompt (domain description fixed,
                           no longer references the old "Bob's cat" demo).

api.py                   FastAPI app. lifespan: if VECTOR_DB_PATH missing, builds it from
                           PARSED_CORPUS_PATH JSON (raises clear RuntimeError telling user to run
                           data_prep.code_cli first if that JSON is also missing) via
                           VectorDB(corpus_dict=...). GET / serves static/index.html. POST /ask ->
                           {"answer": str} (disclaimer already baked into the string by Rag.ask_rag).
static/index.html        vanilla HTML/CSS/JS chat UI, no build step.
Procfile                  web: uvicorn api:app --host 0.0.0.0 --port $PORT

tests/
  conftest.py               sys.path bootstrap (repo root + data_prep/) + mini_corpus fixture
                           (scope="module" — required because test_rag.py's module-scoped `rag` fixture
                           depends on it; a function-scoped fixture would ScopeMismatch-error).
  fixtures/mini_corpus.json  4 fake-but-realistic chunks (TEST-PREAVIS, TEST-CONGES, TEST-RUPTURE,
                           TEST-SMIC), one per topic, used by test_vector_db/test_rag/test_api instead of
                           requiring a real Légifrance download for every test run. IDs are deliberately
                           fake (TEST-*) so nobody mistakes fixture text for real law.
  test_vector_db.py, test_rag.py, test_api.py   rewritten this session (see log) to match the current
                           VectorDB(corpus_dict=...) / retrieve()->list[dict] API — the old versions
                           called a corpus_df/pandas/CSV signature that no longer exists.
  test_code_*.py            cover data_prep/ (downloader/parser/orchestrator) — pre-existing, untouched.
  test_agent.py, test_config.py, test_moderator.py   pre-existing, mostly untouched (test_moderator.py's
                           example question swapped from "Bob's cat" to a labour-law question).

All 29 tests pass with real Groq calls + real embeddings (no mocking, per this repo's established style;
GROQ_API_KEY is present in .env). Full suite runtime ~60s.
```

## Status against pf.md (as of this session)

Done: Jalon 1 (ingestion), Jalon 2 (chunking+indexation+persistence, embedding model tracked), Jalon 6
bonus (moderator = "agent modérateur" improvement), git workflow (main/dev/feature+PRs already in git log).

Fixed this session: legal disclaimer now guaranteed in code (`Rag.DISCLAIMER`, appended to every
`ask_rag` return path — refusal and normal answer alike) rather than left to the LLM to remember;
`rag_prompt_system.txt`/`moderator_system.txt` rewritten for the real domain; `api.py` + `test_api.py`/
`test_vector_db.py`/`test_rag.py` fixed to match the current `VectorDB(corpus_dict=...)` signature
(were still calling a dead `corpus_df`/pandas/CSV API); `pandas` dropped from requirements.txt (no
longer used anywhere after that fix).

Still missing (see TodoWrite in active session, or re-derive from pf.md §5/§2 if starting fresh):
1. **Interactive CLI loop** ("module d'interrogation" — pf.md §2 and Jalon 5 both require a CLI
   question/answer REPL showing answer + source articles + disclaimer + clean exit. Currently only
   `api.py` (web) and `rag.py`'s single hardcoded `__main__` question exist.
2. **Retrieval validation script (Jalon 3)** — no script/test checks that, for ~5 known questions, the
   expected article shows up in top-k, before the LLM was wired in. Should be built as a standalone
   script/test using the real corpus (not the mini fixture) once it's been downloaded locally.
3. **README** — still just a one-line title. Needs: justified technical choices, answers to pf.md §4
   reflection questions (Q1 granularité chunking, Q2 traçabilité, Q3 fraîcheur, Q4 réponses
   conditionnelles, Q5 frontière conseil juridique), install/run instructions (mention running
   `data_prep.code_cli` before first `api.py` launch since `data/` is gitignored).
4. **Compte rendu (one page)** — difficulties, design decisions, what you'd do with more time. Doesn't
   exist anywhere in the repo yet.
5. **config.py cleanup** — `CORPUS_PATH` (pointing at a CSV under `data/raw/` that the pipeline never
   actually produces — only `PARSED_CORPUS_PATH`, the JSON, is real) is dead code left over from before
   the CSV->JSON rewrite. Should be removed once nothing references it (currently nothing does, post
   api.py fix).
6. Not yet verified: whether the full real downloaded corpus (`python -m data_prep.code_cli`) actually
   covers ≥5 of the 8 themes pf.md lists — should download for real and spot-check once step 2 (Jalon 3
   validation script) is built, since it downloads the whole Code du travail (not theme-limited) so this
   should hold by construction, but hasn't been run end-to-end in this session.

## Fraîcheur / corpus date (Q3, unresolved design question)

Not yet decided: how the system surfaces the corpus's download date / risk of obsolescence to the user.
No code addresses this yet — needs a decision (e.g. stamp the download date into the vector DB collection
metadata alongside `embedding_model`, surface it in the CLI/API). Worth deciding when answering Q3 in the
README, and implementing alongside the CLI loop (step 1 above) if a code answer (not just a README answer)
is wanted.

---

# Historical log (mini-TP demo phase — "Bob's cat" corpus)

Tracks the step-by-step integration of the **moderator** into this RAG project, following the plan in
[prep.md](prep.md) (a demo/reference project, not this one). Workflow: one step implemented at a time,
user commits/pushes to GitHub after each step before the next one starts.

Repo structure: originally a flat layout (`agent.py`, `config.py`, `rag.py`, `vector_db.py` at root) — steps 1-5 below were built that way. A structural refactor (see bottom of log) later moved code into `src/`, prompts into `prompts/`, keeping `tests/` as-is; file links in the early log entries point at the paths as they were at the time, not necessarily where they live now. **The mini-TP's own corpus/vector-db/rag code has since been superseded by the real Code du travail data_prep/ pipeline — treat retrieve()/VectorDB signatures mentioned below as historical, not current (see Architecture section above for current signatures).**

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
