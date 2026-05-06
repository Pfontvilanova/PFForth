# FORTH CODE WORD: code/ai/pattern/patpca
# Reduce dimensionalidad a n componentes principales (PCA)

WORD_NAME = 'pat-pca'
#
# === STACK EFFECT ===
# ( n -- ) Aplica PCA y añade columnas PC1..PCn al dataset
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
    """Barra de porcentaje."""
    filled = round(min(v, 1.0) * width)
    return '█' * filled + '░' * (width - filled)


def _bar_loading(v, width=8):
    """Barra de carga (+/- centrada)."""
    mid   = width // 2
    fill  = round(abs(v) * mid)
    fill  = min(fill, mid)
    if v >= 0:
        return '·' * mid + '█' * fill + '░' * (mid - fill)
    else:
        return '░' * (mid - fill) + '█' * fill + '·' * mid


def execute(forth):
    _ensure_ai(forth)

    df = forth._ai.get('dataset')
    if df is None:
        print("Error: no hay dataset cargado — usa data-load primero")
        return

    if not forth.stack:
        print("Error: pat-pca requiere el número de componentes en la pila")
        print("  Uso: 2 pat-pca   (reduce a 2 componentes principales)")
        return

    n = forth.stack.pop()
    if not isinstance(n, int) or n < 1:
        print(f"Error: número de componentes debe ser entero ≥ 1, recibido: {n}")
        return

    target = forth._ai.get('target_col')

    # Columnas numéricas sin el objetivo
    num_cols = [c for c in df.select_dtypes(include='number').columns
                if c != target]

    if len(num_cols) < 2:
        print("Error: se necesitan al menos 2 columnas numéricas (sin contar el objetivo)")
        return

    if n >= len(num_cols):
        print(f"Aviso: pidiendo {n} componentes de {len(num_cols)} variables — "
              f"ajustando a {len(num_cols)-1}")
        n = len(num_cols) - 1

    try:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        import numpy as np
    except ImportError as e:
        print(f"Error: falta dependencia — {e}")
        return

    # Preparar datos
    X = df[num_cols].copy().fillna(df[num_cols].mean())
    scaler  = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Aplicar PCA
    pca      = PCA(n_components=n, random_state=42)
    X_pca    = pca.fit_transform(X_scaled)
    var_ratio = pca.explained_variance_ratio_
    loadings  = pca.components_          # shape: (n, n_features)

    # Añadir componentes al dataset
    df = df.copy()
    pc_names = [f"PC{i+1}" for i in range(n)]
    for i, name in enumerate(pc_names):
        df[name] = X_pca[:, i].round(4)
    forth._ai['dataset'] = df

    total_var = var_ratio.sum()

    print(f"=== PAT-PCA: {n} componentes principales ===")
    print(f"  Variables de entrada : {len(num_cols)}  ({', '.join(num_cols[:4])}"
          f"{'...' if len(num_cols) > 4 else ''})")
    print(f"  Varianza total retenida: {100*total_var:.1f}%")
    print()

    W = max(len(c) for c in num_cols)

    for i in range(n):
        vr  = var_ratio[i]
        cum = var_ratio[:i+1].sum()
        print(f"  PC{i+1}  {100*vr:5.1f}%  {_bar(vr)}  "
              f"(acumulado: {100*cum:.1f}%)")

        # Top 3 variables que más contribuyen a este componente
        load_i   = loadings[i]
        top_idx  = sorted(range(len(num_cols)),
                          key=lambda j: abs(load_i[j]), reverse=True)[:3]
        for j in top_idx:
            col  = num_cols[j]
            val  = load_i[j]
            sign = '+' if val >= 0 else '-'
            print(f"       {col:<{W}}  {sign}{abs(val):.3f}  {_bar_loading(val)}")
        print()

    # Consejo de cuántos componentes usar
    for k in range(1, len(var_ratio)+1):
        if var_ratio[:k].sum() >= 0.90:
            print(f"  → Para retener el 90% de la información bastan {k} componentes")
            break

    if total_var < 0.80:
        print(f"  → Con {n} componentes solo se retiene el {100*total_var:.0f}% —")
        print(f"    considera aumentar el número de componentes")

    print(f"  → Columnas añadidas al dataset: {', '.join(pc_names)}")
    print(f"    Usa data-select para quedarte solo con las PCs y el objetivo")

    if forth._ai.get('verbose'):
        print()
        print("  Interpretación:")
        print("  · PC1 capta la mayor variación del dataset.")
        print("  · Cada PC es independiente (ortogonal) de las demás.")
        print("  · Los valores de carga indican cuánto pesa cada variable.")
        print("  · Carga positiva = relación directa con esa PC.")
        print("  · Carga negativa = relación inversa con esa PC.")

    forth._ai['last_op'] = {
        'type': 'pat-pca',
        'data': {
            'features':   num_cols,
            'components': pc_names,
            'variance':   [round(float(v), 4) for v in var_ratio],
        },
        'metrics': {
            'n_components':    n,
            'total_variance':  round(float(total_var), 4),
        },
    }
