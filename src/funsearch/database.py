"""Island-model database of scoring programs.

Mirrors the FunSearch design: several semi-independent populations evolve
in parallel; periodic migrations replace the worst island with a copy of the
best.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import random

from .program import Program


@dataclass
class Entry:
    program: Program
    fitness: float
    refuted: int
    elapsed: float


@dataclass
class Island:
    capacity: int
    entries: List[Entry] = field(default_factory=list)

    def best(self) -> Optional[Entry]:
        return max(self.entries, key=lambda e: e.fitness) if self.entries else None

    def insert(self, entry: Entry):
        # Drop duplicates by signature
        sig = entry.program.signature()
        self.entries = [e for e in self.entries if e.program.signature() != sig]
        self.entries.append(entry)
        if len(self.entries) > self.capacity:
            self.entries.sort(key=lambda e: e.fitness, reverse=True)
            self.entries = self.entries[: self.capacity]

    def sample(self, rng=None) -> Optional[Program]:
        rng = rng or random
        if not self.entries:
            return None
        # Soft-rank sampling: top entries are more likely
        sorted_e = sorted(self.entries, key=lambda e: e.fitness, reverse=True)
        weights = [max(1.0, len(sorted_e) - i) for i in range(len(sorted_e))]
        chosen = rng.choices(sorted_e, weights=weights, k=1)[0]
        return chosen.program.copy()


class Database:
    def __init__(self, n_islands=4, island_capacity=8, seed=42):
        self.rng = random.Random(seed)
        self.islands = [Island(capacity=island_capacity) for _ in range(n_islands)]
        self.history = []  # all entries inserted, oldest first

    def insert(self, island_idx: int, entry: Entry):
        self.islands[island_idx].insert(entry)
        self.history.append((island_idx, entry))

    def best(self) -> Optional[Entry]:
        best = None
        for isl in self.islands:
            b = isl.best()
            if b is None:
                continue
            if best is None or b.fitness > best.fitness:
                best = b
        return best

    def best_per_island(self):
        return [isl.best() for isl in self.islands]

    def sample_parent(self) -> (int, Optional[Program]):
        # Pick an island with probability proportional to its best fitness so
        # promising islands get explored more (still leaving room for losers).
        bests = self.best_per_island()
        weights = []
        for b in bests:
            if b is None:
                weights.append(1.0)
            else:
                weights.append(max(1.0, b.fitness + 1.0))
        idx = self.rng.choices(range(len(self.islands)), weights=weights, k=1)[0]
        return idx, self.islands[idx].sample(self.rng)

    def migrate(self):
        """Replace the worst island with a copy of the best island's top program."""
        bests = self.best_per_island()
        if any(b is None for b in bests):
            return
        worst_idx = min(range(len(bests)), key=lambda i: bests[i].fitness)
        best_idx = max(range(len(bests)), key=lambda i: bests[i].fitness)
        if worst_idx == best_idx:
            return
        # Re-seed the worst island with a perturbed copy of the global best
        seed = bests[best_idx].program
        new_isl = Island(capacity=self.islands[worst_idx].capacity)
        new_isl.insert(Entry(program=seed.copy(),
                             fitness=bests[best_idx].fitness,
                             refuted=bests[best_idx].refuted,
                             elapsed=bests[best_idx].elapsed))
        self.islands[worst_idx] = new_isl

    def summary(self):
        lines = []
        for i, isl in enumerate(self.islands):
            b = isl.best()
            if b is None:
                lines.append(f"  island {i}: (empty)")
            else:
                lines.append(f"  island {i}: best fitness={b.fitness:.3f} "
                             f"refuted={b.refuted} time={b.elapsed:.1f}s "
                             f"|terms|={len(b.program.terms)}")
        return "\n".join(lines)
