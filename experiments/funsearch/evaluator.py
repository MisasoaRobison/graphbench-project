"""Sandboxed evaluation of a candidate `heuristic_score` function.

Each candidate is compiled in a restricted namespace, then plugged into the
existing local search and run on a small subset of conjectures with a short
time budget. The total cost (sum of times for found counter-examples plus a
2x-budget penalty for misses) is the metric to minimize.
"""
from __future__ import annotations

import math
import random
import time
import traceback
from dataclasses import dataclass, field

import networkx as nx
import numpy as np

from src.parser import load_benchmark
from src.search import search

_SAFE_BUILTINS = {
    "abs": abs, "min": min, "max": max, "sum": sum, "len": len,
    "range": range, "list": list, "dict": dict, "set": set, "tuple": tuple,
    "sorted": sorted, "reversed": reversed, "enumerate": enumerate, "zip": zip,
    "round": round, "int": int, "float": float, "bool": bool, "str": str,
    "isinstance": isinstance, "all": all, "any": any, "map": map, "filter": filter,
    "True": True, "False": False, "None": None,
}


def compile_score_fn(code: str):
    """Exec `code` in a restricted namespace and return its heuristic_score."""
    ns = {
        "__builtins__": _SAFE_BUILTINS,
        "math": math, "nx": nx, "networkx": nx, "np": np, "numpy": np,
    }
    exec(code, ns)
    fn = ns.get("heuristic_score")
    if fn is None or not callable(fn):
        raise ValueError("Candidate code does not define heuristic_score()")
    return fn


@dataclass
class EvalResult:
    score: float
    refuted: int
    total: int
    avg_time_refuted: float
    errors: int
    traceback: str = ""
    failed_ids: list = field(default_factory=list)


def evaluate_candidate(code: str, benchmark_path: str, eval_ids: list[int],
                       time_per_conjecture: float = 5.0,
                       miss_penalty_factor: float = 2.0) -> EvalResult:
    """Score one candidate function.

    Args:
        code: source code that defines `heuristic_score`.
        benchmark_path: path to the benchmark CSV/XLSX.
        eval_ids: list of conjecture IDs to use for evaluation.
        time_per_conjecture: seconds budget for each conjecture.
        miss_penalty_factor: multiplier for the per-conjecture budget that is
            counted as cost when no counter-example is found.

    Returns:
        EvalResult. Lower `score` is better.
    """
    try:
        fn = compile_score_fn(code)
    except Exception:
        return EvalResult(
            score=miss_penalty_factor * time_per_conjecture * len(eval_ids) * 2,
            refuted=0, total=len(eval_ids), avg_time_refuted=0.0, errors=1,
            traceback=traceback.format_exc(),
        )

    conjectures = load_benchmark(benchmark_path)
    by_id = {c.conjecture_id: c for c in conjectures}
    subset = [by_id[i] for i in eval_ids if i in by_id]

    refuted = 0
    cost = 0.0
    errors = 0
    elapsed_refuted = []
    failed = []
    for c in subset:
        try:
            t0 = time.time()
            G, viol, info = search(c, time_limit=time_per_conjecture, score_fn=fn)
            elapsed = time.time() - t0
            if G is not None and viol > 1e-9:
                refuted += 1
                cost += elapsed
                elapsed_refuted.append(elapsed)
            else:
                cost += miss_penalty_factor * time_per_conjecture
                failed.append(c.conjecture_id)
        except Exception:
            errors += 1
            cost += miss_penalty_factor * time_per_conjecture
            failed.append(c.conjecture_id)

    avg_t = sum(elapsed_refuted) / len(elapsed_refuted) if elapsed_refuted else 0.0
    return EvalResult(
        score=cost, refuted=refuted, total=len(subset),
        avg_time_refuted=avg_t, errors=errors, failed_ids=failed,
    )
