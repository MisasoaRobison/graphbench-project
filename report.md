# GraphBench Challenge — Rapport

**Master 1 MIAGE — Refutation automatique de conjectures en theorie des graphes**

| | |
|---|---|
| Etudiants | Robison — Diallo |
| Formation | Master 1 MIAGE |
| Date | Mai 2026 |
| Depot GitHub | https://github.com/Jalloh-hub/graphbench-project |
| Conjectures refutees | **100 / 100** |
| Score final | **52,17 s** (cout total, somme des t_i) |

---

## 1. Introduction et objectif

Une conjecture en theorie des graphes affirme qu'une propriete A(G) ≤ f(B(G))
(ou ≥) est vraie pour toute classe C. Le benchmark fourni contient 100
conjectures impliquant 21 invariants structurels et spectraux et 5 classes
de graphes (`connected`, `tree`, `bipartite`, `planar`, `claw_free`). Notre
objectif : refuter automatiquement le plus de conjectures possible le plus
vite possible, avec un budget de 60 s par conjecture et un cout de 120 s
en cas d'echec.

Le projet est decoupe en deux parties. La **Partie 1** construit une
heuristique metaheuristique generique. La **Partie 2** implemente une
architecture inspiree de FunSearch (Romera-Paredes et al., Nature 2024)
permettant d'evoluer automatiquement la fonction de score.

L'ensemble du code est dans le depot `graphbench-project/` — voir
`experiments/reproduce.md` pour rejouer chaque experience.

## 2. Heuristique simple (Partie 1)

### 2.1 Architecture

```
benchmark.csv  -->  parser.py  -->  Conjecture
                                        |
                                        v
                                    search.py
                              /        |        \
                       templates    mutations   repair_class
                          |            |            |
                       graph6 <---  invariants  <-- scoring
```

La recherche se deroule en **deux phases**.

**Phase 1 — templates.** Une bibliotheque etendue de graphes nommes
(chemins, cycles, etoiles subdivisees, generalised Petersen, coronas,
friendship, gluings de K_n, line graphs, books, lollipops, barbells,
hypercubes Q_3-Q_6, brooms, double brooms…) est filtree par classe puis
essayee en premier. Beaucoup de contre-exemples classiques sont des
instances de ces familles : par exemple, l'etoile K_{1,5} dont chaque
arete est subdivisee deux fois refute la conjecture 1587 (matching
number ≥ f(total domination number)) en 0,06 s.

La fonction `extreme_seeds(graph_classes, x_inv, y_inv)`
([src/graph_generation.py](src/graph_generation.py)) selectionne en plus
des graphes specifiquement adaptes au couple d'invariants en jeu :
brooms pour les conjectures `proximity` / `remoteness` croisees avec
`vertex_cover` / `matching`, grands K_n pour les conjectures spectrales,
hypercubes pour la connectivite algebrique, etc. **Aucun de ces
templates n'est un contre-exemple cable en dur** : ce sont des familles
parametrees connues de la litterature pour produire des contre-exemples
sur ces invariants.

**Phase 2 — recherche locale a population.** Une population de 8 a 12
graphes est maintenue, on selectionne un parent par tournoi de taille 3,
on applique une mutation aleatoire, on repare la classe, on score, on
remplace le pire si l'enfant est meilleur. En cas de stagnation, on
injecte un nouveau graphe aleatoire plus grand pour relancer
l'exploration.

### 2.2 Score direction-aware

`src/scoring.py` definit un score qui prend en compte la **direction**
dans laquelle on doit pousser le graphe pour violer la conjecture :

- `conjecture_directions(conjecture, x)` retourne `(dir_x, dir_y) ∈ {-1, 0, +1}`
  selon le signe de la conjecture (`<=` vs `>=`) et la pente locale du
  polynome `f`.
- Des dictionnaires `DENSITY_BIAS` et `SIZE_BIAS` associent chaque
  invariant a son sens de variation typique (la `density` croit avec les
  aretes, le `diameter` decroit, etc.).
- Le score combine alors : `violation + push_densite + push_taille
  + bonus_specifiques_au_couple_d_invariants`.

Cela transforme la recherche locale en une remontee de gradient guidee
par la conjecture, plutot qu'une exploration aveugle.

### 2.3 Composants generiques

- **Invariants** (`src/invariants.py`) : les 21 invariants du benchmark
  sont supportes. Les NP-difficiles (domination, total domination,
  independent domination, independence number, vertex cover) sont
  exacts par backtracking bitmask jusqu'a n ≤ 28, gloutons au-dela. Les
  invariants spectraux passent par `scipy.sparse.linalg`.
  **Tous les resultats sont caches par chaine graph6**.
- **Mutations** (`src/mutations.py`) : 13 operateurs, adaptes a la
  classe (les arbres n'autorisent que add_leaf, subdivide_edge,
  remove_leaf, contract_edge, add_path).
- **Reparation** (`src/repair.py`) : reconnect, spanning-tree, removal
  d'aretes des cycles impairs (biparti), removal d'aretes jusqu'a
  planarite, ou addition d'aretes entre voisins pour casser une griffe
  induite.

Aucun composant ne lit `conjecture.conjecture_id` autrement que pour
l'affichage : **aucun contre-exemple n'est cable en dur**.

## 3. Architecture FunSearch (Partie 2)

Nous fournissons **deux implementations independantes** de l'architecture
FunSearch, qui partagent le meme principe mais avec des choix techniques
differents. Toutes deux respectent la forme imposee par le §7.2 du sujet.

### 3.1 Pipeline LLM-first — `experiments/funsearch/`

Boucle FunSearch fidele au papier : on demande au LLM une nouvelle
fonction `heuristic_score`, on la compile dans un sandbox, on l'evalue,
on garde les meilleures.

- `llm_provider.py` : abstraction `mock` (mutation locale, sans cle),
  `anthropic` (Claude), `openai` (GPT). Choix au runtime.
- `prompts.py` : prompt systeme + template utilisateur incluant les top-K
  candidats avec leur fitness.
- `evaluator.py` : sandbox restreint, `score_fn=` injecte dans
  `src.search.search`, fitness = cout total (refutations + penalite).
- `funsearch.py` : boucle principale, archive JSON, candidates persistes
  dans `experiments/funsearch/candidates/<id>.py`.

### 3.2 Pipeline island model — `src/funsearch/`

Variante symbolique pure (zero dependance externe). Un *programme* est
une combinaison lineaire ponderee de 18 *features* calcules sur G + les
invariants (`violation`, `n`, `m`, `density`, `density_balance`,
`leaves`, `Delta`, `xy_gap`, etc.). Le terme `violation` est protege.

- `program.py` : representation + export Python conforme au §7.2.
- `database.py` : modele en **4 ilots** de capacite 6, deduplication par
  signature, migration periodique (le pire ilot est re-ensemence avec
  le meilleur programme global).
- `evaluator.py` : passe le programme via `score_fn=` a la recherche, et
  ne touche jamais a `src/scoring.py`.
- `sampler.py` : mutation symbolique offline (perturb_weight, add_term,
  remove_term, swap_feature, flip_sign, rescale, crossover) + hook LLM
  optionnel (`--prefer-llm` avec `ANTHROPIC_API_KEY`).
- `runner.py` : seed -> sample -> mutate -> evaluate -> insert -> migrate
  -> export dans `results/evolved_score.py`.

L'export `Program.to_python()` produit un fichier Python avec la
signature et la docstring exactement comme demande par le sujet :

```python
def heuristic_score(G, invariants, conjecture):
    """G : graphe NetworkX, invariants : dict, conjecture : objet
       retourne un score numerique a maximiser"""
    violation = conjecture.violation(x, y)
    if violation > 1e-9:
        return 1e6 + violation
    ...
    return (
        + 1.0000 * violation
        + 0.0010 * n
    )
```

Le score evolue se branche dans le pipeline principal via
`python main.py --score evolved`.

## 4. Resultats experimentaux

### 4.1 Configuration

- 100 conjectures du benchmark fourni
- Budget : 60 s par conjecture (cout 120 s si echec)
- Materiel : Windows 11, Python 3.13, 16 cores (un seul thread utilise
  par recherche), 16 Go RAM

### 4.2 Tableau de resultats

| Configuration | Refutees | Cout total | t_moyen (refutees) |
|---|---:|---:|---:|
| Heuristique simple (Partie 1, score direction-aware) | **100** / 100 | **52,17 s** | **0,52 s** |

Aucune conjecture n'a echoue. Le cout total est tres en-dessous du
seuil critique (12 000 s = 100 × 120 s = aucune refutation).

### 4.3 Comportement par phase

Sur les 100 refutations :
- **Phase template** : majorite des conjectures, refutees en <0,1 s
  (graphes nommes essayes en debut).
- **Phase init** : conjectures dont le contre-exemple est decouvert par
  l'un des 6 graphes aleatoires initiaux.
- **Phase search** : conjectures necessitant la recherche locale a
  population (1-10 s typiquement, e.g. ID 980, 981 avec n>100 sommets).

### 4.4 Echecs et succes typiques

- **Succes immediat** : conjectures dont le contre-exemple est une
  famille connue ; les templates `extreme_seeds` couvrent K_{1,5}
  double-subdivise pour 1587, K_n colles pour les conjectures
  triangle/degre, brooms pour proximity-vc.
- **Succes par recherche locale** : conjectures `clique_number ≤ f(avg_degree)`
  necessitant de grands graphes peu denses (n≈140) ; le score
  direction-aware pousse vers la sparsity car DENSITY_BIAS[avg_degree]=+1
  et la conjecture est avec sign=`<=`.
- **Aucun echec** sur ce benchmark — voir §5.4 pour la discussion.

## 5. Discussion scientifique

### 5.1 Quelles conjectures sont faciles a refuter ?

Toutes les conjectures du benchmark se sont averees refutables dans le
budget de 60 s. Les conjectures **combinatoires** (domination, matching,
clique, degre) sont triviales pour les templates ; les conjectures
**spectrales** (`largest_eigenvalue`, `second_smallest_laplace_eigenvalue`)
necessitent simplement les bonnes familles (K_n, K_{n,n}, cycles
longs) ; les conjectures de **distance** (`proximity`, `remoteness`)
demandent les familles broom / double broom.

### 5.2 Quels invariants sont difficiles a manipuler ?

Les invariants `proximity` et `remoteness` ont un signal de violation
faible sous une mutation locale (ajouter/retirer une arete change peu
la moyenne des distances). C'est pourquoi nous comptons surtout sur les
*templates* pour ces conjectures. Sans la fonction `extreme_seeds`, ces
conjectures sont les plus difficiles a refuter par recherche locale
pure.

### 5.3 Quelles mutations sont efficaces ?

D'apres les logs, les mutations les plus productives sont :
- `subdivide_edge` et `add_leaf` : critiques pour les conjectures de
  domination et matching (transforment un graphe en spider).
- `attach_clique` et `attach_triangle` : critiques pour clique-vs-degre.
- `twin_vertex` : utile pour les conjectures spectrales (ajoute un
  vecteur propre repete).
- `two_swap` : preserve la sequence de degres, utile pour les
  recherches d-regulieres.

### 5.4 L'architecture FunSearch ameliore-t-elle l'heuristique initiale ?

L'heuristique statique direction-aware refute deja 100/100 conjectures
en 52 s, ce qui plafonne l'espace d'amelioration. Sur les *sous-benchmarks
medium* (conjectures refutees par recherche locale en 1-5 s), nous
mesurons que :

- l'island model offline converge vers `0,001 * n + 1,756 * violation`
  (7/8 vs 6/8 pour la seed pure violation),
- le pipeline LLM-first produit des variantes plus expressives qui
  egalent ou battent legerement l'heuristique de reference selon la
  graine.

L'architecture FunSearch ne change donc pas le **nombre** de
refutations, mais elle permet de **valider experimentalement** que
l'heuristique manuelle direction-aware est competitive : aucune
fonction evoluee ne la depasse de plus de quelques pourcents sur les
sous-benchmarks que nous avons testes.

### 5.5 L'IA a-t-elle produit des idees utiles ?

Nous avons utilise Claude (Opus 4) comme assistant de programmation
pour : (1) lister les familles de graphes pertinentes pour
`extreme_seeds`, (2) coder les algorithmes exacts de domination /
independent domination par bitmask, (3) concevoir l'architecture
FunSearch et son schema d'evaluation. Le hook LLM (`--prefer-llm` /
`--provider anthropic`) permet aussi d'utiliser le LLM au runtime
comme generateur de variantes.

### 5.6 Robustesse sur d'autres benchmarks

Notre architecture est **generique** : tous les composants sont
parametres par classe et par nom d'invariant, jamais par ID de
conjecture (`grep -r "conjecture_id" src/` ne retourne que des
references d'affichage). Sur un benchmark inconnu :

- `extreme_seeds` couvrira la plupart des conjectures faisant
  intervenir les invariants du benchmark fourni (proximity, remoteness,
  spectraux, domination, matching, clique, degre, ...).
- Pour des invariants nouveaux, il suffit d'ajouter une regle dans
  `extreme_seeds` (queleques lignes de code) et l'invariant lui-meme
  dans `src/invariants.py` s'il n'est pas deja la.
- FunSearch peut etre re-execute pour adapter le score :
  `python run_funsearch.py --ids <liste>` (~10 min).

La limitation principale est la taille des graphes : les algorithmes
exacts NP-difficiles plafonnent a n ≤ 28 ; au-dela nous tombons sur des
approximations gloutonnes qui peuvent manquer de precision pour des
conjectures tres serrees. En pratique, le benchmark fourni est entiere-
ment couvert.

---

**Repository** : voir page de garde.
**Pour rejouer chaque experience** : `experiments/reproduce.md`.
