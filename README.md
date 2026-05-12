# GraphBench Challenge

Réfutation automatique de conjectures en théorie des graphes par
métaheuristique locale et architecture de type FunSearch.

| Métrique | Valeur |
|---|---|
| Conjectures réfutées | **100 / 100** |
| Score total (somme des coûts) | **52,17 s** |
| Budget par conjecture | 60 s |
| Temps moyen / réfutation | 0,52 s |

## Aperçu

Pour chaque conjecture `Y sign poly(X)` (avec `sign ∈ {<=, >=}`), le programme
cherche un graphe `G` qui la viole. Pipeline :

1. **Génération** — bibliothèque de graphes paramétriques (chemins, cycles,
   complets, Petersen, hypercubes, Paley, brooms, joins claw-free, …).
2. **Évaluation** — calcul des invariants nécessaires et de la violation
   `viol(G) = poly(X(G)) − Y(G)` (signe selon le `sign`).
3. **Score heuristique** — gradient direction-aware sur la densité et la
   taille, biaisé selon la direction où chaque invariant doit bouger pour
   violer (cf. [src/scoring.py](src/scoring.py)).
4. **Recherche évolutive** — sélection par tournoi, 13 mutations locales,
   redémarrages aléatoires en cas de stagnation.
5. **Réparation** — un graphe muté est ramené dans sa classe imposée (tree,
   bipartite, planar, claw-free, connected) avant scoring.

## Arborescence

```
graphbench-project/
├── src/
│   ├── conjecture.py        # dataclass + violation(x,y) / violation(dict)
│   ├── parser.py            # benchmark.csv / .xlsx → liste de Conjecture
│   ├── graph6.py            # encodage/decodage graph6
│   ├── invariants.py        # tous les invariants (cache via graph6)
│   ├── graph_generation.py  # templates + extreme_seeds par invariant
│   ├── mutations.py         # 13 mutations locales
│   ├── repair.py            # reconnect / re-arbre / re-bipartite / re-planar / dégriffer
│   ├── scoring.py           # heuristique direction-aware + extended invariants
│   └── search.py            # boucle de recherche (accepte score_fn injectable)
├── experiments/
│   └── funsearch/           # Partie 2 : pipeline FunSearch
│       ├── funsearch.py     # boucle principale (CLI)
│       ├── evaluator.py     # sandbox + scoring d'un candidat
│       ├── llm_provider.py  # Anthropic / OpenAI / Mock (offline)
│       ├── prompts.py       # template + doc des invariants
│       ├── seed_functions.py
│       └── README.md
├── benchmark/
│   └── benchmark.csv        # 100 conjectures, séparateur `;`, cp1252
├── results/
│   ├── results_counterexamples.csv   # sortie officielle 100/100
│   └── final3.log           # log complet du dernier run
├── main.py                  # CLI : lance la recherche sur le benchmark
├── requirements.txt
└── README.md
```

## Installation

```
python -m venv .venv
.venv\Scripts\activate                  # Windows
# source .venv/bin/activate              # Linux/macOS
pip install -r requirements.txt
```

Python ≥ 3.10 (testé sur 3.13).

## Lancement de la recherche

Tout le benchmark, 60 s par conjecture :
```
python main.py --benchmark benchmark/benchmark.csv --time 60 \
    --output results/results_counterexamples.csv
```

Options utiles :
- `--limit N` : ne traite que les `N` premières conjectures.
- `--ids "688,713"` : restreint à une liste d'IDs.
- `--output ...` : `.csv` (séparateur `;`) ou `.xlsx`.
- `--score evolved` ou `--score path/to/custom.py` : remplace
  `src/scoring.heuristic_score` par une fonction FunSearch-évoluée
  (cf. Partie 2 ci-dessous).

Sortie : un CSV (ou xlsx) avec, par conjecture, `id`, `found`, `x_value`,
`y_value`, `violation`, `nodes`, `edges`, `graph6`, `phase`, `evaluations`,
`elapsed_s`.

## Pipeline FunSearch (Partie 2)

Le dépôt fournit **deux implémentations indépendantes** de l'architecture
FunSearch. Elles partagent le même principe (seed → sample → évaluer →
garder top-K) mais explorent des choix techniques différents.

### a) `experiments/funsearch/` — LLM-first

Boucle qui demande à un LLM de proposer des `heuristic_score` et conserve les
meilleurs sur un sous-ensemble d'évaluation :

```
# offline (mock provider)
python -m experiments.funsearch.funsearch --provider mock \
    --iterations 10 --eval-size 12 --eval-time 5 --reset

# avec Claude (anthropic)
$env:ANTHROPIC_API_KEY = "..."
pip install anthropic
python -m experiments.funsearch.funsearch --provider anthropic --iterations 20

# avec GPT
$env:OPENAI_API_KEY = "..."
pip install openai
python -m experiments.funsearch.funsearch --provider openai --iterations 20
```

Détails dans [experiments/funsearch/README.md](experiments/funsearch/README.md).

### b) `src/funsearch/` — Island model (symbolique pur)

Boucle évolutive sans dépendance LLM. Un *programme* est une combinaison
linéaire pondérée de 18 *features* calculés sur G et ses invariants ;
4 îlots, migration périodique, mutation symbolique + crossover.

```
python run_funsearch.py                              # 40 iters, ~12 min
python run_funsearch.py --hard                       # cible les conjectures dures
python run_funsearch.py --ids 1566,1708,6574,6903    # IDs précis
python run_funsearch.py --prefer-llm                 # ANTHROPIC_API_KEY requis
```

Sortie : `results/evolved_score.py` (conforme à la forme imposée §7.2),
réutilisable via `python main.py --score evolved`.

## Outils complémentaires

```
python validate.py [results.csv|.xlsx]           # validateur léger
python experiments/compare.py FILE_A FILE_B       # comparaison baseline / évolué
python build_report.py                            # report.md → report.html
```

Le pas-à-pas complet pour rejouer chaque expérience est dans
[experiments/reproduce.md](experiments/reproduce.md).

## Conventions importantes

- `proximity = (n−1) / max_v σ(v)` (min closeness centrality) — convention
  utilisée par le benchmark, **différente** de la définition Aouchiche–Hansen.
- `remoteness = (n−1) / min_v σ(v)` (max closeness centrality).
- `largest_eigenvalue`, `largest_distance_eigenvalue`,
  `second_smallest_laplace_eigenvalue` requièrent `scipy` (sinon NetworkX
  3.6 lève une exception silencieusement attrapée → valeur 0).

## Choix techniques discutés dans le rapport

- Score direction-aware basé sur le signe `<=` / `>=` et la pente de
  `poly` au point courant.
- `extreme_seeds(x_inv, y_inv)` qui pré-construit des graphes paramétriques
  spécialement utiles selon les invariants en jeu (paths longs et brooms pour
  prox/rem vs vc/matching, K_n + pendant claw-free pour λ₁/λ₂, K₁ ∨ (Kₐ⊔K_b)
  pour rem en claw-free, …).
- Mutations adaptées à la classe (arbres : add_leaf / subdivide / contract).

## Validation indépendante des contre-exemples

Pour vérifier que chaque ligne de `results/results_counterexamples.csv`
respecte les quatre règles du §11 (classe correcte, invariants justes,
inégalité strictement violée, format graph6) :
```
python -m experiments.validate_results \
    --results results/results_counterexamples.csv \
    --benchmark benchmark/benchmark.csv
```
Le script décode chaque `graph6`, recalcule les invariants à partir du
graphe décodé, et compare. Sortie attendue sur les résultats fournis :
```
validated    : 100 / 100
failures     : 0
```

## Reproductibilité

Le benchmark complet a été exécuté avec :
```
python main.py --benchmark benchmark/benchmark.csv --time 60 \
    --output results/results_counterexamples.csv
```
Résultat : `Refuted 100/100 conjectures. Total cost: 52.17`.
