# FORTH CODE WORD: code/ai/data/datanorm
# Normaliza columnas numéricas del dataset activo (MinMax 0-1)

WORD_NAME = 'data-norm'
#
# === STACK EFFECT ===
# ( -- ) Normaliza columnas numéricas a rango 0-1 (excluye columna objetivo)
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


def execute(forth):
    _ensure_ai(forth)

    df = forth._ai.get('dataset')
    if df is None:
        print("Error: no hay dataset cargado — usa data-load primero")
        return

    try:
        from sklearn.preprocessing import MinMaxScaler
    except ImportError:
        print("Error: scikit-learn no está instalado (pip install scikit-learn)")
        return

    target     = forth._ai.get('target_col')
    num_cols   = df.select_dtypes(include='number').columns.tolist()
    skip_cols  = [target] if target else []
    cols_to_norm = [c for c in num_cols if c not in skip_cols]

    if not cols_to_norm:
        print("No hay columnas numéricas para normalizar.")
        return

    scaler = MinMaxScaler()
    ranges_before = {c: (float(df[c].min()), float(df[c].max())) for c in cols_to_norm}

    df = df.copy()
    df[cols_to_norm] = scaler.fit_transform(df[cols_to_norm])
    forth._ai['dataset'] = df
    forth._ai['scaler']  = scaler

    col_w = max(len(c) for c in cols_to_norm) + 2
    print(f"✓ Normalizadas {len(cols_to_norm)} columnas (MinMax 0-1):")
    print(f"  {'columna':<{col_w}} {'antes (min, max)':>20}   {'ahora'}")
    print("  " + "-" * (col_w + 32))
    for col in cols_to_norm:
        mn, mx = ranges_before[col]
        print(f"  {col:<{col_w}} ({mn:.3g}, {mx:.3g}){'':<{max(0,14-len(f'({mn:.3g}, {mx:.3g})'))}}--> (0.0, 1.0)")

    if skip_cols:
        print(f"  (excluida: {', '.join(skip_cols)} — columna objetivo)")

    forth._ai['last_op'] = {
        'type':    'data-norm',
        'data':    {'columns': cols_to_norm, 'skipped': skip_cols},
        'metrics': {'n_normalized': len(cols_to_norm), 'ranges_before': ranges_before},
    }

    if forth._ai.get('verbose'):
        print()
        print(f"  Se han ajustado {len(cols_to_norm)} variables al rango 0-1.")
        print("  Esto hace que todas las variables tengan el mismo peso en el modelo.")
        if target:
            print(f"  La columna objetivo '{target}' no se ha modificado.")
