import pytest
import json
import re
from unittest.mock import patch
from data_prep.code_orchestrator import CodeOrchestrator

@pytest.fixture
def section_patterns():
    return [("partie_racine", re.compile(r"^\s*Partie\s+(l[ée]gislative|r[ée]glementaire)", re.IGNORECASE))]

@pytest.fixture
def sample_tree():
    return {
        "data": {"title": "Partie législative"},
        "children": [{
            "data": {
                "num": "L1111-1", "cid": "ID123", "etat": "VIGUEUR",
                "texte": "Texte de l'article.", "dateDebut": 12345
            }
        }]
    }

class TestCodeOrchestrator:

    @patch("code_downloader.CodeTravailDownloader.load")
    def test_orchestrator_run_and_save(self, mock_load, section_patterns, sample_tree, tmp_path):
        """Vérifie que l'orchestrateur déroule tout le pipeline et sauvegarde un JSON valide."""
        mock_load.return_value = sample_tree
        output_file = tmp_path / "output" / "corpus_test.json"
        
        orchestrator = CodeOrchestrator(
            output_path=output_file,
            raw_cache_dir=tmp_path / "raw",
            source_url_template="http://test.com/{legi_id}",
            legifrance_article_url_template="http://legifrance/{id}",
            legi_id="TXT_TEST",
            code_name="Code de test",
            section_patterns=section_patterns
        )
        
        chunks = orchestrator.run(force_download=False, limit=None)
        
        # Vérification des chunks en mémoire
        assert len(chunks) == 1
        assert chunks[0].categorie == "legislatif"
        
        # Vérification du fichier sauvegardé
        assert output_file.exists()
        with open(output_file, "r", encoding="utf-8") as f:
            saved_json = json.load(f)
            
        assert len(saved_json) == 1
        assert saved_json[0]["num"] == "L1111-1"
        assert saved_json[0]["categorie"] == "legislatif"

    @patch("code_downloader.CodeTravailDownloader.load")
    def test_orchestrator_limit_parameter(self, mock_load, section_patterns, sample_tree, tmp_path):
        """Vérifie que le paramètre 'limit' restreint correctement le nombre de chunks en sortie."""
        mock_load.return_value = sample_tree
        
        orchestrator = CodeOrchestrator(
            output_path=tmp_path / "corpus.json",
            raw_cache_dir=tmp_path / "raw",
            source_url_template="http://test.com/{legi_id}",
            legifrance_article_url_template="http://legifrance/{id}",
            legi_id="TXT_TEST",
            code_name="Code de test",
            section_patterns=section_patterns,
            max_chars=5  # force un découpage en plusieurs sous-chunks (part1, part2...)
        )
        
        # On demande une limite stricte de 1 seul chunk
        chunks = orchestrator.run(limit=1)
        assert len(chunks) == 1