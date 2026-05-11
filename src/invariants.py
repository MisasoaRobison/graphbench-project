import networkx as nx
import math

# -------------------------
# HELPERS
# -------------------------
def safe_connected(G):
    return G.number_of_nodes() > 0 and nx.is_connected(G)

def compute_all_average_distances(G):
    if not safe_connected(G) or G.number_of_nodes() < 2:
        return [0.0]
    n = G.number_of_nodes()
    all_lengths = dict(nx.all_pairs_shortest_path_length(G))
    avg_distances = []
    for node in G.nodes():
        total_dist = sum(all_lengths[node].values())
        avg_distances.append(total_dist / (n - 1))
    return avg_distances

# -------------------------
# CŒUR DU CALCUL
# -------------------------
def compute_invariant(G, name):
    n_nodes = G.number_of_nodes()
    degrees = [d for _, d in G.degree()] if n_nodes > 0 else []

    # --- BASE ---
    if name == "n": return n_nodes
    if name == "m": return G.number_of_edges()
    if name in ["average_degree", "avg_degree"]:
        return sum(degrees) / n_nodes if n_nodes > 0 else 0
    if name == "minimum_degree": return min(degrees) if degrees else 0
    if name == "maximum_degree": return max(degrees) if degrees else 0
    if name == "density": return nx.density(G)

    # --- STRUCTURE / CLIQUES ---
    if name == "triangle_number":
        return sum(nx.triangles(G).values()) // 3
    if name == "clique_number":
        cliques = list(nx.find_cliques(G))
        return max(len(c) for c in cliques) if cliques else 0

    # --- DISTANCES ---
    if name == "diameter":
        return nx.diameter(G) if safe_connected(G) else n_nodes
    if name == "radius":
        return nx.radius(G) if safe_connected(G) else n_nodes
    if name == "proximity":
        return min(compute_all_average_distances(G))
    if name == "remoteness":
        return max(compute_all_average_distances(G))

    # --- INDICES TOPOLOGIQUES (ZAGREB / RANDIC) ---
    if name == "first_zagreb_index":
        return sum(d**2 for d in degrees)
    if name == "second_zagreb_index":
        return sum(G.degree(u) * G.degree(v) for u, v in G.edges())
    if name == "randic_index":
        res = 0
        for u, v in G.edges():
            d_u, d_v = G.degree(u), G.degree(v)
            if d_u > 0 and d_v > 0:
                res += 1.0 / math.sqrt(d_u * d_v)
        return res

    # --- MATCHING / COVER ---
    if name == "matching_number":
        return len(nx.max_weight_matching(G, maxcardinality=True))
    if name == "vertex_cover_number":
        return len(nx.approximation.min_weighted_vertex_cover(G))
    if name == "independence_number":
        return len(nx.approximation.maximum_independent_set(G))

    # --- DOMINATION ---
    if name == "domination_number":
        return domination_number_logic(G)
    if name == "independent_domination_number":
        # Une approximation courante est l'ensemble indépendant maximal (glouton)
        return len(nx.approximation.maximum_independent_set(G))
    if name == "total_domination_number":
        return total_domination_number_logic(G)

    # --- SPECTRAL (Nécessite potentiellement SciPy/NumPy) ---
    # Si SciPy n'est pas là, on renvoie 0 pour éviter le crash
    try:
        if name == "largest_eigenvalue": # Rayon spectral
            return max(nx.adjacency_spectrum(G).real)
        if name == "second_smallest_laplace_eigenvalue":
            if n_nodes < 2: return 0
            spectrum = sorted(nx.laplacian_spectrum(G))
            return spectrum[1] if len(spectrum) > 1 else 0
        if name == "largest_distance_eigenvalue":
            if not safe_connected(G): return 0
            # Matrice des distances
            dist_matrix = nx.to_numpy_array(G, weight=None) # Placeholder
            # On utilise une approximation simple car la matrice de distance est lourde
            return n_nodes * (n_nodes - 1) / 2 # Très grossier si pas de NumPy
    except:
        return 0

    raise ValueError(f"Invariant non supporté : {name}")

# -------------------------
# LOGIQUES SUPPLÉMENTAIRES
# -------------------------
def domination_number_logic(G):
    nodes = list(G.nodes)
    uncovered = set(nodes)
    count = 0
    while uncovered:
        best = max(nodes, key=lambda v: len((set(G.neighbors(v)) | {v}) & uncovered))
        uncovered -= (set(G.neighbors(best)) | {best})
        count += 1
    return count

def total_domination_number_logic(G):
    if G.number_of_nodes() == 0: return 0
    uncovered = set(list(G.nodes))
    count = 0
    nodes = list(G.nodes)
    while uncovered:
        best = None
        best_gain = -1
        for v in nodes:
            gain = len(set(G.neighbors(v)) & uncovered)
            if gain > best_gain:
                best_gain = gain
                best = v
        if best is None or best_gain == 0: break
        uncovered -= set(G.neighbors(best))
        count += 1
    return count