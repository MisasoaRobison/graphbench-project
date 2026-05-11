import random
import time
import networkx as nx

from src.graph_generation import (template_list, random_for_class,
                                   is_claw_free, extreme_seeds)
from src.mutations import mutate
from src.repair import repair_class
from src.scoring import (compute_required_invariants, base_violation,
                          heuristic_score, build_extended_invariants)
from src.graph6 import graph6


def make_candidate(G, inv, v, score, g6):
    return {"G": G, "inv": inv, "v": v, "score": score, "g6": g6}


def is_in_class(G, classes):
    classes = set(classes or [])
    if G.number_of_nodes() < 2: return False
    if "connected" in classes and not nx.is_connected(G): return False
    if "tree" in classes and not nx.is_tree(G): return False
    if "bipartite" in classes and not nx.is_bipartite(G): return False
    if "planar" in classes and not nx.is_planar(G): return False
    if "claw_free" in classes and not is_claw_free(G): return False
    return True


def evaluate_graph(G, conjecture, score_fn=None):
    G = nx.convert_node_labels_to_integers(G)
    try:
        inv = compute_required_invariants(G, conjecture)
        v = base_violation(inv, conjecture)
        if score_fn is None:
            s = heuristic_score(G, inv, conjecture)
        else:
            ext = build_extended_invariants(G, conjecture, inv)
            s = score_fn(G, ext, conjecture)
        return make_candidate(G, inv, v, s, graph6(G))
    except Exception:
        return None


def search(conjecture, time_limit=60, verbose=False, score_fn=None):
    start = time.time()
    classes = conjecture.graph_classes
    seen = set()
    best = None
    visited = 0

    def left():
        return time_limit - (time.time() - start)

    def consider(G):
        nonlocal best, visited
        if G is None or G.number_of_nodes() < 2: return None
        G = nx.convert_node_labels_to_integers(G)
        if not is_in_class(G, classes): return None
        try:
            g6 = graph6(G)
        except Exception:
            return None
        if g6 in seen: return None
        seen.add(g6)
        cand = evaluate_graph(G, conjecture, score_fn=score_fn)
        visited += 1
        if cand is None: return None
        if best is None or cand["score"] > best["score"]:
            best = cand
        return cand

    seeds = extreme_seeds(classes, conjecture.x_invariant, conjecture.y_invariant)
    templates = template_list(classes) + seeds
    random.shuffle(templates)
    for tpl in templates:
        if left() <= 0: break
        c = consider(tpl)
        if c is not None and c["v"] > 1e-9:
            return c["G"], c["v"], {"phase": "template", "n_evaluated": visited,
                                     "elapsed": time.time() - start}

    population = []
    if best is not None:
        population.append(best)
    for nodev in range(6):
        if left() <= 0: break
        G0 = random_for_class(classes)
        G0 = repair_class(G0, classes)
        c = consider(G0)
        if c is not None:
            population.append(c)
            if c["v"] > 1e-9:
                return c["G"], c["v"], {"phase": "init", "n_evaluated": visited,
                                         "elapsed": time.time() - start}

    if not population:
        Gd = repair_class(nx.path_graph(8), classes)
        c = consider(Gd)
        if c is not None:
            population.append(c)

    stag = 0
    while left() > 0:
        if not population: break
        ps = random.sample(population, min(3, len(population)))
        parent = max(ps, key=lambda c: c["score"])
        H = mutate(parent["G"], classes)
        H = repair_class(H, classes)
        c = consider(H)
        if c is None:
            stag += 1
        else:
            if c["v"] > 1e-9:
                return c["G"], c["v"], {"phase": "search", "n_evaluated": visited,
                                         "elapsed": time.time() - start}
            if c["score"] > parent["score"]:
                stag = 0
                population.append(c)
                if len(population) > 12:
                    population.sort(key=lambda x: x["score"], reverse=True)
                    population = population[:8]
            else:
                stag += 1
        if stag > 80:
            stag = 0
            G0 = random_for_class(classes, min_n=8,
                                   max_n=random.choice([16, 22, 30, 40, 60, 80]))
            G0 = repair_class(G0, classes)
            c = consider(G0)
            if c is not None:
                population.append(c)
                if c["v"] > 1e-9:
                    return c["G"], c["v"], {"phase": "restart", "n_evaluated": visited,
                                             "elapsed": time.time() - start}

    if best is None:
        return None, float("-inf"), {"phase": "none", "n_evaluated": visited,
                                      "elapsed": time.time() - start}
    return best["G"], best["v"], {"phase": "best", "n_evaluated": visited,
                                   "elapsed": time.time() - start}