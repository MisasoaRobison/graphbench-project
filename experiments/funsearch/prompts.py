"""Prompt templates used to ask an LLM for a new candidate scoring function."""

INVARIANTS_DOC = """\
The `invariants` argument is a dict. Keys you can expect (most queried via
`.get(key, 0)`):

    n, m, density,
    minimum_degree (or "delta"),  maximum_degree (or "Delta"),
    average_degree (or "avg"),
    diameter (or "diam"),  radius (or "rad"),
    triangle_number (or "triangles"),  clique_number (or "omega"),
    domination_number (or "gamma"),  total_domination_number,
    independence_number (or "alpha"),  vertex_cover_number (or "tau"),
    matching_number (or "mu"),  independent_domination_number,
    randic_index,  harmonic_index,
    first_zagreb_index,  second_zagreb_index,
    proximity,  remoteness          # both in (0, 1], min/max closeness
    largest_eigenvalue,  largest_distance_eigenvalue,
    second_smallest_laplace_eigenvalue,

Plus the X and Y invariants of the current conjecture.

The `conjecture` argument exposes:
    conjecture.violation(invariants)  -> float, > 0 means the graph violates it
    conjecture.x_invariant            -> name of X
    conjecture.y_invariant            -> name of Y
    conjecture.sign                   -> "<=" or ">="
    conjecture.polynomial(x)          -> value of poly used in the inequality

`G` is a networkx graph; libraries available: `nx`, `np`, `math`.
"""


SYSTEM = """\
You are designing a Python scoring function used by a local-search metaheuristic
that searches for counter-examples to conjectures in graph theory. The search
mutates a graph and keeps the ones with the highest score, so the score should
guide the search even on graphs that are not yet violating the conjecture.
"""


USER_TEMPLATE = """\
Goal: produce ONE new `heuristic_score(G, invariants, conjecture)` function.

It must return a single float; higher = more promising. When the conjecture
is violated (violation > 0), the function should return a very large value so
the search stops, and otherwise it should provide a smooth gradient toward
graphs that are likely to violate the conjecture (e.g. add bonuses that depend
on the direction we want each invariant to move).

{invariants_doc}

CONSTRAINTS:
- Only use `math`, `nx`, `np`, the arguments, and basic builtins.
- Do NOT do file/network I/O.
- The function must be deterministic given (G, invariants, conjecture).
- It must run in well under 1 ms on a 30-vertex graph.

Here are the best scoring functions found so far (lower benchmark score = better):

{examples}

Now write ONE improved variant. Reply with a SINGLE python code block (no
explanation outside the block):

```python
def heuristic_score(G, invariants, conjecture):
    ...
```
"""


def render_examples(top_candidates):
    blocks = []
    for c in top_candidates:
        blocks.append(
            f"# candidate {c['id']!r} -- benchmark score={c['score']:.2f}, "
            f"refuted={c['refuted']}/{c['total']}\n"
            f"```python\n{c['code'].strip()}\n```"
        )
    return "\n\n".join(blocks)


def build_user_prompt(top_candidates):
    return USER_TEMPLATE.format(
        invariants_doc=INVARIANTS_DOC,
        examples=render_examples(top_candidates),
    )
