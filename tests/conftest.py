import sys
from pathlib import Path

# Racine du projet (pour trouver data_prep.xxx)
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

# Dossier des sources (pour que les scripts se trouvent entre eux sans le préfixe data_prep)
data_prep_dir = root_dir / "data_prep"
sys.path.insert(0, str(data_prep_dir))