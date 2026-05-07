import networkx as nx

# ----------------------------------------------------------------------
# Calculs exacts pour n <= 30
# ----------------------------------------------------------------------

def exact_domination(G):
    nodes = list(G.nodes)
    n = len(nodes)
    order = sorted(nodes, key=lambda v: G.degree(v), reverse=True)
    best = n

    def is_dominating(S):
        dominated = set()
        for v in S:
            dominated.add(v)
            dominated.update(G.neighbors(v))
        return len(dominated) == n

    def search(idx, current):
        nonlocal best
        if len(current) >= best:
            return
        if idx == n:
            if is_dominating(current):
                best = len(current)
            return
        search(idx + 1, current)
        current.append(order[idx])
        search(idx + 1, current)
        current.pop()

    search(0, [])
    return best

def exact_total_domination(G):
    nodes = list(G.nodes)
    n = len(nodes)
    best = n

    def is_total_dominating(S):
        dominated = set()
        for v in S:
            dominated.update(G.neighbors(v))
        if len(dominated) < n:
            return False
        for v in S:
            if not any(u in S for u in G.neighbors(v)):
                return False
        return True

    def search(idx, current):
        nonlocal best
        if len(current) >= best:
            return
        if idx == n:
            if is_total_dominating(current):
                best = len(current)
            return
        search(idx + 1, current)
        current.append(nodes[idx])
        search(idx + 1, current)
        current.pop()

    search(0, [])
    return best

def exact_independent_domination(G):
    nodes = list(G.nodes)
    n = len(nodes)
    best = n

    def is_independent(S):
        for i, u in enumerate(S):
            for v in S[i + 1:]:
                if G.has_edge(u, v):
                    return False
        return True

    def is_dominating(S):
        dominated = set(S)
        for v in S:
            dominated.update(G.neighbors(v))
        return len(dominated) == n

    def search(idx, current):
        nonlocal best
        if len(current) >= best:
            return
        if idx == n:
            if is_independent(current) and is_dominating(current):
                best = len(current)
            return
        search(idx + 1, current)
        current.append(nodes[idx])
        search(idx + 1, current)
        current.pop()

    search(0, [])
    return best

def exact_independent_set(G):
    nodes = list(G.nodes)
    n = len(nodes)
    best = 0

    def is_independent(S):
        for i, u in enumerate(S):
            for v in S[i + 1:]:
                if G.has_edge(u, v):
                    return False
        return True

    def search(idx, current):
        nonlocal best
        upper = len(current) + (n - idx)
        if upper <= best:
            return
        if idx == n:
            if is_independent(current):
                best = max(best, len(current))
            return
        search(idx + 1, current)
        current.append(nodes[idx])
        search(idx + 1, current)
        current.pop()

    search(0, [])
    return best

def exact_vertex_cover(G):
    return G.number_of_nodes() - exact_independent_set(G)

# ----------------------------------------------------------------------
# Heuristiques pour grands graphes (n > 30)
# ----------------------------------------------------------------------

def approx_domination(G):
    nodes = list(G.nodes)
    uncovered = set(nodes)
    count = 0
    while uncovered:
        v = max(nodes, key=lambda x: len((set(G.neighbors(x)) | {x}) & uncovered))
        uncovered -= (set(G.neighbors(v)) | {v})
        count += 1
    return count

def approx_total_domination(G):
    nodes = list(G.nodes)
    uncovered = set(nodes)
    count = 0
    while uncovered:
        best = nodes[0]
        best_gain = 0
        for v in nodes:
            gain = len(set(G.neighbors(v)) & uncovered)
            if gain > best_gain:
                best_gain = gain
                best = v
        uncovered -= set(G.neighbors(best))
        count += 1
    return count

def approx_independent_domination(G):
    ind_set = nx.approximation.maximum_independent_set(G)
    dominated = set(ind_set)
    for v in ind_set:
        dominated.update(G.neighbors(v))
    missing = set(G.nodes) - dominated
    return len(ind_set) + len(missing)   # simple ajout

# ----------------------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------------------

def compute_invariant(G, name):
    # Invariants simples
    if name == "n":
        return G.number_of_nodes()
    if name == "m":
        return G.number_of_edges()
    degrees = [d for _, d in G.degree()]
    if name == "average_degree":
        return sum(degrees) / len(degrees) if degrees else 0
    if name == "minimum_degree":
        return min(degrees) if degrees else 0
    if name == "maximum_degree":
        return max(degrees) if degrees else 0
    if name == "triangle_number":
        return sum(nx.triangles(G).values()) // 3
    if name == "clique_number":
        if G.number_of_nodes() <= 30:
            # calcul exact
            max_clique = 0
            for clique in nx.find_cliques(G):
                max_clique = max(max_clique, len(clique))
            return max_clique
        else:
            # approximation pour les grands graphes
            return len(nx.approximation.max_clique(G))
    if name == "diameter":
        return nx.diameter(G) if nx.is_connected(G) and G.number_of_nodes() > 1 else G.number_of_nodes()
    if name == "radius":
        return nx.radius(G) if nx.is_connected(G) and G.number_of_nodes() > 1 else G.number_of_nodes()
    if name == "matching_number":
        return len(nx.max_weight_matching(G, maxcardinality=True))

    n = G.number_of_nodes()
    if n <= 30:
        if name == "domination_number":
            return exact_domination(G)
        if name == "total_domination_number":
            return exact_total_domination(G)
        if name == "independent_domination_number":
            return exact_independent_domination(G)
        if name == "vertex_cover_number":
            return exact_vertex_cover(G)
        if name == "independence_number":
            return exact_independent_set(G)
    else:
        if name == "domination_number":
            return approx_domination(G)
        if name == "total_domination_number":
            return approx_total_domination(G)
        if name == "independent_domination_number":
            return approx_independent_domination(G)
        if name == "vertex_cover_number":
            return len(nx.approximation.min_weighted_vertex_cover(G))
        if name == "independence_number":
            return len(nx.approximation.maximum_independent_set(G))

    raise ValueError(f"Invariant non supporté : {name}")