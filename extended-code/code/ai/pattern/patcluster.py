# FORTH CODE WORD: code/ai/pattern/patcluster
# Agrupa filas en n clusters usando K-Means

WORD_NAME = 'pat-cluster'
#
# === STACK EFFECT ===
# ( n -- ) Agrupa los datos en n clusters; añade columna 'cluster'
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


def _bar(v, width=20):
    filled = round(v * width)
    return '█' * filled + '░' * (width - filled)


def _fmt(v):
    if isinstance(v, float):
        if abs(v) >= 1000 or (abs(v) < 0.01 and v != 0):
            return f"{v:.2e}"
        return f"{v:.3g}"
    return str(v)


def execute(forth):
    _ensure_ai(forth)

    df = forth._ai.get('dataset')
    if df is None:
        print("Error: no hay dataset cargado — usa data-load primero")
        return

    if not forth.stack:
        print("Error: pat-cluster requiere el número de clusters en la pila")
        print("  Uso: 3 pat-cluster")
        return

    n = forth.stack.pop()
    if not isinstance(n, int) or n < 2:
        print(f"Error: número de clusters debe ser entero ≥ 2, recibido: {n}")
        return

    target = forth._ai.get('target_col')

    # Columnas numéricas, excluyendo el objetivo y cluster previo
    num_cols = [c for c in df.select_dtypes(include='number').columns
                if c != target and c != 'cluster']

    if len(num_cols) < 1:
        print("Error: se necesita al menos 1 columna numérica (distinta del objetivo)")
        return

    if n > len(df):
        print(f"Error: no se pueden crear {n} clusters con solo {len(df)} filas")
        return

    try:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import silhouette_score
        import numpy as np
    except ImportError as e:
        print(f"Error: falta dependencia — {e}")
        return

    # Preparar datos (rellenar nulos temporalmente con media)
    X = df[num_cols].copy()
    X = X.fillna(X.mean())
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Entrenar K-Means
    km = KMeans(n_clusters=n, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    # Añadir columna al dataset
    df = df.copy()
    df['cluster'] = labels
    forth._ai['dataset'] = df

    # Silhouette score (calidad del agrupamiento, -1 a 1)
    sil = silhouette_score(X_scaled, labels) if len(set(labels)) > 1 else 0.0
    sil_label = ("excelente" if sil > 0.7 else
                 "buena"     if sil > 0.5 else
                 "moderada"  if sil > 0.25 else "débil")

    print(f"=== PAT-CLUSTER: K-Means con {n} clusters ===")
    print(f"  Variables usadas : {', '.join(num_cols)}")
    print(f"  Calidad (silhouette): {sil:.3f}  [{sil_label}]")
    print()

    # Perfil de cada cluster
    W = max(len(c) for c in num_cols)
    for k in range(n):
        mask  = df['cluster'] == k
        count = mask.sum()
        pct   = count / len(df)
        print(f"  Cluster {k}  ({count} filas, {100*pct:.0f}%)  "
              f"{_bar(pct)}")

        profile = df.loc[mask, num_cols].mean()
        global_m = df[num_cols].mean()

        for col in num_cols:
            val    = profile[col]
            gval   = global_m[col]
            diff   = val - gval
            arrow  = ("↑↑" if diff >  0.5*global_m.std() else
                      "↑"  if diff >  0.2*global_m.std() else
                      "↓↓" if diff < -0.5*global_m.std() else
                      "↓"  if diff < -0.2*global_m.std() else
                      "·")
            print(f"    {col:<{W}}  {_fmt(val):>8}  {arrow}")

        # Distribución del objetivo en este cluster
        if target and target in df.columns:
            tvals = df.loc[mask, target]
            if tvals.nunique() <= 10:
                dist = tvals.value_counts(normalize=True)
                parts = [f"{v}:{100*p:.0f}%" for v, p in dist.items()]
                print(f"    {'→ '+target:<{W+4}}  {', '.join(parts)}")
        print()

    # Consejo de número óptimo
    if forth._ai.get('verbose'):
        print(f"  Para encontrar el número óptimo de clusters, prueba")
        print(f"  valores de 2 a {min(8, len(df)//2)} y compara la calidad silhouette.")
        print(f"  → columna 'cluster' añadida al dataset")

    forth._ai['last_op'] = {
        'type': 'pat-cluster',
        'data': {
            'n_clusters': n,
            'features':   num_cols,
            'sizes':      [int((df['cluster'] == k).sum()) for k in range(n)],
        },
        'metrics': {
            'silhouette': round(sil, 4),
            'n_clusters': n,
        },
    }
