"""FunSearch-style loop that evolves the `heuristic_score` function.

Pipeline (matches the project spec, section 7):
    1. An LLM proposes a candidate scoring function.
    2. The candidate is evaluated on a subset of conjectures.
    3. Best candidates are kept in an archive.
    4. The LLM is given the top-K candidates and asked for a new variant.
    5. Repeat for N iterations.

Run:
    python -m experiments.funsearch.funsearch --iterations 20 \\
        --eval-size 12 --eval-time 5 --provider mock
"""
from __future__ import annotations

import argparse
import json
import os
import random
import time
import traceback
from dataclasses import asdict
from pathlib import Path

from experiments.funsearch.evaluator import evaluate_candidate, EvalResult
from experiments.funsearch.llm_provider import (
    get_provider, extract_score_fn, ProviderError,
)
from experiments.funsearch.prompts import SYSTEM, build_user_prompt
from experiments.funsearch.seed_functions import SEED_FUNCTIONS
from src.parser import load_benchmark


ROOT = Path(__file__).resolve().parent
ARCHIVE_DEFAULT = ROOT / "archive.json"
CANDIDATES_DIR = ROOT / "candidates"


def load_archive(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"candidates": []}


def save_archive(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_candidate_code(cid: str, code: str) -> None:
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    (CANDIDATES_DIR / f"{cid}.py").write_text(code, encoding="utf-8")


_HARD_CONJECTURE_IDS = [
    688, 713, 1591, 1729, 1917, 2129, 2131, 3144, 3157, 3191, 3193, 3368, 3384,
    5381, 5421, 5968, 6011, 6013, 6124, 6466, 6472, 7565, 7566, 7694, 7695, 7811,
    4288,
]


def pick_eval_ids(benchmark_path: str, n: int, seed: int) -> list[int]:
    """Pick a diverse, mostly-hard subset of conjecture IDs for evaluation.

    Mixes a stratified sample (by class and X invariant) with a few of the
    conjectures known to require careful scoring. The harder ones give the
    evaluator enough signal to distinguish candidate functions.
    """
    rng = random.Random(seed)
    conjectures = load_benchmark(benchmark_path)
    by_id = {c.conjecture_id: c for c in conjectures}
    buckets: dict[tuple, list] = {}
    for c in conjectures:
        key = (tuple(sorted(c.graph_classes or [])), c.x_invariant, c.sign)
        buckets.setdefault(key, []).append(c.conjecture_id)
    for ids in buckets.values():
        rng.shuffle(ids)

    picked: list[int] = []
    # Step 1: reserve ~60% of the budget for known-hard cases.
    hard_pool = [i for i in _HARD_CONJECTURE_IDS if i in by_id]
    rng.shuffle(hard_pool)
    target_hard = min(len(hard_pool), max(1, int(0.6 * n)))
    picked.extend(hard_pool[:target_hard])

    # Step 2: fill the rest with stratified samples.
    keys = list(buckets.keys())
    rng.shuffle(keys)
    while len(picked) < n:
        progress = False
        for k in keys:
            while buckets[k]:
                cand = buckets[k].pop()
                if cand not in picked:
                    picked.append(cand)
                    progress = True
                    break
            if len(picked) >= n:
                break
        if not progress:
            break
    return picked[:n]


def record_candidate(archive: dict, cid: str, code: str, result: EvalResult,
                     source: str) -> dict:
    entry = {
        "id": cid,
        "source": source,
        "code": code,
        "score": result.score,
        "refuted": result.refuted,
        "total": result.total,
        "avg_time_refuted": result.avg_time_refuted,
        "errors": result.errors,
        "failed_ids": result.failed_ids,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    archive["candidates"].append(entry)
    save_candidate_code(cid, code)
    return entry


def top_k(archive: dict, k: int) -> list[dict]:
    valid = [c for c in archive["candidates"] if c.get("errors", 0) == 0]
    return sorted(valid, key=lambda c: c["score"])[:k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=10,
                    help="number of LLM proposals to evaluate")
    ap.add_argument("--eval-size", type=int, default=12,
                    help="number of conjectures used to score each candidate")
    ap.add_argument("--eval-time", type=float, default=5.0,
                    help="time budget per conjecture during evaluation (s)")
    ap.add_argument("--top-k", type=int, default=3,
                    help="number of best candidates shown to the LLM")
    ap.add_argument("--provider", default=os.environ.get("FUNSEARCH_PROVIDER", "auto"),
                    choices=["auto", "anthropic", "openai", "mock"])
    ap.add_argument("--benchmark", default="benchmark/benchmark.csv")
    ap.add_argument("--archive", default=str(ARCHIVE_DEFAULT))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--reset", action="store_true",
                    help="ignore existing archive and start from seeds")
    args = ap.parse_args()

    archive_path = Path(args.archive)
    archive = {"candidates": []} if args.reset else load_archive(archive_path)

    eval_ids = pick_eval_ids(args.benchmark, args.eval_size, args.seed)
    print(f"Evaluation subset ({len(eval_ids)} conjectures): {eval_ids}")

    # Bootstrap with seeds if archive is empty.
    if not archive["candidates"]:
        print("Bootstrapping with seed candidates...")
        for name, code in SEED_FUNCTIONS.items():
            t0 = time.time()
            result = evaluate_candidate(code, args.benchmark, eval_ids,
                                        time_per_conjecture=args.eval_time)
            entry = record_candidate(archive, f"seed_{name}", code, result, "seed")
            print(f"  [seed:{name}] score={result.score:.2f} "
                  f"refuted={result.refuted}/{result.total} "
                  f"errors={result.errors} ({time.time()-t0:.1f}s)")
            save_archive(archive_path, archive)

    provider = get_provider(args.provider)
    provider_name = type(provider).__name__
    print(f"Provider: {provider_name}")

    for it in range(args.iterations):
        leaders = top_k(archive, args.top_k)
        if not leaders:
            print("No valid leader candidates, stopping.")
            break
        user_prompt = build_user_prompt(leaders)
        print(f"\n=== iteration {it + 1}/{args.iterations} ===")
        try:
            raw = provider.generate(SYSTEM, user_prompt)
            code = extract_score_fn(raw)
        except Exception as e:
            print(f"  LLM error: {e}")
            traceback.print_exc()
            continue

        cid = f"gen_{int(time.time())}_{it}"
        t0 = time.time()
        result = evaluate_candidate(code, args.benchmark, eval_ids,
                                    time_per_conjecture=args.eval_time)
        entry = record_candidate(archive, cid, code, result, provider_name)
        save_archive(archive_path, archive)
        print(f"  -> score={result.score:.2f} "
              f"refuted={result.refuted}/{result.total} "
              f"errors={result.errors} "
              f"({time.time()-t0:.1f}s)")
        best = top_k(archive, 1)[0]
        print(f"  best so far: {best['id']} score={best['score']:.2f}")

    # Final summary
    print("\n" + "=" * 70)
    leaderboard = top_k(archive, 5)
    print("Top candidates after this run:")
    for c in leaderboard:
        print(f"  {c['id']:<32s} score={c['score']:.2f}  "
              f"refuted={c['refuted']}/{c['total']}")
    if leaderboard:
        winner = leaderboard[0]
        out = ROOT / "best_score_fn.py"
        out.write_text(winner["code"], encoding="utf-8")
        print(f"\nWrote winner ({winner['id']}) to {out}")


if __name__ == "__main__":
    main()
