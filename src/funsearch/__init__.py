"""FunSearch-inspired automated search for better heuristic_score functions.

The architecture follows the FunSearch idea (DeepMind, 2023):
  1. A *database* of candidate scoring programs, organised as islands.
  2. A *sampler* picks parents from the database.
  3. A *generator* proposes variants (locally via symbolic mutation, or
     optionally via an LLM call if an API key is available).
  4. An *evaluator* runs each variant on a sub-benchmark and returns its
     fitness (refuted count + speed).
  5. Variants beating their island's worst are inserted; periodic migration
     mixes the islands.

The evolved best program is exported as a self-contained Python file
(``results/evolved_score.py``) matching the *form imposed by the project
statement*: a ``heuristic_score(G, invariants, conjecture)`` function whose
body builds a single numeric score.
"""
