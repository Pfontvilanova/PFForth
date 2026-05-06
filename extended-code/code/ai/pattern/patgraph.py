# FORTH CODE WORD: code/ai/pattern/patgraph
# Grafo de relaciones entre columnas por correlación

WORD_NAME = 'pat-graph'
#
# === STACK EFFECT ===
# ( threshold -- ) Enlaza columnas cuya |correlación| supera el umbral
#                  Muestra grupos (componentes conexas) y nodos clave
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {
            'dataset': None, 'target_col': None,
            'train_set': None, 'test_set': None,
            'model': None, 'last_op': None,
            'verbose': False, 'image': None,
            'audio': None, 'clip_model': None, 'yolo_model': None,
        }


def _connected_components(nodes, edges):
    """DFS para encontrar componentes conexas (sin networkx)."""
    adj = {n: [] for n in nodes}
    for a, b, _ in edges:
        adj[a].append(b)
        adj[b].append(a)

    visited = set()
    groups  = []

    def dfs(node, group):
        visited.add(node)
        group.append(node)
        for nb in adj[node]:
            if nb not in visited:
                dfs(nb, group)

    for node in nodes:
        if node not in visited:
            g = []
            dfs(node, g)
            groups.append(sorted(g))

    return groups


def _degree(node, edges):
    """Número de conexiones de un nodo."""
    return sum(1 for a, b, _ in edges if a == node or b == node)


def execute(forth):
    _ensure_ai(forth)

    df = forth._ai.get('dataset')
    if df is None:
        print("Error: no hay dataset cargado — usa data-load primero")
        return

    if not forth.stack:
        print("Error: pat-graph requiere un umbral en la pila")
        print("  Uso: 0.7 pat-graph   (conectar columnas con |corr| ≥ 0.7)")
        return

    threshold = forth.stack.pop()
    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        print(f"Error: umbral debe ser un número entre 0 y 1, recibido: {threshold}")
        return

    if not 0.0 < threshold < 1.0:
        print(f"Error: umbral debe estar entre 0 y 1 exclusivos (recibido {threshold})")
        return

    target  = forth._ai.get('target_col')
    num_df  = df.select_dtypes(include='number')

    if num_df.shape[1] < 2:
        print("Error: se necesitan al menos 2 columnas numéricas")
        return

    corr = num_df.corr()
    cols = list(corr.columns)

    # Construir lista de aristas
    edges = []
    for i, c1 in enumerate(cols):
        for c2 in cols[i+1:]:
            v = corr.loc[c1, c2]
            if abs(v) >= threshold:
                edges.append((c1, c2, round(float(v), 3)))

    edges.sort(key=lambda x: abs(x[2]), reverse=True)

    print(f"=== PAT-GRAPH: umbral |correlación| ≥ {threshold} ===")
    print(f"  Columnas analizadas : {len(cols)}")
    print(f"  Conexiones halladas : {len(edges)}")
    print()

    if not edges:
        print(f"  No hay pares con |correlación| ≥ {threshold}")
        print(f"  Prueba un umbral más bajo: {max(0.3, threshold-0.2):.1f} pat-graph")
        forth._ai['last_op'] = {
            'type': 'pat-graph',
            'data': {'threshold': threshold, 'edges': [], 'groups': []},
            'metrics': {'n_edges': 0, 'n_groups': 0},
        }
        return

    # Mostrar aristas
    print("── Conexiones ─────────────────────────────────────────")
    W = max(len(c) for c in cols)
    for c1, c2, v in edges:
        sign   = '+' if v >= 0 else '-'
        bar    = '█' * round(abs(v) * 10) + '░' * (10 - round(abs(v) * 10))
        t_mark = " ← objetivo" if c2 == target or c1 == target else ""
        strength = ("muy alta" if abs(v) >= 0.9 else
                    "alta    " if abs(v) >= 0.7 else "media   ")
        print(f"  {c1:<{W}}  ──  {c2:<{W}}  {sign}{abs(v):.3f}  {bar}  "
              f"{strength}{t_mark}")

    # Componentes conexas
    groups = _connected_components(cols, edges)
    groups_with_edges = [g for g in groups if len(g) > 1]
    isolated          = [g[0] for g in groups if len(g) == 1]

    print()
    print("── Grupos de variables relacionadas ───────────────────")
    if groups_with_edges:
        for i, g in enumerate(groups_with_edges, 1):
            # Nodo más conectado del grupo
            hub = max(g, key=lambda n: _degree(n, edges))
            members = ', '.join(
                (f"[{n}]" if n == hub else n) for n in g
            )
            print(f"  Grupo {i}: {members}")
            if hub == target:
                print(f"    → El objetivo '{target}' es el centro de este grupo")
            else:
                print(f"    → '{hub}' es el nodo más conectado (posible variable clave)")
    else:
        print("  No hay grupos con más de una conexión")

    if isolated:
        print(f"  Aisladas (sin conexiones): {', '.join(isolated)}")
        print(f"  → Estas variables son independientes del resto")

    # Nodo más central globalmente
    if len(cols) > 2:
        hub_global = max(cols, key=lambda n: _degree(n, edges))
        hub_deg    = _degree(hub_global, edges)
        print()
        print(f"── Nodo más central ───────────────────────────────────")
        print(f"  '{hub_global}'  ({hub_deg} conexiones)")
        if hub_global == target:
            print(f"  → El propio objetivo es la variable más conectada")
        else:
            print(f"  → Variable con mayor influencia global en el dataset")

    # Consejo sobre redundancia
    redundant = [(c1, c2, v) for c1, c2, v in edges if abs(v) >= 0.9]
    if redundant:
        print()
        print(f"── Posibles redundancias (|corr| ≥ 0.9) ──────────────")
        for c1, c2, v in redundant:
            print(f"  '{c1}' y '{c2}' ({v:+.3f}) — considera eliminar una con data-drop")

    # Modo verbose: tabla de adyacencia textual
    if forth._ai.get('verbose') and len(cols) <= 12:
        print()
        print("── Matriz de adyacencia ───────────────────────────────")
        short = {c: c[:5] for c in cols}
        header = '  ' + ' '.join(f"{short[c]:>6}" for c in cols)
        print(header)
        for c1 in cols:
            row = []
            for c2 in cols:
                if c1 == c2:
                    row.append('  —   ')
                else:
                    v = corr.loc[c1, c2]
                    row.append(f" {'X' if abs(v)>=threshold else '·'}({abs(v):.2f})")
            print(f"  {short[c1]:<5} {''.join(row)}")

    forth._ai['last_op'] = {
        'type': 'pat-graph',
        'data': {
            'threshold': threshold,
            'edges':     [(c1, c2, v) for c1, c2, v in edges],
            'groups':    groups_with_edges,
            'isolated':  isolated,
        },
        'metrics': {
            'n_edges':  len(edges),
            'n_groups': len(groups_with_edges),
            'n_isolated': len(isolated),
        },
    }
