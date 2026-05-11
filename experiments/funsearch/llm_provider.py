"""LLM providers for the FunSearch loop.

Three back-ends are supported:
- `anthropic`: uses the official Anthropic SDK (needs ANTHROPIC_API_KEY).
- `openai`: uses the OpenAI SDK (needs OPENAI_API_KEY).
- `mock`: no API call. Mutates the current best candidate by perturbing its
  numeric constants. Useful for offline development and reproducible demos.
"""
from __future__ import annotations

import os
import random
import re
from typing import Optional


class ProviderError(RuntimeError):
    pass


class AnthropicProvider:
    DEFAULT_MODEL = "claude-opus-4-5"

    def __init__(self, model: Optional[str] = None):
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise ProviderError("anthropic SDK not installed") from e
        self.client = Anthropic()
        self.model = model or os.environ.get("FUNSEARCH_MODEL", self.DEFAULT_MODEL)

    def generate(self, system: str, user: str) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # Aggregate text blocks
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


class OpenAIProvider:
    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, model: Optional[str] = None):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ProviderError("openai SDK not installed") from e
        self.client = OpenAI()
        self.model = model or os.environ.get("FUNSEARCH_MODEL", self.DEFAULT_MODEL)

    def generate(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""


_NUMERIC = re.compile(r"(?<![\w.])(-?\d+\.\d+|-?\d+)(?![\w.])")


class MockProvider:
    """Local 'mutation' provider.

    Picks one of the top candidates and tweaks its numeric constants by a
    random factor sampled from a log-uniform around 1. Occasionally adds a
    small `+ k * something` term picked from a small palette. This is not a
    real LLM, but it lets the full FunSearch pipeline run offline.
    """

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)
        self.extra_terms = [
            "0.1 * invariants.get('triangles', 0)",
            "0.05 * invariants.get('Delta', 0)",
            "0.03 * invariants.get('n', 0)",
            "0.5 * invariants.get('density', 0)",
            "0.2 * invariants.get('diam', 0)",
            "-0.1 * invariants.get('gamma', 0)",
            "0.15 * invariants.get('alpha', 0)",
        ]

    def generate(self, system: str, user: str) -> str:
        # Pull the first candidate from the prompt; the prompt embeds top
        # candidates as ```python code blocks```.
        match = re.search(r"```python\s*\n(def heuristic_score.*?)\n```",
                          user, re.DOTALL)
        base = match.group(1) if match else (
            "def heuristic_score(G, invariants, conjecture):\n"
            "    return conjecture.violation(invariants)\n"
        )

        def perturb(m):
            val = float(m.group(1))
            factor = 10 ** self.rng.uniform(-0.3, 0.3)
            new = val * factor
            # Keep ints as ints
            if "." not in m.group(1):
                return str(int(round(new)))
            return f"{new:.4f}"

        mutated = _NUMERIC.sub(perturb, base)
        if self.rng.random() < 0.6:
            extra = self.rng.choice(self.extra_terms)
            # Inject the extra term into a return statement if there is one.
            mutated = re.sub(
                r"return\s+([^\n]+)",
                lambda r: f"return ({r.group(1)}) + {extra}",
                mutated, count=1,
            )
        return f"```python\n{mutated}\n```"


def get_provider(name: str = "auto") -> object:
    name = (name or "auto").lower()
    if name == "anthropic":
        return AnthropicProvider()
    if name == "openai":
        return OpenAIProvider()
    if name == "mock":
        return MockProvider()
    if name == "auto":
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                return AnthropicProvider()
            except ProviderError:
                pass
        if os.environ.get("OPENAI_API_KEY"):
            try:
                return OpenAIProvider()
            except ProviderError:
                pass
        return MockProvider()
    raise ProviderError(f"Unknown provider: {name}")


CODE_BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)\n```", re.DOTALL)


def extract_score_fn(text: str) -> str:
    """Extract a heuristic_score function body from raw LLM output."""
    for block in CODE_BLOCK.findall(text):
        if "def heuristic_score" in block:
            return block.strip()
    if "def heuristic_score" in text:
        return text.strip()
    raise ValueError("No heuristic_score function in LLM response")
