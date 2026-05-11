import random
import networkx as nx


def random_connected(min_n=6, max_n=18):
    n = random.randint(min_n, max_n)
    p = random.uniform(2.0 / n, 0.6)
    G = nx.erdos_renyi_graph(n, p)
    if not nx.is_connected(G):
        comps = list(nx.connected_components(G))
        for i in range(len(comps) - 1):
            G.add_edge(random.choice(list(comps[i])), random.choice(list(comps[i+1])))
    return G


def random_tree(min_n=6, max_n=24):
    n = random.randint(min_n, max_n)
    return nx.random_labeled_tree(n) if hasattr(nx, "random_labeled_tree") else nx.random_tree(n)


def random_bipartite(min_n=6, max_n=18):
    n1 = random.randint(2, max_n // 2)
    n2 = random.randint(2, max_n - n1)
    p = random.uniform(0.2, 0.7)
    G = nx.bipartite.random_graph(n1, n2, p)
    if not nx.is_connected(G):
        left = [v for v, d in G.nodes(data=True) if d.get("bipartite") == 0]
        right = [v for v, d in G.nodes(data=True) if d.get("bipartite") == 1]
        for u in left:
            for v in right:
                if not nx.is_connected(G):
                    G.add_edge(u, v)
                else:
                    break
            if nx.is_connected(G):
                break
    return G


def random_planar(min_n=6, max_n=16):
    n = random.randint(min_n, max_n)
    for _ in range(10):
        G = nx.random_geometric_graph(n, radius=random.uniform(0.25, 0.55))
        if nx.is_planar(G):
            if not nx.is_connected(G):
                comps = list(nx.connected_components(G))
                for i in range(len(comps) - 1):
                    u = random.choice(list(comps[i])); v = random.choice(list(comps[i+1]))
                    G.add_edge(u, v)
                    if not nx.is_planar(G):
                        G.remove_edge(u, v)
            if nx.is_connected(G) and nx.is_planar(G):
                return G
    return random_tree(min_n, max_n)


def random_claw_free(min_n=6, max_n=18):
    n_base = random.randint(max(3, min_n // 2), max(4, max_n // 2))
    base = nx.erdos_renyi_graph(n_base, random.uniform(0.2, 0.6))
    if not nx.is_connected(base):
        comps = list(nx.connected_components(base))
        for i in range(len(comps) - 1):
            base.add_edge(random.choice(list(comps[i])), random.choice(list(comps[i+1])))
    if base.number_of_edges() < 2:
        base = nx.path_graph(random.randint(min_n, max_n))
    return nx.convert_node_labels_to_integers(nx.line_graph(base))


def t_path(n): return nx.path_graph(n)
def t_cycle(n): return nx.cycle_graph(n)
def t_complete(n): return nx.complete_graph(n)
def t_complete_bipartite(a, b): return nx.complete_bipartite_graph(a, b)
def t_star(n): return nx.star_graph(n)
def t_wheel(n): return nx.wheel_graph(n)
def t_petersen(): return nx.petersen_graph()


def t_generalized_petersen(n, k):
    G = nx.Graph()
    for i in range(n):
        G.add_edge(i, (i + 1) % n)
        G.add_edge(n + i, n + ((i + k) % n))
        G.add_edge(i, n + i)
    return G


def t_subdivided_star(k, s=2):
    G = nx.Graph(); center = 0; nid = 1
    for _ in range(k):
        prev = center
        for _ in range(s + 1):
            G.add_edge(prev, nid); prev = nid; nid += 1
    return G


def t_spider(legs, length):
    return t_subdivided_star(legs, length - 1)


def t_caterpillar(spine, leaves):
    G = nx.path_graph(spine); nid = spine
    for v in range(spine):
        for _ in range(leaves):
            G.add_edge(v, nid); nid += 1
    return G


def t_corona(G, k=1):
    H = nx.convert_node_labels_to_integers(G.copy())
    nid = H.number_of_nodes()
    for v in list(H.nodes()):
        for _ in range(k):
            H.add_edge(v, nid); nid += 1
    return H


def t_friendship(k):
    G = nx.Graph(); G.add_node(0)
    for i in range(k):
        u, v = 1 + 2*i, 2 + 2*i
        G.add_edge(0, u); G.add_edge(0, v); G.add_edge(u, v)
    return G


def t_glued_kn(num, k):
    G = nx.Graph()
    for c in range(num):
        base = c * k
        for i in range(k):
            for j in range(i+1, k):
                G.add_edge(base+i, base+j)
        if c > 0:
            G.add_edge(c*k - 1, c*k)
    return G


def t_double_star(a, b):
    G = nx.Graph(); G.add_edge(0, 1); nid = 2
    for _ in range(a):
        G.add_edge(0, nid); nid += 1
    for _ in range(b):
        G.add_edge(1, nid); nid += 1
    return G


def t_book(k):
    G = nx.Graph(); G.add_edge(0, 1)
    for i in range(k):
        G.add_edge(0, 2+i); G.add_edge(1, 2+i)
    return G


def t_grid(a, b):
    return nx.convert_node_labels_to_integers(nx.grid_2d_graph(a, b))


def t_random_regular(n, d):
    if (n*d) % 2 != 0 or d >= n:
        return None
    try:
        return nx.random_regular_graph(d, n)
    except Exception:
        return None


def t_lollipop(m, k): return nx.lollipop_graph(m, k)
def t_barbell(m, k): return nx.barbell_graph(m, k)

def t_hypercube(d):
    """Q_d : hypercube de dimension d (2^d sommets, d-regulier)."""
    G = nx.hypercube_graph(d)
    return nx.convert_node_labels_to_integers(G)


def t_kneser(n, k):
    try:
        G = nx.algorithms.operators.complement(nx.lollipop_graph(1, 1))
        # fallback simple : graphe biparti dense
        return nx.complete_bipartite_graph(n - k, k)
    except Exception:
        return nx.complete_bipartite_graph(n - k, k)

def t_line_kab(a, b):
    return nx.convert_node_labels_to_integers(nx.line_graph(nx.complete_bipartite_graph(a, b)))


def t_broom(hub_leaves, tail_length):
    """Hub with `hub_leaves` pendants and a tail path of `tail_length` edges.

    Gives small vc/matching with a single very peripheral vertex (small prox).
    """
    G = nx.Graph(); G.add_node(0); nid = 1
    for _ in range(hub_leaves):
        G.add_edge(0, nid); nid += 1
    prev = 0
    for _ in range(tail_length):
        G.add_edge(prev, nid); prev = nid; nid += 1
    return G


def t_double_broom(left_leaves, mid_len, right_leaves):
    """Path of length mid_len with `left_leaves` pendants on one end and
    `right_leaves` pendants on the other. Keeps matching/vc small."""
    G = nx.Graph()
    spine = list(range(mid_len + 1))
    for i in range(mid_len):
        G.add_edge(spine[i], spine[i + 1])
    nid = mid_len + 1
    for _ in range(left_leaves):
        G.add_edge(0, nid); nid += 1
    for _ in range(right_leaves):
        G.add_edge(mid_len, nid); nid += 1
    return G


def t_complete_with_pendant(n, k=1):
    """K_n with k pendant vertices each attached to a single vertex of K_n.
    Stays claw-free for any k. Has large lambda1 but low alg_conn."""
    G = nx.complete_graph(n)
    nid = n
    for _ in range(k):
        G.add_edge(0, nid); nid += 1
    return G


def t_complete_minus_edge(n):
    """K_n minus one edge. Still claw-free, near-maximal lambda1."""
    G = nx.complete_graph(n)
    if n >= 2:
        G.remove_edge(0, 1)
    return G


def t_kneser_safe(n, k):
    try:
        G = nx.generators.classic.complete_graph(0)  # placeholder
        from itertools import combinations
        nodes = list(combinations(range(n), k))
        G = nx.Graph()
        for i, a in enumerate(nodes):
            for j in range(i + 1, len(nodes)):
                if not (set(a) & set(nodes[j])):
                    G.add_edge(i, j)
        return G if G.number_of_edges() > 0 else None
    except Exception:
        return None


def t_clique_join_with_satellite(a, b, far_size):
    """K_1 join (K_a ⊔ K_b) plus `far_size` extra vertices forming a clique
    attached to a single K_a vertex. Always claw-free; gives a vertex of degree
    a+b at the center, with far vertices at distance 2 (high remoteness)."""
    G = nx.Graph()
    center = 0
    for i in range(1, a + 1):
        G.add_edge(center, i)
        for j in range(i + 1, a + 1):
            G.add_edge(i, j)
    for i in range(a + 1, a + b + 1):
        G.add_edge(center, i)
        for j in range(i + 1, a + b + 1):
            G.add_edge(i, j)
    far_start = a + b + 1
    far_end = far_start + far_size
    for f in range(far_start, far_end):
        G.add_edge(f, 1)
    for f in range(far_start, far_end):
        for g in range(f + 1, far_end):
            G.add_edge(f, g)
    return G


def t_paley(q):
    """Paley graph on q vertices (q prime power ≡ 1 mod 4). Strongly regular,
    claw-free for most q, useful for spectral conjectures."""
    try:
        from networkx.generators.classic import paley_graph
        return paley_graph(q)
    except Exception:
        return None


def is_claw_free(G):
    for v in G.nodes():
        nbrs = list(G.neighbors(v))
        if len(nbrs) < 3:
            continue
        for i in range(len(nbrs)):
            for j in range(i+1, len(nbrs)):
                if G.has_edge(nbrs[i], nbrs[j]):
                    continue
                for k in range(j+1, len(nbrs)):
                    if not G.has_edge(nbrs[i], nbrs[k]) and not G.has_edge(nbrs[j], nbrs[k]):
                        return False
    return True


def template_list(graph_classes):
    classes = set(graph_classes or [])
    T = []
    for n in (6, 8, 10, 12, 14, 16, 18, 20):
        T.append(t_path(n)); T.append(t_cycle(n))
    for n in (6, 8, 10, 12, 14, 16, 20):
        T.append(t_caterpillar(n // 2, 1))
        T.append(t_caterpillar(n // 2, 2))
    for k in range(3, 9):
        for s in range(1, 5):
            T.append(t_subdivided_star(k, s))
    for n in (4, 5, 6, 7, 8, 9, 10):
        T.append(t_corona(nx.path_graph(n), 1))
        T.append(t_corona(nx.cycle_graph(n), 1))
    for a in (2, 3, 4, 5, 6):
        for b in (2, 3, 4, 5, 6):
            T.append(t_double_star(a, b))
    for legs in range(3, 9):
        for length in range(2, 6):
            T.append(t_spider(legs, length))
    if "tree" not in classes:
        for n in (4, 5, 6, 7, 8, 9, 10, 12):
            T.append(t_complete(n))
        for a in (2, 3, 4, 5, 6, 7):
            for b in (2, 3, 4, 5, 6, 7):
                T.append(t_complete_bipartite(a, b))
        for n in (5, 6, 7, 8, 9, 10, 12, 15):
            T.append(t_wheel(n))
        T.append(t_petersen())
        for np_, kp in [(5,2),(6,2),(7,2),(7,3),(8,3),(9,2),(9,4),(10,3),(11,2),(12,5)]:
            T.append(t_generalized_petersen(np_, kp))
        for k in (2, 3, 4, 5, 6, 8, 10):
            T.append(t_friendship(k))
        for k in (2, 3, 4, 5, 6, 8):
            T.append(t_book(k))
        for num, k in [(2,3),(3,3),(4,3),(2,4),(3,4),(4,4),(2,5),(3,5),(2,6)]:
            T.append(t_glued_kn(num, k))
        for a in (3, 4, 5, 6):
            for b in (3, 4, 5, 6):
                T.append(t_grid(a, b))
        
        for d in (2, 3, 4, 5, 6):
            T.append(t_hypercube(d))
        # K_n plus grands pour proximity faible
        for n in (15, 18, 20, 25, 30):
            T.append(t_complete(n))
        for n in (8, 10, 12):
            T.append(t_complete_bipartite(n, n))
        
                # Grands graphes bipartis pour les conjectures triangle_number vs largest_eigenvalue
        for n in (10, 12, 15, 20, 25, 30, 40, 50):
            T.append(nx.complete_bipartite_graph(n, n))
        for n in (15, 20, 25, 30):
            T.append(nx.complete_bipartite_graph(int(n*1.5), int(n*0.5)))

                # Graphes très denses pour proximity (proximity = 1 pour graphe complet)
        for n in (30, 40, 50, 60, 70, 80, 90, 100):
            T.append(nx.complete_graph(n))
        for n in (15, 20, 25, 30, 35, 40):
            T.append(nx.complete_bipartite_graph(n, n))
        
        for n, d in [(8,3),(10,3),(10,4),(12,3),(12,4),(14,3),(16,3),(20,3)]:
            r = t_random_regular(n, d)
            if r is not None:
                T.append(r)
        for m, k in [(3,2),(4,2),(4,4),(5,3),(6,4)]:
            T.append(t_lollipop(m, k))
        for m, k in [(3,2),(4,2),(4,3),(5,3),(6,4)]:
            T.append(t_barbell(m, k))
        for a in (2, 3, 4, 5):
            for b in (2, 3, 4, 5):
                T.append(t_line_kab(a, b))
    if "tree" in classes:
        T = [g for g in T if nx.is_tree(g)]
    if "bipartite" in classes:
        T = [g for g in T if nx.is_bipartite(g)]
    if "planar" in classes:
        T = [g for g in T if nx.is_planar(g)]
    if "claw_free" in classes:
        T = [g for g in T if is_claw_free(g)]
    T = [g for g in T if g.number_of_nodes() >= 2 and nx.is_connected(g)]
    return T


def random_for_class(graph_classes, min_n=6, max_n=20):
    classes = set(graph_classes or [])
    if "tree" in classes: return random_tree(min_n, max_n)
    if "bipartite" in classes: return random_bipartite(min_n, max_n)
    if "planar" in classes: return random_planar(min_n, max_n)
    if "claw_free" in classes: return random_claw_free(min_n, max_n)
    return random_connected(min_n, max_n)


def extreme_seeds(graph_classes, x_name, y_name):
    """Return graphs likely to violate conjectures involving the given invariants.

    Picks heavy on graphs that produce extreme values for the named invariants.
    Filtered by class membership downstream.
    """
    names = {x_name, y_name}
    S = []
    # Sparse / path-like family: large diameter, remoteness, alpha.
    for n in (10, 14, 20, 30, 50, 70, 100):
        S.append(t_path(n))
    for legs in (3, 4, 5, 6, 8):
        for length in (3, 5, 8):
            S.append(t_spider(legs, length))
    for spine in (4, 6, 8, 12, 16, 24, 32):
        for leaves in (1, 2, 3):
            S.append(t_caterpillar(spine, leaves))
    for k in (3, 5, 8, 12, 16):
        for s in (2, 3, 5):
            S.append(t_subdivided_star(k, s))
    for a, b in [(2,2),(2,4),(3,5),(4,8),(5,10),(6,12),(8,8),(9,12),(10,10),(10,11),(11,11),(11,10),(15,6),(20,1)]:
        S.append(t_double_star(a, b))
    # Larger double stars sweep
    for a in range(2, 16):
        for b in range(2, 16):
            if 4 <= a + b <= 24:
                S.append(t_double_star(a, b))

    classes = set(graph_classes or [])
    is_tree_only = "tree" in classes
    if not is_tree_only:
        # Dense family: small proximity, large clique / triangle / eigenvalue.
        for n in (10, 15, 20, 30, 50, 80, 120):
            S.append(t_complete(n))
        for n in (6, 8, 10, 12, 16, 20, 25, 30):
            S.append(t_complete_bipartite(n, n))
        for a, b in [(3,9),(4,12),(5,15),(6,20),(8,24),(10,30)]:
            S.append(t_complete_bipartite(a, b))
        for n in (5, 8, 10, 12, 16, 20):
            S.append(t_wheel(n))
        for k in (3, 5, 8, 12, 16, 20):
            S.append(t_friendship(k))
        for k in (3, 5, 8, 12, 16):
            S.append(t_book(k))
        for num, k in [(2,4),(3,4),(4,4),(2,5),(3,5),(2,6),(3,6),(2,8)]:
            S.append(t_glued_kn(num, k))
        for m_, k_ in [(4,3),(6,4),(8,5),(10,6),(12,8)]:
            S.append(t_lollipop(m_, k_))
            S.append(t_barbell(m_, k_))
        for d in (3, 4, 5, 6):
            S.append(t_hypercube(d))
        # Line graphs of complete graphs / complete bipartite → claw-free, dense.
        for kn in (4, 5, 6, 7, 8, 10):
            S.append(nx.convert_node_labels_to_integers(nx.line_graph(nx.complete_graph(kn))))
        for a, b in [(2,3),(2,4),(3,3),(3,4),(4,4),(3,5),(4,5),(5,5)]:
            S.append(t_line_kab(a, b))
        for n, d in [(8,3),(10,3),(10,4),(12,3),(12,4),(14,3),(16,3),(20,3),(20,5),(24,4)]:
            r = t_random_regular(n, d)
            if r is not None: S.append(r)
        # Multi-clique paths and webs (good for total_domination / matching).
        for a, b in [(2,4),(3,4),(4,4),(2,5),(3,5),(2,6)]:
            S.append(t_glued_kn(a, b))

    # Specific boosts based on what invariants appear.
    if "proximity" in names or "remoteness" in names:
        for n in (40, 50, 60, 80, 100, 150, 200):
            if not is_tree_only:
                S.append(t_complete(n))
            S.append(t_path(n))
    if "largest_eigenvalue" in names or "largest_distance_eigenvalue" in names:
        for n in (10, 15, 20, 30, 50):
            if not is_tree_only:
                S.append(t_complete(n))
        for n in (10, 16, 24, 32):
            S.append(t_star(n))
    if "second_smallest_laplace_eigenvalue" in names:
        # Cycles and large complete bipartite emphasize this spectrum.
        for n in (6, 10, 14, 20, 30, 50):
            S.append(t_cycle(n))
        if not is_tree_only:
            for n in (8, 12, 16, 20):
                S.append(t_complete(n))
    if "triangle_number" in names or "clique_number" in names:
        if not is_tree_only:
            for n in (6, 8, 10, 12, 15, 20, 25):
                S.append(t_complete(n))
            for k in (3, 5, 8, 12, 16):
                S.append(t_friendship(k))
    if "matching_number" in names or "vertex_cover_number" in names \
            or "independence_number" in names:
        for n in (8, 12, 16, 20, 30):
            S.append(t_path(n))
        if not is_tree_only:
            for n in (8, 10, 12, 14, 16, 20):
                S.append(t_cycle(n))

    # Broom family: small vc/matching plus a far peripheral vertex (small prox).
    # Useful for `prox >= linear(vc)` / `prox >= linear(matching)` style.
    if "proximity" in names and (
        "vertex_cover_number" in names or "matching_number" in names
        or "independence_number" in names or "total_domination_number" in names
        or "domination_number" in names):
        for hl in (4, 8, 12, 14, 16, 20, 30):
            for tl in (2, 3, 4, 5, 6, 8):
                S.append(t_broom(hl, tl))
        for ll in (2, 4, 6, 8, 12):
            for mid in (2, 3, 4, 5, 6, 8):
                for rl in (2, 4, 6, 8, 12):
                    S.append(t_double_broom(ll, mid, rl))

    # Brooms / spider-tail also help remoteness with vc/matching/dom.
    if "remoteness" in names and (
        "vertex_cover_number" in names or "matching_number" in names
        or "domination_number" in names or "total_domination_number" in names):
        for hl in (4, 8, 12, 16, 20):
            for tl in (2, 3, 4, 6, 8):
                S.append(t_broom(hl, tl))
        for ll in (2, 4, 6, 8):
            for mid in (2, 3, 4, 6, 8):
                for rl in (2, 4, 6, 8):
                    S.append(t_double_broom(ll, mid, rl))

    # K_1 ∨ (K_a ⊔ K_b) with a satellite K_c attached to one vertex:
    # claw-free, low-density yet high remoteness via the central join vertex.
    if ("remoteness" in names or "proximity" in names) and not is_tree_only:
        for a in (3, 4, 5, 6, 7, 8):
            for b in (3, 4, 5, 6, 7, 8):
                for c in (2, 3, 4, 5, 6):
                    S.append(t_clique_join_with_satellite(a, b, c))

    # Claw-free families pushing large lambda1 vs small triangle / alg_conn.
    if (("largest_eigenvalue" in names or "second_smallest_laplace_eigenvalue" in names)
            and not is_tree_only):
        for n in (6, 8, 10, 12, 14, 16, 18, 20, 24):
            for k in (1, 2, 3, 5):
                S.append(t_complete_with_pendant(n, k))
            S.append(t_complete_minus_edge(n))
        for q in (5, 9, 13, 17, 25, 29):
            pg = t_paley(q)
            if pg is not None:
                S.append(pg)
        for k in (3, 5, 7, 10, 14, 20):
            S.append(t_friendship(k))

    return S

def t_complete_graphs():
    """Liste de graphes complets de grande taille"""
    T = []
    for n in [25, 30, 35, 40, 45, 50]:
        T.append(nx.complete_graph(n))
        # Graphes très denses pour proximité
    for G in t_complete_graphs():
        T.append(G)
    for G in t_strongly_regular(50, 0, 0, 0):
        T.append(G)
    return T

def t_strongly_regular(n, k, l, mu):
    """Graphes fortement réguliers (si disponibles)"""
    try:
        # Graphe de Paley (existe pour n ≡ 1 mod 4, n puissance de premier)
        from networkx.generators.classic import paley_graph
        for q in [9, 13, 17, 25, 29, 37, 41, 49, 53, 61]:
            if q <= n:
                G = paley_graph(q)
                yield G
    except Exception:
        pass
