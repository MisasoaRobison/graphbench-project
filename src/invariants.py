import networkx as nx

# -------------------------
# HELPERS SAFE
# -------------------------
def safe_connected(G):
    return G.number_of_nodes() > 0 and nx.is_connected(G)

def compute_invariant(G, name):

    degrees = [d for _, d in G.degree()]

    # -------------------------
    # BASE
    # -------------------------
    if name == "n":
        return G.number_of_nodes()

    if name == "m":
        return G.number_of_edges()

    if name == "average_degree":
        return sum(degrees) / len(degrees) if degrees else 0

    if name == "minimum_degree":
        return min(degrees) if degrees else 0

    if name == "maximum_degree":
        return max(degrees) if degrees else 0

    # -------------------------
    # STRUCTURE
    # -------------------------
    if name == "triangle_number":
        return sum(nx.triangles(G).values()) // 3

    if name == "clique_number":
      cliques = list(nx.find_cliques(G))
      if not cliques:
          return 0
      return max(len(c) for c in cliques)

    # -------------------------
    # DISTANCES (SAFE)
    # -------------------------
    if name == "diameter":
        return nx.diameter(G) if safe_connected(G) else len(G)

    if name == "radius":
        return nx.radius(G) if safe_connected(G) else len(G)

    # -------------------------
    # MATCHING / COVER (SAFE)
    # -------------------------
    if name == "matching_number":
        return len(nx.max_weight_matching(G, maxcardinality=True))

    if name == "vertex_cover_number":
        return len(nx.approximation.min_weighted_vertex_cover(G))

    if name == "independence_number":
        return len(nx.approximation.maximum_independent_set(G))

    if name == "domination_number":
        return domination_number(G)

    if name == "independent_domination_number":
        return len(nx.approximation.maximum_independent_set(G))

    # -------------------------
    # TOTAL DOMINATION (FIX CRITIQUE)
    # -------------------------
    if name == "total_domination_number":
        uncovered = set(list(G.nodes))
        count = 0

        while uncovered:
            best = None
            best_gain = -1

            for v in list(G.nodes):
                gain = len(set(G.neighbors(v)) & uncovered)
                if gain > best_gain:
                    best_gain = gain
                    best = v

            if best is None:
                break

            uncovered -= set(G.neighbors(best))
            count += 1

        return count

    raise ValueError(f"Invariant non supporté : {name}")
  
def domination_number(G):
    nodes = list(G.nodes)
    uncovered = set(nodes)
    count = 0

    while uncovered:

        best = max(
            nodes,
            key=lambda v: len((set(G.neighbors(v)) | {v}) & uncovered)
        )

        uncovered -= set(G.neighbors(best)) | {best}
        count += 1

    return count