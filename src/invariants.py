import math
import networkx as nx
import numpy as np

CACHE = {}


def cache_key(G):
    H = nx.convert_node_labels_to_integers(G)
    try:
        return nx.to_graph6_bytes(H, header=False).decode().strip()
    except Exception:
        return None


def clear_cache():
    CACHE.clear()


def neighbor_masks(G):
    H = nx.convert_node_labels_to_integers(G)
    n = H.number_of_nodes()
    closed = [0] * n
    opn = [0] * n
    for v in range(n):
        m = 0
        for u in H.neighbors(v):
            m |= (1 << u)
        closed[v] = m | (1 << v)
        opn[v] = m
    return n, closed, opn


def domination_bitmask(G):
    n, closed, dummy = neighbor_masks(G)
    if n == 0:
        return 0
    full = (1 << n) - 1
    best = [n]

    def srch(covered, depth):
        if covered == full:
            best[0] = min(best[0], depth); return
        if depth + 1 >= best[0]:
            return
        unc = full & ~covered
        v = (unc & -unc).bit_length() - 1
        cands = [u for u in range(n) if closed[u] & (1 << v)]
        cands.sort(key=lambda u: bin(closed[u] & ~covered).count("1"), reverse=True)
        for u in cands:
            srch(covered | closed[u], depth + 1)

    srch(0, 0)
    return best[0]


def total_domination_bitmask(G):
    n, dummy, opn = neighbor_masks(G)
    if n == 0:
        return 0
    if any(opn[v] == 0 for v in range(n)):
        return n
    full = (1 << n) - 1
    best = [n]

    def srch(covered, depth):
        if covered == full:
            best[0] = min(best[0], depth); return
        if depth + 1 >= best[0]:
            return
        unc = full & ~covered
        v = (unc & -unc).bit_length() - 1
        cands = [u for u in range(n) if opn[u] & (1 << v)]
        cands.sort(key=lambda u: bin(opn[u] & ~covered).count("1"), reverse=True)
        for u in cands:
            srch(covered | opn[u], depth + 1)

    srch(0, 0)
    return best[0]


def independence_number(G):
    if G.number_of_nodes() == 0:
        return 0
    Gc = nx.complement(G)
    best = 0
    for clique in nx.find_cliques(Gc):
        if len(clique) > best:
            best = len(clique)
    return best


def independent_domination_bitmask(G):
    n, closed, dummy = neighbor_masks(G)
    if n == 0:
        return 0
    H = nx.convert_node_labels_to_integers(G)
    adj = [set(H.neighbors(v)) for v in range(n)]
    full = (1 << n) - 1
    best = [n]

    def srch(covered, chosen, depth):
        if covered == full:
            best[0] = min(best[0], depth); return
        if depth + 1 >= best[0]:
            return
        unc = full & ~covered
        v = (unc & -unc).bit_length() - 1
        for u in range(n):
            if not (closed[u] & (1 << v)):
                continue
            if any(u in adj[s] for s in chosen):
                continue
            chosen.append(u)
            srch(covered | closed[u], chosen, depth + 1)
            chosen.pop()

    srch(0, [], 0)
    return best[0]


def greedy_dom(G):
    H = nx.convert_node_labels_to_integers(G)
    nodes = list(H.nodes())
    unc = set(nodes); count = 0
    while unc:
        v = max(nodes, key=lambda x: len((set(H.neighbors(x)) | {x}) & unc))
        unc -= (set(H.neighbors(v)) | {v}); count += 1
    return count


def greedy_total_dom(G):
    H = nx.convert_node_labels_to_integers(G)
    nodes = list(H.nodes())
    if any(H.degree(v) == 0 for v in nodes):
        return len(nodes)
    unc = set(nodes); count = 0
    while unc:
        v = max(nodes, key=lambda x: len(set(H.neighbors(x)) & unc))
        unc -= set(H.neighbors(v)); count += 1
    return count


def greedy_ind_dom(G):
    H = nx.convert_node_labels_to_integers(G)
    nodes = sorted(H.nodes(), key=lambda v: H.degree(v))
    chosen = []; forbidden = set()
    for v in nodes:
        if v not in forbidden:
            chosen.append(v); forbidden.add(v); forbidden.update(H.neighbors(v))
    return len(chosen)


def greedy_indep(G):
    H = nx.convert_node_labels_to_integers(G)
    nodes = sorted(H.nodes(), key=lambda v: H.degree(v))
    chosen = []; forbidden = set()
    for v in nodes:
        if v not in forbidden:
            chosen.append(v); forbidden.add(v); forbidden.update(H.neighbors(v))
    return len(chosen)


def largest_eig(G):
    """Spectral radius (largest adjacency eigenvalue)."""
    n = G.number_of_nodes()
    if n == 0:
        return 0.0
    H = nx.convert_node_labels_to_integers(G)
    try:
        A = np.array(nx.adjacency_matrix(H).todense(), dtype=float)
        eigs = np.linalg.eigvalsh(A)
        return float(eigs[-1])
    except Exception:
        return 0.0


def largest_dist_eig(G):
    """Largest distance-matrix eigenvalue."""
    if not nx.is_connected(G) or G.number_of_nodes() < 2:
        return 0.0
    H = nx.convert_node_labels_to_integers(G)
    n = H.number_of_nodes()
    try:
        D = np.zeros((n, n), dtype=float)
        sp = dict(nx.all_pairs_shortest_path_length(H))
        for u in range(n):
            for v in range(n):
                D[u, v] = sp[u].get(v, 0)
        eigs = np.linalg.eigvalsh(D)
        return float(eigs[-1])
    except Exception:
        return 0.0


def alg_conn(G):
    """Second smallest Laplacian eigenvalue (algebraic connectivity)."""
    if G.number_of_nodes() < 2:
        return 0.0
    if not nx.is_connected(G):
        return 0.0
    H = nx.convert_node_labels_to_integers(G)
    n = H.number_of_nodes()
    try:
        L = np.array(nx.laplacian_matrix(H).todense(), dtype=float)
        eigs = np.linalg.eigvalsh(L)
        eigs.sort()
        return float(eigs[1]) if len(eigs) >= 2 else 0.0
    except Exception:
        return 0.0


def prox_rem(G):
    """Dataset convention:
       proximity  = min closeness centrality = (n-1) / max_v sum_u d(v,u)
       remoteness = max closeness centrality = (n-1) / min_v sum_u d(v,u)
    Both are in (0, 1] with proximity <= remoteness."""
    if not nx.is_connected(G) or G.number_of_nodes() < 2:
        return 0.0, 0.0
    H = nx.convert_node_labels_to_integers(G)
    n = H.number_of_nodes()
    sp = dict(nx.all_pairs_shortest_path_length(H))
    sums = [sum(sp[v].get(u, 0) for u in range(n)) for v in range(n)]
    max_sum = max(sums); min_sum = min(sums)
    proximity = (n - 1) / max_sum if max_sum > 0 else 0.0
    remoteness = (n - 1) / min_sum if min_sum > 0 else 0.0
    return proximity, remoteness


def randic(G):
    s = 0.0
    for u, v in G.edges():
        du, dv = G.degree(u), G.degree(v)
        if du > 0 and dv > 0:
            s += 1.0 / math.sqrt(du * dv)
    return s


def harmonic(G):
    s = 0.0
    for u, v in G.edges():
        du, dv = G.degree(u), G.degree(v)
        if du + dv > 0:
            s += 2.0 / (du + dv)
    return s


def z1(G):
    return sum(d * d for nodev, d in G.degree())


def z2(G):
    return sum(G.degree(u) * G.degree(v) for u, v in G.edges())


EXACT_DOM = 22
EXACT_IND = 26


def compute_invariant(G, name):
    key = cache_key(G)
    if key is not None:
        cached = CACHE.get((key, name))
        if cached is not None:
            return cached
    val = compute_inner(G, name)
    if key is not None:
        CACHE[(key, name)] = val
    return val


def compute_inner(G, name):
    n = G.number_of_nodes()
    m = G.number_of_edges()
    if name in ("order", "n"):
        return n
    if name in ("size", "m"):
        return m
    if name == "density":
        return nx.density(G)
    degs = [d for nodev, d in G.degree()]
    if name == "minimum_degree":
        return min(degs) if degs else 0
    if name == "maximum_degree":
        return max(degs) if degs else 0
    if name == "average_degree":
        return (sum(degs) / n) if n else 0.0
    if name == "diameter":
        if n < 2 or not nx.is_connected(G):
            return n
        return nx.diameter(G)
    if name == "radius":
        if n < 2 or not nx.is_connected(G):
            return n
        return nx.radius(G)
    if name == "triangle_number":
        return sum(nx.triangles(G).values()) // 3
    if name == "clique_number":
        if n == 0:
            return 0
        best = 1
        for c in nx.find_cliques(G):
            if len(c) > best:
                best = len(c)
        return best
    if name == "matching_number":
        return len(nx.max_weight_matching(G, maxcardinality=True))
    if name == "domination_number":
        return domination_bitmask(G) if n <= EXACT_DOM else greedy_dom(G)
    if name == "total_domination_number":
        return total_domination_bitmask(G) if n <= EXACT_DOM else greedy_total_dom(G)
    if name == "independent_domination_number":
        return independent_domination_bitmask(G) if n <= EXACT_DOM else greedy_ind_dom(G)
    if name == "independence_number":
        return independence_number(G) if n <= EXACT_IND else greedy_indep(G)
    if name == "vertex_cover_number":
        return n - (independence_number(G) if n <= EXACT_IND else greedy_indep(G))
    if name == "randic_index":
        return randic(G)
    if name == "harmonic_index":
        return harmonic(G)
    if name == "first_zagreb_index":
        return z1(G)
    if name == "second_zagreb_index":
        return z2(G)
    if name == "proximity":
        return prox_rem(G)[0]
    if name == "remoteness":
        return prox_rem(G)[1]
    if name == "largest_eigenvalue":
        return largest_eig(G)
    if name == "largest_distance_eigenvalue":
        return largest_dist_eig(G)
    if name == "second_smallest_laplace_eigenvalue":
        return alg_conn(G)
    raise ValueError("Invariant non supporte: " + name)