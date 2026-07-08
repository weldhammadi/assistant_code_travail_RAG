"""
Parsing de l'arborescence Légifrance
"""
import re
import sys
from pathlib import Path
from typing import Optional
from chunk_structure import Chunk

if __name__ == "__main__":
	sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import LEGIFRANCE_ARTICLE_URL, CODE_NAME, SECTION_PATTERNS, LEGI_TEXT_ID

class CodeTravailParser:
    """Transforme l'arbre JSON Légifrance en une liste plate de Chunk."""

    def __init__(self, include_abroges: bool = False, max_chars: int = 3000):
        self.include_abroges = include_abroges
        self.max_chars = max_chars
        self._id_counts: dict = {}
        self.section_patterns = SECTION_PATTERNS
        self.legifrancearticle_url = LEGIFRANCE_ARTICLE_URL
        self.code_name = CODE_NAME

    # API publique
    def parse(self, raw_tree: dict) -> list:
        """Point d'entrée : parcourt l'arbre et retourne la liste de Chunk dédupliqués."""
        self._id_counts = {}
        chunks = self._walk(raw_tree, hierarchy={})
        return chunks

    # Parcours récursif
    def _walk(self, node: dict, hierarchy: dict) -> list:
        chunks = []
        data = node.get("data", {})
        children = node.get("children")

        if children:
            title = self._clean_text(data.get("title", ""))
            level = self._classify_section(title)
            new_hierarchy = dict(hierarchy)
            if level != "autre":
                new_hierarchy[level] = title
            for child in children:
                chunks.extend(self._walk(child, new_hierarchy))
            return chunks

        article_chunks = self._build_article_chunks(data, hierarchy)
        chunks.extend(article_chunks)
        return chunks

    def _build_article_chunks(self, data: dict, hierarchy: dict) -> list:
        """Construit un ou plusieurs Chunk à partir d'un nœud feuille (article)."""
        if "texte" not in data:
            return []

        etat = data.get("etat", "INCONNU")
        if etat != "VIGUEUR" and not self.include_abroges:
            return []

        text = self._clean_text(data.get("texte", ""))
        if not text:
            return []

        num = data.get("num") or data.get("cid")
        cid = data.get("cid")
        categorie = self._infer_categorie(num)
        breadcrumb = self._build_breadcrumb(hierarchy)
        
        # Récupération de l'ID de la version la plus récente
        versions = data.get("articleVersions", [])
        latest_id = cid
        if versions:
            # Tri ou sélection de la version avec la date de début la plus récente
            latest_version = max(versions, key=lambda v: v.get("dateDebut") or 0)
            latest_id = latest_version.get("id", cid)
            
        url = self.legifrancearticle_url.format(id=latest_id) if latest_id else None

        blocks = self._split_long_text(text) if len(text) > self.max_chars else [text]

        chunks = []
        for i, block in enumerate(blocks):
            chunk_id = num if len(blocks) == 1 else f"{num}_part{i + 1}"
            chunk_id = self._make_unique_id(chunk_id, cid)
            chunks.append(
                Chunk(
                    id=chunk_id,
                    text=f"Article {num} - {breadcrumb}\n\n{block}",
                    code=self.code_name,
                    source=breadcrumb or self.code_name,
                    categorie=categorie,
                    num=num,
                    cid=cid,
                    etat=etat,
                    date_debut_vigueur=data.get("dateDebut"),
                    date_fin_vigueur=data.get("dateFin"),
                    url=url,
                )
            )
        return chunks

    # Aides internes
    def _classify_section(self, title: str) -> str:
        for level, pattern in self.section_patterns:
            if pattern.match(title or ""):
                return level
        return "autre"

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _infer_categorie(num: Optional[str]) -> str:
        if not num:
            return "autre"
        if num.upper().startswith("L"):
            return "legislatif"
        if num.upper().startswith("R"):
            return "reglementaire"
        return "autre"

    @staticmethod
    def _build_breadcrumb(hierarchy: dict) -> str:
        """Construit un fil d'Ariane à partir de l'arborescence 
        (partie > livre > titre > chapitre > section > sous-section)."""
        return " > ".join(
            v for v in [
                hierarchy.get("partie"), hierarchy.get("livre"), hierarchy.get("titre"),
                hierarchy.get("chapitre"), hierarchy.get("section"), hierarchy.get("sous_section"),
            ] if v
        )

    def _split_long_text(self, text: str) -> list:
        """Découpe un article trop long en sous-blocs, en respectant les paragraphes."""
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        blocks, current = [], ""

        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) > self.max_chars and current:
                blocks.append(current.strip())
                current = paragraph
            else:
                current = candidate

        if current.strip():
            blocks.append(current.strip())

        # Cas limite : un seul paragraphe déjà trop long (ex: tableau) -> découpage brut.
        final_blocks = []
        for block in blocks:
            if len(block) <= self.max_chars:
                final_blocks.append(block)
            else:
                for i in range(0, len(block), self.max_chars):
                    final_blocks.append(block[i: i + self.max_chars])

        return final_blocks or [text]

    def _make_unique_id(self, base_id: str, cid: Optional[str]) -> str:
        """Garantit l'unicité des id (certains articles génériques type 'Annexe' se répètent)."""
        if base_id not in self._id_counts:
            self._id_counts[base_id] = 0
            return base_id

        self._id_counts[base_id] += 1
        suffix = (cid or "")[-6:] or str(self._id_counts[base_id])
        return f"{base_id}_{suffix}"
    
if __name__ == "__main__":
    # Test rapide du parser
    import json
    from data_prep.code_downloader import CodeTravailDownloader

    downloader = CodeTravailDownloader(LEGI_TEXT_ID, cache_dir=Path("raw_cache"))
    raw_tree = downloader.load(force_download=False)

    parser = CodeTravailParser(include_abroges=False, max_chars=3000)
    chunks = parser.parse(raw_tree)

    print(f"Nombre de chunks générés : {len(chunks)}")
    for chunk in chunks[:5]:
        print(json.dumps(chunk.to_dict(), ensure_ascii=False, indent=2))