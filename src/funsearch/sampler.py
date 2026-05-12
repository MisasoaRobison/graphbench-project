"""Sampling / generation of new candidate programs.

Two modes are supported:
 - `offline` (default): symbolic mutation of the parent program directly,
   no external dependency. This is the mode used in the evaluation.
 - `llm`: if the env var ANTHROPIC_API_KEY is set and the `anthropic` package
   is installed, we ask Claude to propose a Python expression and re-parse
   it into a Program. This is the literal FunSearch pipeline (the LLM
   proposes code; we test it).

Both modes return ``Program`` instances; both are validated before insertion.
"""

import os
import random
import re

from .program import Program, ALL_FEATURE_NAMES


# ---------------------------------------------------------------------------
# Offline sampler
# ---------------------------------------------------------------------------

def offline_sample(database, rng=None):
    """Sample a single new program by mutating (or crossing) parents from the
    database. Returns (island_idx, new_program)."""
    rng = rng or random
    idx, parent = database.sample_parent()
    if parent is None:
        return idx, Program(terms=[(1.0, "violation")])
    op = rng.choices(["mutate", "crossover"], weights=[3, 1])[0]
    if op == "mutate":
        return idx, parent.mutate(rng=rng)
    # crossover
    _, other = database.sample_parent()
    if other is None:
        return idx, parent.mutate(rng=rng)
    return idx, Program.crossover(parent, other, rng=rng)


# ---------------------------------------------------------------------------
# LLM sampler (optional)
# ---------------------------------------------------------------------------
# The LLM is asked to return Python source for a new heuristic_score body.
# We parse the body line-by-line looking for "<weight> * <feature>" terms.
# Anything that doesn't fit the grammar is silently ignored, so the LLM
# can return arbitrary code without breaking the loop.

LLM_PROMPT_TEMPLATE = """You are improving a heuristic to refute conjectures
in graph theory. Each candidate program is a linear combination of features
of a graph and its invariants. Given the best candidates so far (with their
fitness scores), propose a new candidate that should do better.

Available features:
{features}

Best programs so far:
{best_programs}

Return ONLY a linear combination of features in this exact format, one
weighted term per line, e.g.:

1.0 * violation
0.05 * leaves
-0.2 * density_balance

Do not include any prose, explanation, code fences or comments.
The first term MUST be "1.0 * violation" or similar with positive weight.
You may include 4 to 10 terms.
"""


def _format_features():
    return ", ".join(ALL_FEATURE_NAMES)


def _format_program(p):
    lines = []
    for w, name in p.terms:
        sign = "+" if w >= 0 else "-"
        lines.append(f"  {sign} {abs(w):.3f} * {name}")
    return "\n".join(lines)


def _parse_program_text(text):
    """Extract '<weight> * <feature>' lines from arbitrary text. Returns a
    Program (possibly empty)."""
    terms = []
    pattern = re.compile(r"([-+]?\s*\d+(?:\.\d+)?)\s*\*\s*([A-Za-z_][A-Za-z0-9_]*)")
    for match in pattern.finditer(text):
        weight_str = match.group(1).replace(" ", "")
        try:
            w = float(weight_str)
        except ValueError:
            continue
        name = match.group(2)
        if name in ALL_FEATURE_NAMES:
            terms.append((w, name))
    if not terms:
        return None
    return Program(terms=terms).cleaned()


def llm_sample(database, model="claude-haiku-4-5"):
    """Try to obtain a new program via the Anthropic API. Returns
    (island_idx, program) or None if the API is unavailable / call fails."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
    except ImportError:
        return None

    # Build prompt
    bests = [e for e in database.best_per_island() if e is not None]
    if not bests:
        return None
    bests.sort(key=lambda e: e.fitness, reverse=True)
    bests = bests[:3]

    best_block = []
    for i, e in enumerate(bests, 1):
        best_block.append(f"Program #{i} (fitness={e.fitness:.2f}, "
                          f"refuted={e.refuted}/{len(database.history) and 'k'}):")
        best_block.append(_format_program(e.program))
    prompt = LLM_PROMPT_TEMPLATE.format(
        features=_format_features(),
        best_programs="\n\n".join(best_block),
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text if msg.content else ""
    except Exception:
        return None

    p = _parse_program_text(text)
    if p is None:
        return None

    # Pick the worst island for LLM proposals (gives them room to grow)
    idx = min(range(len(database.islands)),
              key=lambda i: (database.islands[i].best().fitness
                              if database.islands[i].best() else 0))
    return idx, p


def sample_one(database, prefer_llm=False, rng=None):
    """Return (island_idx, new_program). Tries LLM first if requested."""
    if prefer_llm:
        out = llm_sample(database)
        if out is not None:
            return out
    return offline_sample(database, rng=rng)
