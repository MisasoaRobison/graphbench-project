import random
import networkx as nx


def _fid(G):
    return 0 if G.number_of_nodes() == 0 else max(G.nodes()) + 1


def add_edge(G):
    if G.number_of_nodes() < 2: return G
    H = G.copy(); nodes = list(H.nodes())
    for _ in range(20):
        u, v = random.sample(nodes, 2)
        if not H.has_edge(u, v):
            H.add_edge(u, v); return H
    return H


def remove_edge(G):
    if G.number_of_edges() == 0: return G
    H = G.copy(); u, v = random.choice(list(H.edges())); H.remove_edge(u, v); return H


def add_vertex(G):
    H = G.copy(); new = _fid(H); H.add_node(new)
    if G.number_of_nodes() > 0:
        deg = random.randint(1, min(3, G.number_of_nodes()))
        for t in random.sample(list(G.nodes()), deg):
            H.add_edge(new, t)
    return H


def remove_vertex(G):
    if G.number_of_nodes() <= 3: return G
    H = G.copy(); H.remove_node(random.choice(list(H.nodes()))); return H


def subdivide_edge(G):
    if G.number_of_edges() == 0: return G
    H = G.copy(); u, v = random.choice(list(H.edges())); H.remove_edge(u, v)
    w = _fid(H); H.add_edge(u, w); H.add_edge(w, v); return H


def add_leaf(G):
    if G.number_of_nodes() == 0: return add_vertex(G)
    H = G.copy(); v = random.choice(list(H.nodes())); new = _fid(H); H.add_edge(v, new); return H


def add_path(G):
    if G.number_of_nodes() == 0: return add_vertex(G)
    H = G.copy(); v = random.choice(list(H.nodes())); prev = v
    for _ in range(random.randint(1, 4)):
        new = _fid(H); H.add_edge(prev, new); prev = new
    return H


def attach_clique(G):
    if G.number_of_nodes() == 0: return G
    H = G.copy(); anchor = random.choice(list(H.nodes()))
    k = random.randint(2, 4); ids = [_fid(H) + i for i in range(k)]
    cluster = [anchor] + ids
    for i in range(len(cluster)):
        for j in range(i+1, len(cluster)):
            H.add_edge(cluster[i], cluster[j])
    return H


def attach_triangle(G):
    if G.number_of_nodes() == 0: return G
    H = G.copy(); anchor = random.choice(list(H.nodes()))
    a = _fid(H); b = a + 1
    H.add_edge(anchor, a); H.add_edge(anchor, b); H.add_edge(a, b); return H


def twin_vertex(G):
    if G.number_of_nodes() == 0: return G
    H = G.copy(); v = random.choice(list(H.nodes())); new = _fid(H); H.add_node(new)
    for u in list(H.neighbors(v)):
        H.add_edge(new, u)
    if random.random() < 0.5:
        H.add_edge(new, v)
    return H


def contract_edge(G):
    if G.number_of_edges() == 0 or G.number_of_nodes() <= 3: return G
    H = G.copy(); u, v = random.choice(list(H.edges()))
    try:
        H = nx.contracted_edge(H, (u, v), self_loops=False)
        return nx.convert_node_labels_to_integers(H)
    except Exception:
        return G


def two_swap(G):
    edges = list(G.edges())
    if len(edges) < 2: return G
    H = G.copy()
    for _ in range(15):
        e1, e2 = random.sample(edges, 2); a, b = e1; c, d = e2
        if len({a, b, c, d}) < 4: continue
        if H.has_edge(a, c) or H.has_edge(b, d): continue
        H.remove_edge(a, b); H.remove_edge(c, d); H.add_edge(a, c); H.add_edge(b, d); return H
    return H


def rewire(G):
    if G.number_of_edges() == 0: return G
    H = G.copy(); u, v = random.choice(list(H.edges())); H.remove_edge(u, v)
    nodes = list(H.nodes())
    for _ in range(10):
        x = random.choice(nodes)
        if x != u and not H.has_edge(u, x):
            H.add_edge(u, x); return H
    H.add_edge(u, v); return H


def remove_leaf(G):
    if G.number_of_nodes() <= 2: return G
    leaves = [v for v in G.nodes() if G.degree(v) == 1]
    if not leaves: return G
    H = G.copy(); H.remove_node(random.choice(leaves)); return H


ALL_MUT = [
    (add_edge, 2), (remove_edge, 2), (add_vertex, 1), (remove_vertex, 1),
    (subdivide_edge, 2), (add_leaf, 2), (add_path, 2), (attach_clique, 1),
    (attach_triangle, 1), (twin_vertex, 1), (contract_edge, 1),
    (two_swap, 1), (rewire, 2),
]
TREE_MUT = [
    (add_leaf, 3), (subdivide_edge, 2), (remove_leaf, 2),
    (contract_edge, 1), (add_path, 2),
]


def mutate(G, graph_classes=None):
    classes = set(graph_classes or [])
    ops = TREE_MUT if "tree" in classes else ALL_MUT
    fns = [f for f, _ in ops]; ws = [w for _, w in ops]
    fn = random.choices(fns, weights=ws, k=1)[0]
    try:
        return fn(G)
    except Exception:
        return G
