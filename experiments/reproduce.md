# Comment refaire les experiences

Toutes les commandes sont a lancer depuis la racine du projet
(`graphbench-project/`).

## 0. Pre-requis

```bash
pip install -r requirements.txt
```

Verifier :

```bash
python -c "import networkx, numpy, pandas, scipy, sympy, openpyxl; print('ok')"
```

## 1. Heuristique simple (Partie 1)

### Lancer le benchmark complet

```bash
python main.py --benchmark benchmark/benchmark.csv --time 60 \
    --output results/results_counterexamples.csv
```

Sortie attendue (en environ 1 minute, grace aux templates) :
- `results/results_counterexamples.csv`
- ecran : `Refuted 100/100 conjectures. Total cost: 52.17`

### Variantes

```bash
python main.py --limit 10                       # 10 premieres conjectures
python main.py --ids 886,1191,1587 --time 5     # IDs cibles, budget court
python main.py --time 120                       # budget temps personnalise
python main.py --output results/baseline.xlsx   # sortie Excel
```

## 2. Validation des contre-exemples (regle §11 du sujet)

Deux validateurs sont disponibles, equivalents en rigueur :

```bash
# Validateur officiel : decode chaque graph6, recalcule les invariants,
# verifie classe + violation stricte.
python -m experiments.validate_results \
    --results results/results_counterexamples.csv \
    --benchmark benchmark/benchmark.csv

# Validateur leger (XLSX-friendly), memes criteres :
python validate.py results/results_counterexamples.csv
```

Sortie attendue : `validated : 100 / 100, failures : 0`.

## 3. FunSearch (Partie 2) — deux implementations independantes

Le depot contient **deux variantes** de l'architecture FunSearch ;
elles partagent le meme principe (seed -> sample -> evaluate -> keep top-K).

### 3a. Pipeline `experiments/funsearch/` (LLM-first)

Boucle qui demande au LLM (mock par defaut, Anthropic ou OpenAI au choix)
de proposer des `heuristic_score` et conserve les meilleurs :

```bash
# offline (mock provider, mutation locale)
python -m experiments.funsearch.funsearch --provider mock \
    --iterations 10 --eval-size 12 --eval-time 5 --reset

# avec Anthropic Claude
$env:ANTHROPIC_API_KEY = "..."
pip install anthropic
python -m experiments.funsearch.funsearch --provider anthropic --iterations 20

# avec OpenAI GPT
$env:OPENAI_API_KEY = "..."
pip install openai
python -m experiments.funsearch.funsearch --provider openai --iterations 20
```

Detail dans [experiments/funsearch/README.md](funsearch/README.md).

### 3b. Pipeline `src/funsearch/` (island model)

Boucle evolutive symbolique sans dependance LLM. Programme = combinaison
ponderee de 18 features ; modele en 4 ilots avec migration periodique :

```bash
python run_funsearch.py                              # 40 iters, ~12 min
python run_funsearch.py --hard                       # cible les conjectures dures
python run_funsearch.py --ids 1566,1708,6574,6903    # IDs precis
python run_funsearch.py --prefer-llm                 # ANTHROPIC_API_KEY requis
```

Sorties :
- `results/evolved_score.py` — fonction `heuristic_score` evoluee, dans la
  *forme imposee* par l'enonce (§7.2)
- `results/evolved_score.py.json` — dictionnaire (poids + features)
- `results/funsearch_log.txt` — journal d'evolution

### Utiliser un score evolue dans le benchmark

```bash
python main.py --score evolved             # utilise results/evolved_score.py
python main.py --score path/to/custom.py   # autre fichier
```

## 4. Comparaison baseline vs evolue

```bash
python experiments/compare.py \
    results/results_counterexamples.csv \
    results/evolved_full.csv
```

Affiche nombre de refutations, cout total, et deltas par ID.

## 5. Reproduire la table de resultats du rapport

```bash
# (1) Baseline (heuristique direction-aware, Partie 1)
python main.py --time 60 --output results/baseline.csv

# (2) FunSearch (island model) sur conjectures medium
python run_funsearch.py --ids 1566,1708,6574,6903,5381,4288,3961,5421 \
    --iterations 25 --budget 3.0 --output results/evolved_score.py

# (3) Benchmark complet avec le score evolue
python main.py --time 60 --score evolved --output results/evolved_full.csv

# (4) Validation
python -m experiments.validate_results --results results/baseline.csv
python -m experiments.validate_results --results results/evolved_full.csv

# (5) Comparaison
python experiments/compare.py results/baseline.csv results/evolved_full.csv
```

## 6. Sanity check rapide (~5 min)

```bash
python main.py --limit 10 --time 10 --output results/quick_baseline.csv
python run_funsearch.py --sub-size 6 --iterations 12 --budget 2.0
python main.py --limit 10 --time 10 --score evolved --output results/quick_evolved.csv
python validate.py results/quick_evolved.csv
```
