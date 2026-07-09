"""
Orchestrator for the data preparation pipeline.
"""
from datetime import datetime, timezone
from pathlib import Path
from code_downloader import CodeTravailDownloader
from code_parser import CodeTravailParser
import sys
from typing import Optional
import json

class CodeOrchestrator:
    """Chef d'orchestre : téléchargement -> parsing -> écriture du corpus JSON."""
    def __init__(
        self,
        output_path: Path,
        raw_cache_dir: Path,
        source_url_template: str,
        legifrance_article_url_template: str,
        legi_id: str,
        code_name: str,
        section_patterns: list,
        include_abroges: bool = False,
        max_chars: int = 3000,
    ):
        self.output_path = output_path
        self.meta_path = output_path.parent / "corpus_meta.json"
        self.downloader = CodeTravailDownloader(source_url_template, legi_id, cache_dir=raw_cache_dir)
        self.parser = CodeTravailParser(section_patterns=section_patterns, 
                                        raw_json_code={}, 
                                        legifrance_article_url_template=legifrance_article_url_template, 
                                        code_name=code_name, 
                                        include_abroges=include_abroges, 
                                        max_chars=max_chars)
        self.chunks: list = []

    def run(self, force_download: bool = False, limit: Optional[int] = None) -> list:
        raw_tree = self.downloader.load(force_download=force_download)
        self.chunks = self.parser.parse(raw_tree)

        if limit:
            self.chunks = self.chunks[:limit]

        self._save()
        self._save_meta()
        self._print_summary()
        return self.chunks

    def _save(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self.chunks], f, indent=2, ensure_ascii=False)

    def _save_meta(self) -> None:
        """Trace la date de génération du corpus (Q3 - fraîcheur), pour que l'assistant puisse
        avertir l'utilisateur du risque d'obsolescence sans avoir à réindexer pour le savoir."""
        meta = {
            "generated_at": datetime.now(timezone.utc).date().isoformat(),
            "source_url": self.downloader.source_url,
            "chunk_count": len(self.chunks),
        }
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def _print_summary(self) -> None:
        legislatif = sum(1 for c in self.chunks if c.categorie == "legislatif")
        reglementaire = sum(1 for c in self.chunks if c.categorie == "reglementaire")
        print(f"\n{len(self.chunks)} chunks générés -> {self.output_path}")
        print(f"  dont législatif : {legislatif}")
        print(f"  dont réglementaire : {reglementaire}")
        print(f"  dont autre : {len(self.chunks) - legislatif - reglementaire}")