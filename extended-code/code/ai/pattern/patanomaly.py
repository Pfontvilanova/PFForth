# FORTH CODE WORD: code/ai/pattern/patanomaly
# Detecta filas anómalas usando Isolation Forest

WORD_NAME = 'pat-anomaly'
#
# === STACK EFFECT ===
# (       -- )  Detección automática (contaminación=auto)
# ( ratio -- )  Ratio esperado de anomalías 0.0–0.5  (ej: 0.1 = 10%)
# Añade columna 'anomalia' al dataset: 1=normal, -1=anómalo
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


def _fmt(v):
    if isinstance(v, float):
        if abs(v) >= 1000 or (abs(v) < 0.01 and v != 0):
            return f"{v:.2e}"
        return f"{v:.3g}"
    return str(v)


def _zscore_label(z):
    az = abs(z)
    if az > 3:  return "!!! muy extremo"
    if az > 2:  return "!!  extremo"
    if az > 1:  return "!   inusual"
    return              "    normal"


def execute(forth):
    _ensure_ai(forth)

    df = forth._ai.get('dataset')
    if df is None:
        print("Error: no hay dataset cargado — usa data-load primero")
        return

    # Ratio de contaminación opcional desde la pila
    contamination = 'auto'
    if forth.stack:
        top = forth.stack[-1]
        if isinstance(top, float) and 0.0 < top <= 0.5:
            contamination = forth.stack.pop()
        elif isinstance(top, float):
            print(f"Aviso: ratio {top} fuera de rango (0–0.5) — usando 'auto'")

    target   = forth._ai.get('target_col')
    num_cols = [c for c in df.select_dtypes(include='number').columns
                if c not in (target, 'anomalia', 'cluster')]

    if not num_cols:
        print("Error: se necesita al menos 1 columna numérica (distinta del objetivo)")
        return

    try:
        from sklearn.ensemble import IsolationForest
        import numpy as np
    except ImportError as e:
        print(f"Error: falta dependencia — {e}")
        return

    # Preparar datos
    X = df[num_cols].copy().fillna(df[num_cols].mean())
    means  = X.mean()
    stds   = X.std().replace(0, 1)         # evitar división por cero

    # Entrenar Isolation Forest
    iso = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=200,
    )
    labels = iso.fit_predict(X)            # 1=normal, -1=anómalo
    scores = iso.score_samples(X)         # más negativo = más anómalo

    # Añadir columna al dataset
    df = df.copy()
    df['anomalia'] = labels
    df['_score']   = scores.round(4)
    forth._ai['dataset'] = df

    n_total   = len(df)
    n_anomaly = int((labels == -1).sum())
    n_normal  = n_total - n_anomaly
    pct       = 100 * n_anomaly / n_total

    cont_label = (f"{100*contamination:.0f}%" if isinstance(contamination, float)
                  else "automático")

    print(f"=== PAT-ANOMALY: Isolation Forest ===")
    print(f"  Variables analizadas : {', '.join(num_cols)}")
    print(f"  Modo contaminación   : {cont_label}")
    print(f"  Normales  : {n_normal} filas")
    print(f"  Anómalas  : {n_anomaly} filas  ({pct:.1f}%)")
    print()

    if n_anomaly == 0:
        print("  No se detectaron anomalías con el umbral actual.")
        print("  Prueba a bajar el ratio: 0.05 pat-anomaly")
    else:
        # Ordenar anomalías por score (más extremas primero)
        anom_df = df[df['anomalia'] == -1].copy()
        anom_df = anom_df.sort_values('_score')

        W = max(len(c) for c in num_cols)
        max_show = 10 if forth._ai.get('verbose') else 5

        print(f"── Filas anómalas {'(todas)' if n_anomaly <= max_show else f'(top {max_show})'} ──────────────────")
        for rank, (idx, row) in enumerate(anom_df.head(max_show).iterrows(), 1):
            score = row['_score']
            print(f"  [{rank}] fila {idx}  score={score:.3f}")
            # Mostrar cada variable con su z-score
            for col in num_cols:
                val = row[col]
                z   = (val - means[col]) / stds[col]
                if abs(z) > 1.0:          # solo mostrar las inusuales
                    print(f"      {col:<{W}}  {_fmt(val):>8}  "
                          f"(z={z:+.2f})  {_zscore_label(z)}")
            # Valor del objetivo si existe
            if target and target in row.index:
                print(f"      {target:<{W}}  {_fmt(row[target]):>8}")
            print()

        if n_anomaly > max_show and not forth._ai.get('verbose'):
            print(f"  ... ({n_anomaly - max_show} más — usa verbose-on para verlas todas)")

    # Limpiar columna auxiliar de score
    df.drop(columns=['_score'], inplace=True)
    forth._ai['dataset'] = df

    # Consejo final
    print("── Qué hacer con las anomalías ─────────────────────────")
    print("  · Revísalas manualmente: pueden ser errores de datos")
    print("  · O casos genuinamente excepcionales (fraude, fallo, etc.)")
    print("  · Para entrenar sin ellas:")
    print("    s\" anomalia\" data-target    \\ (temporal)")
    print("    O filtra en Python con py{ }")
    print("  → columna 'anomalia' añadida (1=normal, -1=anómalo)")

    forth._ai['last_op'] = {
        'type': 'pat-anomaly',
        'data': {
            'features':      num_cols,
            'contamination': contamination,
            'anomaly_idx':   list(df[df['anomalia'] == -1].index),
        },
        'metrics': {
            'n_total':   n_total,
            'n_anomaly': n_anomaly,
            'pct':       round(pct, 2),
        },
    }
