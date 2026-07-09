import json
import sys
from pathlib import Path

import pytest

# Racine du projet (pour trouver data_prep.xxx)
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

# Dossier des sources (pour que les scripts se trouvent entre eux sans le préfixe data_prep)
data_prep_dir = root_dir / "data_prep"
sys.path.insert(0, str(data_prep_dir))

MINI_CORPUS_PATH = Path(__file__).resolve().parent / "fixtures" / "mini_corpus.json"


@pytest.fixture(scope="module")
def mini_corpus() -> list:
	"""Petit corpus de fixture (4 articles fictifs, un par thème) pour les tests hors-réseau."""
	with open(MINI_CORPUS_PATH, "r", encoding="utf-8") as f:
		return json.load(f)