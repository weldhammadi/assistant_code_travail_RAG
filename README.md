# Assistant Code du travail (RAG)

Assistant juridique qui répond en langage naturel à des questions sur le droit du travail français, en
citant systématiquement les articles du Code du travail sur lesquels il s'appuie, et en refusant de
répondre quand l'information n'est pas dans sa base plutôt que d'inventer. Projet M2 MD5 — Data & IA
(voir [pf.md](pf.md) pour l'énoncé complet).

Construit sans LangChain ni LlamaIndex : chunking, embeddings, base vectorielle, prompt et appel LLM sont
tous implémentés à la main.

## Prérequis

- Python 3.11+
- Une clé API [Groq](https://console.groq.com) (gratuite)
- Accès réseau pour le téléchargement initial du corpus (~56 Mo, une seule fois, mis en cache ensuite)

## Installation

```bash
python -m venv .venv
.venv/Scripts/activate        # ou source .venv/bin/activate sous Linux/macOS
pip install -r requirements.txt
cp .env.example .env          # puis renseigner GROQ_API_KEY dans .env
```

## Utilisation

### 1. Constituer le corpus (une seule fois)

```bash
python data_prep/code_cli.py
```

Télécharge le Code du travail depuis le miroir JSON [SocialGouv/legi-data](https://github.com/SocialGouv/legi-data)
(mis en cache dans `data/raw/`, jamais retéléchargé sauf `--force-download`), le parse en une liste plate
d'articles (`data/corpus_code_travail.json`), et écrit `data/corpus_meta.json` (date de génération, utilisée
pour l'avertissement de fraîcheur — voir Q3 plus bas). `data/` est gitignored : chaque développeur régénère
son propre corpus.

> **Important : lancer ce script directement** (`python data_prep/code_cli.py`), pas via
> `python -m data_prep.code_cli` — les imports internes du dossier `data_prep/` sont volontairement plats
> (`from code_orchestrator import ...`) et ne se résolvent que lorsque `data_prep/` lui-même est ajouté à
> `sys.path`, ce que Python ne fait qu'en exécution directe.

Résultat sur le corpus complet : **11 710 chunks** (4 432 législatifs, 7 213 réglementaires, 65 autres),
couvrant l'intégralité du Code du travail — largement plus que les 5 thèmes minimum exigés, puisque
l'ingestion télécharge le code entier plutôt qu'une sélection de thèmes.

Options utiles : `--limit N` (limiter le nombre de chunks, pratique pour tester rapidement),
`--include-abroges` (inclure les articles abrogés), `--max-chars` (taille avant découpage d'un article).

### 2. Interroger l'assistant en ligne de commande

```bash
python cli.py
```

Construit `my_vector_db/` depuis `data/corpus_code_travail.json` au premier lancement (calcul des
embeddings, quelques minutes sur CPU pour le corpus complet), puis le recharge tel quel aux lancements
suivants — **aucune réindexation** au redémarrage. Affiche la date du corpus, la réponse, les articles
source (numéro, section, URL Légifrance) et l'avertissement juridique. Tapez `quit`, `exit` ou `q` pour
sortir proprement.

### 3. Interface web (alternative)

```bash
uvicorn api:app --reload
```

Puis ouvrir `http://127.0.0.1:8000`. Même moteur (`src/rag.py`) que la CLI, via une UI HTML/CSS/JS
statique (`static/index.html`, sans dépendance externe) et deux endpoints : `POST /ask` (réponse +
articles sources dédoublonnés, avec lien Légifrance) et `GET /meta` (date et taille du corpus).
L'interface affiche les articles cités sous chaque réponse (cliquables vers Légifrance), la date du
corpus dans l'en-tête — avec le même avertissement de fraîcheur à 180 jours que la CLI (Q3) — et
l'avertissement juridique, ainsi que des exemples de questions au premier chargement.

**Déploiement (Railway)** : `Procfile` + `railway.json` sont fournis. Comme `data/` et `my_vector_db/`
sont gitignored, un conteneur fraîchement déployé n'a ni l'un ni l'autre — `src/bootstrap.py` gère ça
automatiquement au démarrage (télécharge + parse + indexe si rien n'existe), mais ce premier boot prend
plusieurs minutes (surtout le calcul des embeddings), d'où le `healthcheckTimeout` étendu dans
`railway.json`. Pour ne pas refaire ce travail à chaque déploiement, montez un volume persistant et
pointez-y ces deux variables d'environnement :

```
DATA_DIR=/chemin/vers/le/volume/data
VECTOR_DB_PATH=/chemin/vers/le/volume/my_vector_db
```

(en plus de `GROQ_API_KEY`). Sans volume monté, chaque redéploiement reconstruit tout depuis zéro.

Ce volume sert aussi de référence à `src/auto_refresh.py` (voir Q3) : au démarrage, l'API ne relance un
rafraîchissement immédiat que si le corpus déjà présent sur le volume a plus de 24h, sinon elle attend
l'échéance normale — un redéploiement ne déclenche donc pas de reconstruction inutile si le corpus est
déjà frais.

### 4. Valider le retrieval (Jalon 3, avant tout appel LLM)

```bash
python scripts/evaluate_retrieval.py
```

Vérifie, pour 5 questions dont l'article attendu est connu à l'avance, que cet article remonte dans le
top-k de la recherche vectorielle — sans jamais appeler le LLM. Résultat actuel sur le corpus réel :
**4/5**, avec une limite connue documentée ci-dessous (Q1).

### 5. Mettre à jour le corpus depuis GitHub

```bash
python scripts/update_corpus.py
```

En production (`api.py`), ce rafraîchissement est automatique et quotidien — voir Q3 plus bas et
`src/auto_refresh.py`. Ce script manuel reste utile en local (CLI, dev) ou pour forcer un rafraîchissement
immédiat sans attendre l'échéance quotidienne : il force le retéléchargement (contrairement à l'étape 1,
qui réutilise le cache local), reparse, puis reconstruit entièrement `my_vector_db/` **en place**. Contrairement
au rafraîchissement automatique de l'API (qui reconstruit à côté puis bascule dessus sans interruption), ce
script supprime la base existante avant de la recréer : il refuse donc proprement (message explicite) si
la base est verrouillée par un `cli.py`/`api.py` encore lancé, plutôt que d'échouer avec une erreur système
opaque.

### 6. Tests

```bash
pytest
```

31 tests, aucun mock (vrais appels Groq, vrais embeddings) — nécessite `GROQ_API_KEY` dans `.env`. La
plupart utilisent une petite fixture (`tests/fixtures/mini_corpus.json`, 4 articles fictifs) pour ne pas
dépendre du téléchargement réel ; `tests/test_code_*.py` couvrent le pipeline d'ingestion. ~90s en tout.
Pas encore de fichier de test dédié pour `src/decomposer.py` ni `src/auto_refresh.py` (voir Limites
connues ci-dessous) — `test_rag.py` les exerce indirectement via `ask_rag`, mais sans cas isolés.

## Architecture

```
data_prep/     ingestion : téléchargement (cache local) -> parsing de l'arbre Légifrance -> JSON de chunks
src/           config, agent Groq de base, modérateur, décomposeur de question (HyDE), base vectorielle
               (Chroma), RAG, bootstrap partagé, rafraîchissement automatique quotidien (auto_refresh.py)
prompts/       prompts système (RAG, modérateur, décomposeur), séparés du code
scripts/       evaluate_retrieval.py (Jalon 3), update_corpus.py (rafraîchir manuellement depuis GitHub)
cli.py         boucle interactive en ligne de commande (module d'interrogation)
api.py         API FastAPI + UI web statique, avec rafraîchissement quotidien du corpus en tâche de fond
tests/         un fichier de test par module, + fixtures/mini_corpus.json
```

## Choix techniques

- **Embeddings** : `distiluse-base-multilingual-cased-v2` (sentence-transformers) — multilingue, tourne
  correctement sur CPU, suffisant pour du français juridique sans nécessiter de GPU.
- **Base vectorielle** : ChromaDB en mode persistant local. Le nom du modèle d'embedding est stocké dans
  les métadonnées de la collection (`VectorDB.create_vector_db`), pour que le rechargement (`load_vector_db`)
  sache toujours avec quel modèle réencoder les questions — contrainte explicite de l'énoncé.
- **LLM** : Groq (`openai/gpt-oss-120b`), `temperature=0` pour des réponses aussi déterministes que
  possible sur un usage juridique.
- **Modération** : un second modèle, plus petit (`openai/gpt-oss-safeguard-20b`), classifie chaque
  question en amont (`src/moderator.py`) pour détecter les tentatives de détournement de prompt ; en cas
  de détection, ni la recherche vectorielle ni le LLM principal ne sont appelés. C'est l'amélioration
  retenue pour le Jalon 6.
- **Décomposition de question (HyDE)** : avant la recherche vectorielle, `src/decomposer.py`
  (`Decomposer`, même modèle que le modérateur) découpe la question de l'utilisateur en 2 à 4
  sous-questions atomiques, puis reformule chacune en une affirmation hypothétique de type article de
  loi (technique HyDE — la reformulation ressemble davantage à ce qu'on cherche dans la base qu'une
  question à la première personne). `Rag._retrieve_deduplicated` (`src/rag.py`) recherche séparément
  pour chaque sous-question (8 chunks chacune), déduplique les résultats par id, et plafonne à 20 chunks
  au total (`Rag.MAX_TOTAL_CHUNKS`) pour ne pas exploser le prompt système. En cas d'échec du modèle
  (parsing, timeout...), `decompose()` retombe silencieusement sur `[question]` telle quelle — la
  question originale continue d'être cherchée, jamais de blocage du pipeline.
- **Rafraîchissement automatique quotidien** : la source amont (SocialGouv/legi-data) est mise à jour
  tous les jours ; `api.py` lance un job APScheduler (`src/auto_refresh.py`) qui reconstruit le corpus et
  la base vectorielle une fois par jour, dans un dossier temporaire distinct de la base active, puis
  bascule l'objet `Rag` dessus une fois prêt — aucune interruption de service, et un échec (réseau,
  parsing) laisse simplement l'ancienne base continuer à répondre. Voir Q3 ci-dessous.
- **Avertissement juridique** : ajouté par le code (`Rag.DISCLAIMER`, dans `src/rag.py`), pas seulement
  demandé au LLM dans le prompt — voir Q2 ci-dessous pour la justification.

## Réponses aux questions de réflexion

### Q1 — Granularité du chunking

Retenu : **un chunk par article** (découpé en sous-blocs sur les frontières de paragraphes si l'article
dépasse `max_chars`), avec le fil d'Ariane hiérarchique (Livre > Titre > Chapitre > Section > Sous-section)
préfixé dans le texte embeddé lui-même — une approche hybride légère plutôt qu'un choix strictement binaire.

Avantages du chunking par article : citation précise (chaque chunk correspond exactement à ce qu'on peut
citer), cohérent avec la façon dont le droit se référence lui-même ("au sens de l'article L1234-5"), évite
qu'une réponse ponctuelle soit noyée dans un gros bloc de section. Inconvénient : une question qui demande
une vue d'ensemble d'une section entière (ex. "quels sont tous mes droits en cas de licenciement
économique ?") peut nécessiter plusieurs chunks pour reconstituer l'ensemble — le top-k doit être
suffisamment large. Le regroupement par section aurait l'effet inverse (plus de contexte par chunk, mais
citation moins précise et chunks parfois très volumineux).

Le breadcrumb intégré au texte embeddé est la partie "hybride" : il donne à l'article un minimum de
contexte thématique sans changer la granularité de citation. **Limite observée en pratique** (voir
`evaluate_retrieval.py`, Jalon 3) : pour la question sur la durée du préavis, l'article attendu (`L1234-1`)
ne remonte qu'en 11e position, derrière des articles voisins de la même sous-section (indemnité de
licenciement, remboursement d'allocations chômage) dont le breadcrumb est quasiment identique. Un test
rapide (comparaison de similarité cosinus avec/sans breadcrumb) a écarté l'hypothèse d'une dilution par le
breadcrumb — la similarité *baisse* quand on le retire — donc la cause est une imprécision du modèle
d'embedding sur cette formulation, pas un défaut du breadcrumb lui-même. Retenu comme limite connue plutôt
que masqué (voir le compte rendu pour les pistes d'amélioration).

**Mise à jour depuis l'ajout du décomposeur (HyDE)** : `evaluate_retrieval.py` interroge encore
directement `VectorDB.retrieve` (une seule requête, k=5) et ce résultat 4/5 reste valable tel quel ; en
usage réel via `Rag.ask_rag`, la question passe d'abord par `Decomposer` (voir Choix techniques
ci-dessus), qui élargit le budget de retrieval à 8 chunks par sous-question (jusqu'à 20 au total). Cela
ne change rien à l'article `L1234-1` isolé (rang 11 dans une recherche à une seule requête), mais réduit
concrètement le risque documenté ici pour les questions composées : chaque sous-idée récupère son propre
top-k plutôt que de se partager un seul top-5 global.

### Q2 — Traçabilité

Le numéro d'article est stocké **aux deux endroits** : dans le texte embeddé (préfixe `Article {num} -
{breadcrumb}` en tête de chaque chunk) et dans les métadonnées Chroma (`num`, `cid`, `source`, `categorie`,
`etat`, dates de vigueur, `url` Légifrance). La duplication est volontaire : le texte embeddé sert à la
recherche sémantique, les métadonnées servent à la citation fiable et à l'affichage (CLI et API).

Pour que le LLM cite correctement plutôt que d'inventer : `Rag.build_context` étiquette explicitement
chaque chunk injecté dans le prompt (`[Article {num}]`), et le prompt système (`prompts/rag_prompt_system.txt`)
interdit explicitement d'inventer un numéro d'article ou de citer un article absent du contexte fourni.
**Limite assumée** : il n'y a pas de vérification programmatique a posteriori que les numéros cités dans
la réponse appartiennent bien à l'ensemble fourni — la garantie repose sur l'instruction du prompt, pas
sur un contrôle de code. C'est un axe d'amélioration identifié pour la suite.

### Q3 — Fraîcheur

`data_prep/code_orchestrator.py` écrit un fichier `data/corpus_meta.json` (date de génération, URL
source, nombre de chunks) à chaque exécution de l'ingestion. `cli.py` lit ce fichier au démarrage et
affiche la date du corpus ; si le corpus a plus de 180 jours, un avertissement explicite s'affiche
("le droit du travail évolue... vérifiez qu'aucune réforme récente n'a modifié les articles cités").
L'interface web affiche la même information via `GET /meta` (pastille dans l'en-tête, passant en
avertissement au-delà du même seuil de 180 jours).

Au-delà de l'avertissement, l'API (`api.py`) résout activement le problème : la source amont étant mise
à jour quotidiennement, un job planifié (`src/auto_refresh.py`, via APScheduler) retélécharge, reparse et
reconstruit la base vectorielle une fois par jour, en tâche de fond. La reconstruction se fait dans un
dossier temporaire séparé de la base servant les requêtes en cours ; une fois prête, `Rag.vector_db_object`
bascule dessus atomiquement, et l'ancien dossier temporaire est supprimé. Aucune requête utilisateur n'est
interrompue pendant la reconstruction (qui prend plusieurs minutes, surtout le calcul des embeddings), et
un échec (réseau, parsing) est simplement journalisé — la base précédente continue de répondre. Le premier
rafraîchissement après un déploiement ne se déclenche que si le corpus déjà présent (volume persistant) a
plus de 24h (`seconds_until_next_refresh`, basé sur `corpus_meta.json`), pour ne pas annuler l'intérêt du
volume monté (voir Déploiement ci-dessus) en reconstruisant inutilement à chaque redémarrage.

Ceci ne couvre que le process API : `cli.py` (usage local/ponctuel) n'a pas de rafraîchissement en tâche
de fond — il reste sur `scripts/update_corpus.py` (rafraîchissement manuel) ou sur le corpus déjà présent
en cache, d'où le maintien de la bannière de fraîcheur pour ce chemin-là.

### Q4 — Réponses conditionnelles

Le prompt système instruit le LLM de signaler les réserves (taille d'entreprise, convention collective,
ancienneté...) et de donner la réponse générale assortie de ces réserves plutôt que de trancher à la place
de l'utilisateur, et de ne poser une question de clarification que si l'information manquante est
réellement indispensable pour répondre correctement — pas systématiquement, pour rester utilisable en une
seule question dans le cas courant.

### Q5 — La frontière du conseil juridique

Le prompt distingue explicitement les questions factuelles auxquelles le Code répond directement (durée
légale, nombre de jours...) des questions qui demandent une interprétation d'une situation personnelle
(ex. "mon licenciement est-il abusif ?"). Pour ces dernières, l'assistant est instruit d'expliquer le
cadre légal et les critères pertinents à partir du contexte, sans rendre de verdict sur le cas de
l'utilisateur, et de l'orienter vers un professionnel (avocat, inspection du travail, défenseur syndical).
Ceci est complété par l'avertissement juridique systématique et par le modérateur en amont.

### Sur l'avertissement juridique lui-même

pf.md pose la question directement : où cette garantie est-elle la plus fiable, dans le prompt ou dans le
code ? Choix retenu : **dans le code**, pas seulement demandé au LLM. `Rag.DISCLAIMER` (constante de
classe dans `src/rag.py`) est concaténé à la réponse sur *tous* les chemins de retour de `ask_rag` — refus
du modérateur compris — donc son absence est structurellement impossible plutôt que statistiquement rare.
Le prompt système, lui, indique explicitement au LLM de ne *pas* ajouter sa propre mention, pour éviter un
avertissement dupliqué.

## Limites connues / pistes d'amélioration

Voir le compte rendu pour le détail — en résumé : pas de vérification programmatique des citations (Q2),
la limite de retrieval documentée en Q1 (candidate naturelle pour une recherche hybride lexicale +
vectorielle, en particulier pour les questions citant un numéro d'article explicite), et pas encore de
tests dédiés pour `src/decomposer.py` / `src/auto_refresh.py` (couverts indirectement par `test_rag.py`,
sans cas isolés — ex. franges du fallback `[question]` du décomposeur, ou l'échec réseau/parsing du
rafraîchissement automatique).

## Suite du projet

La suite du projet inclus l'intégration d'un agent récupérateur des articles référencés dans d'autres articles.
Celui-ci passera par l'API Legifrance pour récupérer les textes de lois sous-jacents et les donner au LLM afin de fournir une réponse plus complete.

On pourra aussi mettre en place un agent de détection des dates afin de potentiellement répondre aux questions de l'utilisateur à un certain moment. Ex: "en 2003, était-il obligatoire de trvailler 35 heures par semaine?"