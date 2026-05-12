"""Main FunSearch evolution loop.

Use programatically:

    from src.funsearch.runner import run_evolution
    run_evolution(benchmark_path="benchmark/benchmark.xlsx",
                  iterations=40,
                  sub_size=10,
                  time_per_conjecture=3.0,
                  output_path="results/evolved_score.py")

or from the command line via `run_funsearch.py`.
"""

import json
import os
import time

from .database import Database, Entry
from .evaluator import evaluate_program, select_subbenchmark
from .program import seed_programs
from .sampler import sample_one


def _log(msg, log_lines):
    print(msg, flush=True)
    log_lines.append(msg)


def run_evolution(benchmark_path,
                  iterations=40,
                  sub_size=10,
                  time_per_conjecture=3.0,
                  n_islands=4,
                  island_capacity=6,
                  migration_period=10,
                  output_path="results/evolved_score.py",
                  log_path="results/funsearch_log.txt",
                  seed=42,
                  prefer_llm=False,
                  ids=None):
    """Run the FunSearch evolution. Returns the best program found.

    The evolved program is also written to ``output_path`` as a self-contained
    Python file matching the form imposee.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    log_lines = []
    t_start = time.time()
    _log("=== FunSearch evolution start ===", log_lines)
    _log(f"benchmark={benchmark_path}  iterations={iterations}  "
         f"sub_size={sub_size}  budget={time_per_conjecture}s/conj  "
         f"islands={n_islands}  prefer_llm={prefer_llm}", log_lines)

    sub = select_subbenchmark(benchmark_path, k=sub_size, seed=seed, ids=ids)
    _log(f"Sub-benchmark: {len(sub)} conjectures, IDs={[c.conjecture_id for c in sub]}",
         log_lines)

    db = Database(n_islands=n_islands, island_capacity=island_capacity, seed=seed)

    # Seed the database
    for i, p in enumerate(seed_programs()):
        f, r, dt = evaluate_program(p, sub, time_per_conjecture=time_per_conjecture,
                                     seed=seed + i)
        db.insert(i % n_islands, Entry(program=p, fitness=f, refuted=r, elapsed=dt))
        _log(f"  seed #{i}: fitness={f:.2f}  refuted={r}/{len(sub)}  time={dt:.1f}s  "
             f"|terms|={len(p.terms)}", log_lines)

    _log("\n--- Evolution loop ---", log_lines)
    for it in range(1, iterations + 1):
        island_idx, candidate = sample_one(db, prefer_llm=prefer_llm)
        # Avoid trivially equivalent duplicates
        sig = candidate.signature()
        already_known = any(
            entry.program.signature() == sig
            for island in db.islands for entry in island.entries
        )
        if already_known:
            _log(f"[{it}] island={island_idx} (duplicate, skipped)", log_lines)
            continue

        f, r, dt = evaluate_program(candidate, sub,
                                    time_per_conjecture=time_per_conjecture,
                                    seed=seed + it)
        entry = Entry(program=candidate, fitness=f, refuted=r, elapsed=dt)

        island_best = db.islands[island_idx].best()
        accepted = island_best is None or f > island_best.fitness - 1.0
        if accepted:
            db.insert(island_idx, entry)
            tag = "[ACCEPTED]" if (island_best is None or f > island_best.fitness) \
                  else "[KEPT]"
        else:
            tag = "[rejected]"

        _log(f"[{it}/{iterations}] island={island_idx} {tag} "
             f"fitness={f:.2f}  refuted={r}/{len(sub)}  time={dt:.1f}s  "
             f"|terms|={len(candidate.terms)}", log_lines)

        if it % migration_period == 0:
            db.migrate()
            _log("  -> migration: worst island re-seeded with best program",
                 log_lines)
            _log(db.summary(), log_lines)

    elapsed = time.time() - t_start
    _log(f"\n=== Evolution done in {elapsed:.1f}s ===", log_lines)
    _log(db.summary(), log_lines)

    best = db.best()
    if best is None:
        _log("No best program. Aborting export.", log_lines)
        return None

    _log(f"\nBest program: fitness={best.fitness:.2f}  refuted={best.refuted}/{len(sub)}  "
         f"time={best.elapsed:.1f}s", log_lines)
    _log("Terms:", log_lines)
    for w, name in best.program.terms:
        sign = "+" if w >= 0 else "-"
        _log(f"  {sign} {abs(w):.4f} * {name}", log_lines)

    # Persist the evolved program as Python source
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(best.program.to_python())
    _log(f"\nWrote evolved score to {output_path}", log_lines)

    # Persist log and dict-format
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    with open(output_path + ".json", "w", encoding="utf-8") as f:
        json.dump({
            "best": best.program.to_dict(),
            "fitness": best.fitness,
            "refuted": best.refuted,
            "elapsed": best.elapsed,
            "iterations": iterations,
            "sub_size": sub_size,
            "time_per_conjecture": time_per_conjecture,
        }, f, indent=2)

    return best.program
