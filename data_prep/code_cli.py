"""
Module de test pipeline de chunks du Code du travail
"""
from pathlib import Path
import argparse
from code_orchestrator import CodeOrchestrator
import sys

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    SOURCE_URL_TEMPLATE,
    LEGI_TEXT_ID,
    CODE_NAME,
    SECTION_PATTERNS,
    LEGIFRANCE_ARTICLE_URL_TEMPLATE,
)

def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).parent.parent
    parser = argparse.ArgumentParser(description="Ingestion du Code du travail pour le pipeline RAG.")
    parser.add_argument(
        "--output", type=Path,
        default=project_root / "data" / "corpus_code_travail.json",
        help="Chemin du fichier JSON de sortie.",
    )
    parser.add_argument(
        "--raw-cache-dir", type=Path,
        default=project_root / "data" / "raw",
        help="Dossier de cache pour le JSON brut téléchargé.",
    )
    parser.add_argument("--include-abroges", action="store_true", help="Inclure aussi les articles abrogés/modifiés (par défaut : seulement en vigueur).")
    parser.add_argument("--max-chars", type=int, default=3000, help="Taille max (en caractères) d'un chunk avant découpage.")
    parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre de chunks générés (utile pour tester).")
    parser.add_argument("--force-download", action="store_true", help="Retélécharger la source même si elle est déjà en cache.")
    return parser.parse_args()


def main():
    args = parse_args()
    ingestor = CodeOrchestrator(
        output_path=args.output,
        raw_cache_dir=args.raw_cache_dir,
        source_url_template = SOURCE_URL_TEMPLATE,
        legi_id=LEGI_TEXT_ID,
        code_name=CODE_NAME,
        section_patterns=SECTION_PATTERNS,
        legifrance_article_url_template=LEGIFRANCE_ARTICLE_URL_TEMPLATE,
        include_abroges=args.include_abroges,
        max_chars=args.max_chars,
    )
    ingestor.run(force_download=args.force_download, limit=args.limit)


if __name__ == "__main__":
    main()
    