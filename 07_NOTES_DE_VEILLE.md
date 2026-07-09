# Notes de veille — Piste A (GraphRAG) et Piste B (RAPTOR)

## A. Knowledge Graph (KG)

### Définition et fonctionnement

Un knowledge graph est composé de nœuds reliés par des arêtes.
- Un **nœud** décrit un objet quelconque : une personne, un bâtiment, un concept, etc.
- Une **arête** décrit la relation entre deux nœuds (relation à sens unique ou à double sens).
  - Ex : Ottawa ---- Canada, arête = « capitale »
  - Deux nœuds peuvent être reliés par plusieurs arêtes différentes.

Un KG utilise le NLP pour construire une vue des nœuds et des arêtes à travers un processus d'enrichissement sémantique. On peut par exemple prendre un livre et utiliser le NLP pour classifier son texte et créer des jeux de données corrélés et liés entre eux — c'est ainsi qu'on construit un KG. Il est également facile d'ajouter de nouvelles relations ou d'en supprimer (encore plus avec les LazyGraphRAG et les LightGraphRAG où la réindexation complète n'est pas nécessaire à chaque insertion).

Exemple d'usage : les vidéos recommandées sur YouTube s'appuient sur un KG pour proposer des vidéos pertinentes.

### Problèmes du RAG classique adressés par le KG

- **Fenêtre de contexte limitée** : les LLM ne peuvent traiter qu'une quantité limitée de texte à la fois. Le modèle peut manquer la vue d'ensemble si l'information cruciale est dispersée entre plusieurs chunks.
- **Inefficacités de la recherche sémantique** : même avec des embeddings vectoriels, la récupération reste locale — on récupère le texte le plus similaire, sans raisonner sur les relations entre les concepts.
- **Connaissance fragmentée** : si l'information nécessaire pour répondre à une question s'étend sur plusieurs chunks, le LLM doit la reconstituer à la volée. Ce n'est pas toujours fiable.

### Construction du graphe

Le graphe est composé de trois éléments :
1. **Nœuds** : objets, personnes, bâtiments, etc.
2. **Arêtes** : relations entre deux nœuds.
3. **Résumés de communauté** : une fois le graphe construit, un algorithme de clustering (Leiden) regroupe l'ensemble en communautés, et un LLM génère un rapport sur chaque communauté, à différents niveaux hiérarchiques.

Les niveaux de communauté décrivent la communauté ainsi que les niveaux hiérarchiques qu'elle englobe. Ils sont ensuite utilisés lors d'une sélection récursive pendant la recherche, pour choisir la communauté pertinente à chaque niveau.

Le moteur d'indexation crée ainsi un graphe de connaissances hiérarchique du jeu de données, où chaque niveau de la hiérarchie représente un degré différent d'abstraction et de résumé du matériau d'origine.

### Louvain vs Leiden, les deux algorithmes de clustering des graphes knowledge

- **Louvain** est un algorithme glouton : si deux nœuds sont reliés par une arête et que la requête porte sur cette arête, il va regrouper les deux nœuds en une seule grande communauté.
- **Leiden**, à l'inverse, va couper le lien et placer par exemple « Alice » dans l'une des deux communautés, mais jamais dans les deux à la fois.

**Fonctionnement de l'algorithme de Leiden** : il utilise la modularité, qui représente la qualité du partionnement des nodes, pour classifier en cluster. Une modularité calculée entre 2 nodes intra-classes est positive. De même, une modularité entre 2 nodes inter-classes sera négative. L'objectif est donc localement d'améliorer cette modularité pour recursivement améliorer la modularité globale.

Le processus se déroule en plusieurs phases répétitives (itérations) :

    Déplacement local (Local moving) : Chaque nœud est déplacé vers la communauté de l'un de ses voisins si cela améliore la modularité globale du réseau.

    Affinement (Refinement) : C'est l'innovation majeure de Leiden par rapport à son prédécesseur Louvain. Après le déplacement, l'algorithme tente d'affiner les communautés en divisant celles qui pourraient être mieux réparties, garantissant ainsi une meilleure qualité de partition.

    Agrégation (Aggregation) : Les communautés trouvées sont regroupées en "super-nœuds" pour créer un nouveau réseau simplifié.

    Répétition : Le processus recommence sur ce réseau simplifié jusqu'à ce qu'aucune amélioration supplémentaire ne puisse être faite.

### Coût et LazyGraphRAG

Un KG classique nécessite un résumé (de communauté) à plusieurs niveaux pour être construit → coût élevé, pour deux raisons :
- Multiplication des appels LLM : un résumé est créé pour chaque communauté, et ce pour absolument toutes les questions possibles, y compris celles qui ne seront jamais posées.
- Quand on insère une nouvelle relation dans le KG, tout doit être refait.

**LazyGraphRAG** ne nécessite pas de résumé préalable des données → coût comparable au RAG vectoriel, réduction du coût. Contrairement au GraphRAG classique, LazyGraphRAG ne résume une communauté que lorsque la question posée s'y rapporte réellement. Seule une indexation légère est créée et utilisée pour détecter les bonnes communautés. De plus, quand on insère une nouvelle relation, seule une petite partie de l'indexation doit être refaite (au lieu de tout reconstruire).

### ⚠️ Point de vigilance

La réduction de coût annoncée par Microsoft est très inférieure à ce qui est attendu. Le papier https://arxiv.org/abs/2506.06331 montre que la réduction de coût réelle avoisine plutôt 22 % (au maximum), et non 77 % (voire 99,9 % ???) comme annoncé.

### Utilisation en Python

#### A échelle locale

Pour débuter, expérimenter ou manipuler des volumes de données réduits (quelques milliers de nœuds), on utilise une approche "tout en mémoire" (RAM). En Python, cela se fait généralement via des bibliothèques comme **NetworkX** (pour les graphes génériques) ou **RDFlib** (pour le web sémantique et les standards du W3C).

* **Le principe :** Le graphe est construit et manipulé directement dans le script Python. Les données sont lues depuis un fichier local (JSON, CSV) et chargées en mémoire vive.
* **Les cas d'usage :** Analyse de données de taille moyenne, scripts d'automatisation, algorithmes de recherche de chemins ou calculs de centralité sur un échantillon de données.
* **Avantages :** Installation instantanée, aucune infrastructure ou base de données à gérer, idéal pour apprendre et tester des algorithmes.
* **Limites :** Le graphe disparaît à la fin de l'exécution du script si on ne le sauvegarde pas explicitement. De plus, la taille du graphe est strictement limitée par la mémoire RAM de l'ordinateur.

#### L'approche hybride : Le graphe de fichiers (Style "Obsidian")

Si L4objectif est de lier des connaissances textuelles, de la documentation ou des notes personnelles, vous pouvez adopter une approche décentralisée inspirée d'outils comme **Obsidian** ou **Logseq**.

* **Le principe :** Chaque nœud du graphe est un simple fichier texte au format Markdown (`.md`). Les relations (les arêtes) sont matérialisées par des liens hypertextes internes écrits directement dans le texte (généralement sous la forme `[[Nom de l'autre note]]`).
* **Le rôle de Python :** À l'aide de scripts simples, Python vient scanner votre dossier de notes, lit le texte, extrait les liens grâce à des expressions régulières, et recrée dynamiquement la cartographie de vos idées.
* **Avantages :** Les données restent des fichiers texte bruts, ce qui garantit une durabilité maximale (lisibles sur n'importe quel ordinateur, sans logiciel spécifique). C'est parfait pour le "Personal Knowledge Management" (PKM).
* **Limites :** Cette méthode n'est pas adaptée pour des requêtes de base de données complexes ou pour interconnecter des milliards de données structurées automatiquement.

#### À grande échelle : Les bases de données orientées graphe (Production)

Lorsque le volume de données dépasse les capacités d'une machine (millions ou milliards d'entités) ou que plusieurs utilisateurs doivent interroger le graphe en simultané et en temps réel, il faut basculer sur une architecture de production. On utilise alors une **Base de Données Orientée Graphe (GraphDB)** dédiée, comme **Neo4j**, connectée à Python via un driver officiel.

* **Le principe :** Python ne stocke plus le graphe. Il sert de chef d'orchestre : il extrait les données de vos sources (API, bases SQL, textes analysés par IA), les nettoie, et les envoie au serveur de base de données à l'aide d'un langage de requête spécialisé (comme *Cypher*).
* **Stratégies pour la grande échelle :**
* **Le traitement par lots (*Batching*) :** Pour intégrer de gros volumes, Python découpe les données en paquets (ex: 50 000 nœuds à la fois) pour éviter de saturer le réseau ou le serveur.
* **L'indexation :** On configure la base pour indexer les propriétés clés (comme les identifiants ou les noms), permettant à Python de trouver un nœud instantanément parmi des milliards.
* **La distribution (*Clustering*) :** Le graphe peut être partitionné ou répliqué sur plusieurs serveurs physiques pour absorber la charge de requêtes.


* **Avantages :** Passage à l'échelle virtuellement infini, persistance des données, sécurité, et capacité à faire des requêtes de relations ultra-rapides en production.
* **Limites :** Nécessite une infrastructure (locale ou cloud), une configuration technique plus lourde et l'apprentissage d'un langage de requête de graphe.

### Ressources consultées

- https://www.youtube.com/watch?v=y7sXDpffzQQ (consulté le 09/07/26 à 9h34)
- https://www.microsoft.com/en-us/research/blog/graphrag-improving-global-search-via-dynamic-community-selection/ (consulté le 09/07/26 à 9h45)
- https://www.youtube.com/watch?v=Q5izD6Xlb8o (consulté le 09/07/26 à 9h55)
- https://www.youtube.com/watch?v=YVLwu3jE09c (consulté le 09/07/26 à 10h02)
- https://www.youtube.com/watch?v=u7Z6osuKPqw (consulté le 09/07/26 à 10h10)
- https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/ (consulté le 09/07/26 à 10h13)
- https://arxiv.org/abs/2506.06331 (audit indépendant sur les coûts annoncés)

### Application recommandée: Étude de cas 2 : l'analyste d'investigation

Le GraphRAG serait excellent pour ce cas d'usage :
- **Contraintes clés** : reconstituer des liens entre personnes/événements, presque toutes les questions sont multi-hop.
- **Recommandation à défendre** : GraphRAG — c'est le cas qui justifie le coût d'indexation élevé, précisément parce que le besoin dominant est la traversée de relations.
- **Point fort** : mobiliser directement la limite n°1 du RAG classique de la fiche (questions multi-hop, top-k insuffisant).
- **Nuance à apporter** : Les modèles de langage peuvent "halluciner" des liens ou être biaisés par la façon dont ils ont été entraînés à interpréter les relations. Avant de déployer un système d'investigation, il ne faut pas se fier aux scores de performance fournis par les développeurs de l'outil et faire un test. Il est indispensable de créer un "jeu de tests en conditions réelles" (basé sur des dossiers d'enquêtes passées dont la réponse est connue) pour vérifier si le système réussit réellement à identifier les liens correctement.

---

## B. Retrieval hiérarchique — RAPTOR
*(Recursive Abstractive Processing for Tree-Organized Retrieval)*

---

## C. Hybride & rerankers

---

## D. RAG agentique

---

## E. Faut-il encore du RAG ? Longs contextes, cache et mémoire

