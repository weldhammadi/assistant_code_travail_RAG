"""
Orchestrator for the data preparation pipeline.
"""
from pathlib import Path
from code_downloader import CodeTravailDownloader
from code_parser import CodeTravailParser
import sys
from typing import Optional
import json

if __name__ == "__main__":
	sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
     
from src.config import LEGI_TEXT_ID

class CodeOrchestrator:
    """Chef d'orchestre : téléchargement -> parsing -> écriture du corpus JSON."""
    def __init__(
        self,
        output_path: Path,
        raw_cache_dir: Path,
        source_url_template: str,
        legi_id: str,
        code_name: str,
        section_patterns: list,
        include_abroges: bool = False,
        max_chars: int = 3000,
    ):
        self.output_path = output_path
        self.downloader = CodeTravailDownloader(source_url_template, legi_id, cache_dir=raw_cache_dir)
        self.parser = CodeTravailParser(section_patterns=section_patterns, 
                                        raw_json_code={}, 
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
        self._print_summary()
        return self.chunks
    
    def _save(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self.chunks], f, indent=2, ensure_ascii=False)

    def _print_summary(self) -> None:
        legislatif = sum(1 for c in self.chunks if c.categorie == "legislatif")
        reglementaire = sum(1 for c in self.chunks if c.categorie == "reglementaire")
        print(f"\n{len(self.chunks)} chunks générés -> {self.output_path}")
        print(f"  dont législatif : {legislatif}")
        print(f"  dont réglementaire : {reglementaire}")
        print(f"  dont autre : {len(self.chunks) - legislatif - reglementaire}")