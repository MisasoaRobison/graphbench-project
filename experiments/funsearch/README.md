# FunSearch loop

This sub-package implements Part 2 of the project spec: a FunSearch-style loop
that automatically evolves the `heuristic_score(G, invariants, conjecture)`
function used by the local search.

## Pipeline

1. An LLM is shown the top-K scoring functions known so far and is asked for a
   new variant.
2. The proposed function is sandboxed (`evaluator.compile_score_fn`) with a
   restricted set of builtins plus `nx`, `np`, `math`.
3. The candidate is plugged into the existing `src.search.search` via the
   `score_fn=` argument and run on a small subset of conjectures with a short
   time budget.
4. The total cost (sum of times for successful refutations + a 2× budget
   penalty for misses) is the score to minimize.
5. Everything is recorded in `archive.json` and `candidates/<id>.py`.

## Run

Offline (no API key, uses a local mutation-based provider):
```
python -m experiments.funsearch.funsearch --provider mock \
    --iterations 10 --eval-size 12 --eval-time 5 --reset
```

With Anthropic Claude (requires `pip install anthropic` and
`ANTHROPIC_API_KEY`):
```
export ANTHROPIC_API_KEY=...
python -m experiments.funsearch.funsearch --provider anthropic \
    --iterations 20 --eval-size 15 --eval-time 5
```

With OpenAI:
```
export OPENAI_API_KEY=...
python -m experiments.funsearch.funsearch --provider openai \
    --iterations 20 --eval-size 15 --eval-time 5
```

## Files

| File | Role |
|---|---|
| `funsearch.py` | main loop, CLI, archive bookkeeping |
| `evaluator.py` | sandbox + benchmark scoring of a candidate |
| `llm_provider.py` | `AnthropicProvider`, `OpenAIProvider`, `MockProvider` |
| `prompts.py` | prompt templates with invariant documentation |
| `seed_functions.py` | initial candidates (baseline, size+density, direction-aware) |
| `archive.json` | record of every candidate + score |
| `candidates/` | one `.py` per candidate (proposed function source) |
| `best_score_fn.py` | the winning function at end of run |

## Tuning

- `--eval-size`: increase for less variance, decrease for faster iteration.
- `--eval-time`: per-conjecture budget in the evaluator (5 s is fine on a hard
  subset; lower gives noisier but faster signals).
- `--top-k`: how many leaders to show the LLM.
- `--seed`: deterministic conjecture subset.
- `--reset`: ignore existing `archive.json` and bootstrap from seeds.

The evaluation subset is biased toward conjectures known to require a careful
score (proximity / remoteness, claw-free spectral cases) so candidates can be
distinguished even with a short budget.
