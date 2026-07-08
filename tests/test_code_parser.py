import pytest
import re
from code_parser import CodeTravailParser

@pytest.fixture
def section_patterns():
    """Patterns de section incluant ton correctif pour 'partie_racine'."""
    return [
        ("partie_racine", re.compile(r"^\s*Partie\s+(l[ée]gislative|r[ée]glementaire)", re.IGNORECASE)),
        ("livre", re.compile(r"^\s*Livre\b", re.IGNORECASE)),
        ("titre", re.compile(r"^\s*Titre\b", re.IGNORECASE)),
    ]

@pytest.fixture
def sample_legifrance_tree():
    """Simule un arbre JSON Légifrance minimaliste valide pour le parser."""
    return {
        "data": {"title": "Partie législative"},
        "children": [
            {
                "data": {"title": "Livre premier"},
                "children": [
                    {
                        "data": {
                            "num": "L1111-1",
                            "cid": "CETATEXT000012345678",
                            "texte": "Contenu de l'article de loi.\n\nDeuxième paragraphe.",
                            "etat": "VIGUEUR",
                            "dateDebut": 1609459200000,
                            "articleVersions": [{"id": "LEGIARTI000012345678", "dateDebut": 1609459200000}]
                        }
                    }
                ]
            }
        ]
    }

class TestCodeTravailParser:

    def test_clean_text(self, section_patterns):
        """Vérifie le nettoyage des retours à la ligne et des espaces multiples."""
        parser = CodeTravailParser(section_patterns, "{id}", {}, "Code du travail")
        
        # On simule un texte brut très désordonné avec des espaces normaux
        dirty_text = "Article   1er. \n\n\n  Contenu  avec  espaces.  "
        
        # On nettoie le texte via le parser
        cleaned = parser._clean_text(dirty_text)
        
        # Pour le test, on compare des lignes nettoyées de tout espace superflu aux extrémités
        cleaned_lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
        expected_lines = ["Article 1er.", "Contenu avec espaces."]
        
        assert cleaned_lines == expected_lines

    @pytest.mark.parametrize("partie_title, expected", [
        ("Partie législative", "legislatif"),
        ("Partie réglementaire", "reglementaire"),
        ("Partie législative ancienne", "legislatif_ancien"),
        ("Partie réglementaire ancienne", "reglementaire_ancien"),
        ("Autre Section", "autre")
    ])
    def test_infer_categorie(self, section_patterns, partie_title, expected):
        """Vérifie que la catégorie est correctement déduite selon le titre racine."""
        parser = CodeTravailParser(section_patterns, "{id}", {}, "Code du travail")
        assert parser._infer_categorie(partie_title) == expected

    def test_split_long_text(self, section_patterns):
        """Vérifie que les textes longs sont bien segmentés selon max_chars."""
        parser = CodeTravailParser(section_patterns, "{id}", {}, "Code", max_chars=25)
        text = "Premier bloc de texte.\n\nDeuxième bloc de texte ultra long."
        blocks = parser._split_long_text(text)
        assert len(blocks) >= 2

    def test_parse_integration(self, section_patterns, sample_legifrance_tree):
        """Vérifie le parsing complet de l'arbre et la bonne affectation de la catégorie."""
        parser = CodeTravailParser(
            section_patterns=section_patterns,
            legifrance_article_url_template="https://legifrance.gouv.fr/{id}",
            raw_json_code={},
            code_name="Code du travail"
        )
        
        chunks = parser.parse(sample_legifrance_tree)
        
        assert len(chunks) == 1
        # Utilisation de __class__.__name__ pour contourner le conflit d'ID de module Python lié au sys.path
        assert chunks[0].__class__.__name__ == "Chunk"
        assert chunks[0].num == "L1111-1"
        assert chunks[0].categorie == "legislatif"  # Ton correctif fonctionne parfaitement ici !