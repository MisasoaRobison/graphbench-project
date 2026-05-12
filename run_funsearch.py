"""CLI entry point for the FunSearch evolution loop.

Usage:
    python run_funsearch.py
    python run_funsearch.py --iterations 60 --sub-size 12 --budget 4.0
    python run_funsearch.py --prefer-llm    # requires ANTHROPIC_API_KEY

The evolved heuristic is written to results/evolved_score.py and can be
plugged into the main search via:
    python main.py --score evolved
"""

import argparse
import os
import sys

from src.funsearch.runner import run_evolution


def _default_benchmark():
    for cand in ("benchmark/benchmark.csv", "benchmark/benchmark.xlsx"):
        if os.path.isfile(cand):
            return cand
    return "benchmark/benchmark.csv"


def main():
    parser = argparse.ArgumentParser(description="FunSearch evolution loop")
    parser.add_argument("--benchmark", default=_default_benchmark())
    parser.add_argument("--iterations", type=int, default=40)
    parser.add_argument("--sub-size", type=int, default=10,
                        help="Number of conjectures used to score each candidate")
    parser.add_argument("--budget", type=float, default=3.0,
                        help="Time budget per conjecture during evaluation")
    parser.add_argument("--islands", type=int, default=4)
    parser.add_argument("--capacity", type=int, default=6)
    parser.add_argument("--migration", type=int, default=10)
    parser.add_argument("--output", default="results/evolved_score.py")
    parser.add_argument("--log", default="results/funsearch_log.txt")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--prefer-llm", action="store_true",
                        help="Try the Anthropic API for variant generation when possible")
    parser.add_argument("--ids", type=str, default=None,
                        help="Comma-separated conjecture IDs to use as the sub-benchmark "
                             "(overrides --sub-size random selection)")
    parser.add_argument("--hard", action="store_true",
                        help="Use the precomputed list of hard conjectures from the "
                             "baseline run as the sub-benchmark")
    args = parser.parse_args()

    ids = None
    if args.ids:
        ids = [int(x) for x in args.ids.split(",")]
    elif args.hard:
        from src.funsearch.evaluator import HARD_IDS
        ids = HARD_IDS[: args.sub_size] if args.sub_size else HARD_IDS

    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    run_evolution(
        benchmark_path=args.benchmark,
        iterations=args.iterations,
        sub_size=args.sub_size,
        time_per_conjecture=args.budget,
        n_islands=args.islands,
        island_capacity=args.capacity,
        migration_period=args.migration,
        output_path=args.output,
        log_path=args.log,
        seed=args.seed,
        prefer_llm=args.prefer_llm,
        ids=ids,
    )


main()
