"""
Chunk structure for data preparation
"""
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Chunk:
    """Représente un chunk unitaire (un article, ou un sous-bloc d'article)."""

    id: str
    text: str
    code: str
    source: str
    categorie: str
    num: Optional[str]
    cid: Optional[str]
    etat: str
    date_debut_vigueur: Optional[int] = None
    date_fin_vigueur: Optional[int] = None
    url: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)