# Compte rendu — Assistant Code du travail (RAG)

## Difficultés rencontrées

**Dérive entre le code et l'usage réel du projet.** Le dépôt est parti d'un mini-TP de démonstration
(corpus fictif "le chat de Bob") avant d'être basculé sur le vrai Code du travail via un pipeline
d'ingestion (`data_prep/`) et une réécriture de `VectorDB` (signature `corpus_dict` au lieu d'un
DataFrame pandas chargé depuis un CSV). Cette bascule n'avait pas été répercutée partout : `api.py` et
trois fichiers de tests (`test_api.py`, `test_vector_db.py`, `test_rag.py`) appelaient encore l'ancienne
API et auraient échoué au premier lancement réel. Les avoir retrouvés et corrigés — en s'appuyant sur une
petite fixture dédiée (`tests/fixtures/mini_corpus.json`) plutôt que sur le vrai téléchargement pour
garder les tests rapides — a pris plus de temps que prévu, mais a évité de livrer un projet dont la moitié
des tests étaient silencieusement cassés.

**Un vrai résultat de retrieval imparfait.** En validant le retrieval sur le corpus réel (11 710 chunks,
Jalon 3), l'article attendu pour la question sur la durée du préavis (`L1234-1`) n'est ressorti qu'en
11e position, derrière deux articles voisins traitant d'un sujet différent (indemnité de licenciement,
remboursement d'allocations chômage). Plutôt que d'ajuster la question de test pour la faire "passer", le
choix a été de creuser : un test rapide de similarité cosinus a permis d'écarter l'hypothèse d'une
dilution par le fil d'Ariane hiérarchique injecté dans le texte embeddé (le retirer *dégrade* la
similarité, il ne la pollue pas). La cause réelle semble être une limite du modèle d'embedding
multilingue sur cette formulation précise. Gardé comme résultat honnête (4/5) plutôt que masqué.

**Un blocage Windows sans rapport avec le code.** La reconstruction de la base vectorielle réelle a
d'abord échoué : le dossier `my_vector_db/` était verrouillé par deux instances de `uvicorn api:app`
restées ouvertes depuis une session précédente. Diagnostiqué via `Get-CimInstance Win32_Process` (ligne de
commande complète des processus) plutôt que de forcer une suppression à l'aveugle.

## Décisions de conception

- **Chunking par article + fil d'Ariane hiérarchique intégré au texte embeddé** (approche hybride, pas un
  choix binaire article/section) — détaillé et justifié en Q1 du README.
- **Avertissement juridique garanti par le code**, pas seulement demandé au LLM dans le prompt
  (`Rag.DISCLAIMER`, concaténé sur *tous* les chemins de retour de `ask_rag`, y compris le refus du
  modérateur) — c'est la contrainte "éliminatoire" de l'énoncé, elle ne pouvait pas reposer sur la
  mémoire du modèle.
- **Modérateur en amont comme amélioration du Jalon 6** : un second modèle, plus petit, classifie la
  question avant tout accès à la base vectorielle ou au LLM principal — cohérent avec l'esprit "on
  n'appelle pas le gros modèle si ce n'est pas nécessaire".
- **Fraîcheur via un fichier `corpus_meta.json` séparé** plutôt que dans les métadonnées Chroma : décision
  volontaire pour ne pas coupler la date du corpus à une réindexation complète (~8 min sur le corpus
  réel) — le pipeline d'ingestion peut tracer sa propre date sans toucher à la base vectorielle.

## Ce que je ferais avec plus de temps

1. **Vérification programmatique des citations** : parser la réponse du LLM pour s'assurer que chaque
   numéro d'article cité appartient bien à l'ensemble des chunks fournis, plutôt que de faire reposer
   cette garantie uniquement sur l'instruction du prompt (limite assumée en Q2 du README).
2. **Recherche hybride lexicale + vectorielle** : la faiblesse de retrieval documentée en Jalon 3 suggère
   qu'une recherche par mot-clé sur les numéros d'articles (complémentaire à la recherche vectorielle)
   fiabiliserait à la fois les questions citant un article explicite ("que dit L3121-1 ?") et les cas où
   l'embedding se trompe entre articles voisins d'une même sous-section.
3. **Élargir le jeu d'évaluation** au-delà des 5 questions minimales, et suivre le score au fil des
   itérations de chunking/embedding plutôt que de le valider une seule fois.
4. **Fraîcheur côté API**, pas seulement en CLI — actuellement seule la boucle en ligne de commande
   affiche la date du corpus au démarrage.
5. **Uniformiser les imports de `data_prep/`** avec le style package-relatif déjà utilisé dans `src/` :
   `data_prep/` ne fonctionne aujourd'hui qu'en exécution directe (`python data_prep/code_cli.py`), pas
   via `python -m data_prep.code_cli` — documenté comme contrainte dans le README plutôt que corrigé.
