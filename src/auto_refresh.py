"""Rafraîchissement quotidien automatique du corpus, en tâche de fond dans le process api.py.

La source amont (SocialGouv/legi-data) est mise à jour tous les jours ; sans ce module,
`data/` et `my_vector_db/` restent figés à l'état du dernier déploiement jusqu'à un lancement
manuel de `scripts/update_corpus.py` (voir Q3 dans le README). Contrairement à ce script manuel
(qui supprime `my_vector_db/` en place et refuse de tourner si un `api.py` a la base ouverte),
la reconstruction se fait ici dans un dossier temporaire séparé, puis `rag.vector_db_object`
est basculé dessus une fois prêt -- le process qui sert déjà les requêtes ne voit jamais la
base disparaître, et un échec (réseau, parsing...) laisse simplement l'ancienne base active.
"""
import json
import logging
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "data_prep"))

from code_orchestrator import CodeOrchestrator  # noqa: E402

from src import config  # noqa: E402
from src.vector_db import VectorDB  # noqa: E402

logger = logging.getLogger("auto_refresh")

REFRESH_INTERVAL_HOURS = 24

_previous_tmp_dir: Path | None = None


def refresh_rag(rag) -> None:
    """Retélécharge le corpus (force), reconstruit une base vectorielle dans un dossier
    temporaire, puis bascule `rag.vector_db_object` dessus. N'écrase jamais la base en cours
    de service : en cas d'échec, l'ancienne base continue de répondre aux requêtes."""
    global _previous_tmp_dir

    try:
        orchestrator = CodeOrchestrator(
            output_path=config.PARSED_CORPUS_PATH,
            raw_cache_dir=config.RAW_CACHE_DIR,
            source_url_template=config.SOURCE_URL_TEMPLATE,
            legifrance_article_url_template=config.LEGIFRANCE_ARTICLE_URL_TEMPLATE,
            legi_id=config.LEGI_TEXT_ID,
            code_name=config.CODE_NAME,
            section_patterns=config.SECTION_PATTERNS,
        )
        logger.info("Rafraîchissement quotidien : retéléchargement + reparsing du corpus...")
        orchestrator.run(force_download=True)

        with open(config.PARSED_CORPUS_PATH, "r", encoding="utf-8") as f:
            corpus_dict = json.load(f)

        tmp_path = config.VECTOR_DB_PATH.parent / f"{config.VECTOR_DB_PATH.name}_refresh_{int(time.time())}"
        logger.info(f"Reconstruction de la base vectorielle dans {tmp_path}...")
        new_vector_db = VectorDB(vector_db_path=str(tmp_path), corpus_dict=corpus_dict)

        rag.vector_db_object = new_vector_db
        logger.info("Base vectorielle rafraîchie et activée.")

        if _previous_tmp_dir is not None and _previous_tmp_dir.exists():
            shutil.rmtree(_previous_tmp_dir, ignore_errors=True)
        _previous_tmp_dir = tmp_path

    except Exception:
        logger.exception(
            "Échec du rafraîchissement quotidien du corpus -- la base précédente reste active."
        )


def seconds_until_next_refresh() -> float:
    """Calcule le délai avant le premier rafraîchissement, à partir de la fraîcheur connue du
    corpus (corpus_meta.json). Évite de reconstruire inutilement au démarrage si le volume
    persistant contient déjà un corpus généré il y a moins de REFRESH_INTERVAL_HOURS (voir la
    note sur le volume Railway dans le README) ; renvoie 0 si le corpus est absent ou périmé."""
    if not config.CORPUS_META_PATH.exists():
        return 0

    with open(config.CORPUS_META_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    generated_at = meta.get("generated_at")
    if not generated_at:
        return 0

    generated_dt = datetime.fromisoformat(generated_at).replace(tzinfo=timezone.utc)
    next_refresh_dt = generated_dt + timedelta(hours=REFRESH_INTERVAL_HOURS)
    return max((next_refresh_dt - datetime.now(timezone.utc)).total_seconds(), 0)
