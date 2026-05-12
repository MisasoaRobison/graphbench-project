"""Evaluate a candidate program on a sub-benchmark of conjectures.

A program's fitness mixes:
  - the number of conjectures refuted under a (small) per-conjecture budget,
  - the inverse of the total time spent (faster is better),
  - a bonus for the residual violation when no counter-example is reached.

The evaluator is intentionally fast (3–5 seconds per conjecture, 8–12
conjectures) so the evolution loop can run many iterations within minutes.

Implementation note: we plug the candidate program into the search via the
``score_fn=`` parameter of ``src.search.search``. The search builds an
*extended invariants* dict via ``scoring.build_extended_invariants`` and
passes it to our callable. No monkey-patching is needed.
"""

import random
import time

from src.invariants import clear_cache
from src.parser import load_benchmark
from src.search import search


# ---------------------------------------------------------------------------
# Conjecture selection
# ---------------------------------------------------------------------------

def select_subbenchmark(benchmark_path, k=10, seed=42, ids=None):
    """Pick `k` conjectures for evaluation.

    If ``ids`` is provided (iterable of int), return exactly those conjectures
    in the order they appear in ``ids``. Otherwise stratify across graph
    classes so the fitness signal mixes easy and hard regimes.
    """
    conjectures = load_benchmark(benchmark_path)

    if ids is not None:
        wanted = list(ids)
        by_id = {c.conjecture_id: c for c in conjectures}
        return [by_id[i] for i in wanted if i in by_id][:k] if k else \
               [by_id[i] for i in wanted if i in by_id]

    rng = random.Random(seed)
    buckets = {}
    for c in conjectures:
        key = tuple(sorted(c.graph_classes or []))
        buckets.setdefault(key, []).append(c)

    selected = []
    bucket_keys = list(buckets.keys())
    rng.shuffle(bucket_keys)
    while len(selected) < k and bucket_keys:
        for key in list(bucket_keys):
            pool = buckets[key]
            if not pool:
                bucket_keys.remove(key)
                continue
            c = rng.choice(pool)
            pool.remove(c)
            selected.append(c)
            if len(selected) >= k:
                break

    return selected


# IDs that an earlier version of the baseline struggled with (proximity /
# remoteness / spectral). Used by ``--hard`` of ``run_funsearch.py``.
HARD_IDS = [
    688, 713, 737, 1591, 1729, 1793, 1917, 1919, 2129, 2131,
    3144, 3157, 3191, 3193, 3368, 3384, 3550, 3961, 3979, 4288,
    5421, 5968, 5983, 6011, 6013, 6020, 6466, 6472, 6617, 7565,
]


# ---------------------------------------------------------------------------
# Program scoring
# ---------------------------------------------------------------------------

def evaluate_program(program, conjectures, time_per_conjecture=3.0, seed=0):
    """Plug `program` into the search via ``score_fn=`` and run a short
    search on each conjecture. Returns (fitness, refuted, total_time)."""

    def score_callable(G, invariants, conjecture):
        return program.score(G, invariants, conjecture)

    refuted = 0
    total_time = 0.0
    total_partial_violation = 0.0

    rng_state = random.getstate()
    random.seed(seed)
    try:
        for c in conjectures:
            clear_cache()
            t0 = time.time()
            G, viol, info = search(c, time_limit=time_per_conjecture,
                                   score_fn=score_callable)
            dt = time.time() - t0
            total_time += dt
            if G is not None and viol > 1e-9:
                refuted += 1
            else:
                if viol != float("-inf"):
                    total_partial_violation += max(-5.0, min(5.0, float(viol)))
    finally:
        random.setstate(rng_state)

    speed_bonus = max(0.0, len(conjectures) * time_per_conjecture - total_time) / 10.0
    fitness = 100.0 * refuted + 0.5 * total_partial_violation + speed_bonus
    return fitness, refuted, total_time
