"""
Code downloader for fetching data from Legifrance.
"""
import json
import urllib.request
from pathlib import Path
from ..src.config import SOURCE_URL_TEMPLATE

class CodeTravailDownloader:
    """Télécharge (avec cache local) le JSON brut d'un texte Légifrance."""

    def __init__(self, legi_id: str, cache_dir: Path):
        self.legi_id = legi_id
        self.cache_path = cache_dir / f"{legi_id}.json"

    @property
    def source_url(self) -> str:
        return self.SOURCE_URL_TEMPLATE.format(legi_id=self.legi_id)

    def download(self, force: bool = False) -> Path:
        """Télécharge le fichier si nécessaire et retourne son chemin local."""
        if self.cache_path.exists() and not force:
            print(f"Fichier source déjà présent en cache : {self.cache_path}")
            return self.cache_path

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Téléchargement depuis {self.source_url} ...")
        urllib.request.urlretrieve(self.source_url, self.cache_path)
        print(f"Téléchargement terminé : {self.cache_path}")
        return self.cache_path

    def load(self, force_download: bool = False) -> dict:
        """Télécharge si besoin puis charge le JSON en mémoire."""
        path = self.download(force=force_download)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)