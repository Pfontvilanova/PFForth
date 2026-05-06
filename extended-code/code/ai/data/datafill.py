# FORTH CODE WORD: code/ai/data/datafill
# Rellena valores nulos del dataset activo

WORD_NAME = 'data-fill'
#
# === STACK EFFECT ===
# ( value -- ) Rellena nulos con el valor dado
#              Valores especiales: "mean" "median" "mode" aplican estadísticas por columna
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

    if not forth.stack:
        print("Error: data-fill requiere un valor en la pila")
        print("  Uso: 0 data-fill          (rellena con cero)")
        print("       s\" mean\" data-fill    (rellena con la media)")
        print("       s\" median\" data-fill  (rellena con la mediana)")
        print("       s\" mode\" data-fill    (rellena con la moda)")
        return

    total_nulls = int(df.isnull().sum().sum())
    if total_nulls == 0:
        forth.stack.pop()
        print("  No hay valores nulos en el dataset.")
        return

    value    = forth.stack.pop()
    df       = df.copy()
    strategy = str(value).lower()
    filled   = {}

    if strategy == 'mean':
        num_cols = df.select_dtypes(include='number').columns
        for col in num_cols:
            n = int(df[col].isnull().sum())
            if n > 0:
                m = df[col].mean()
                df[col] = df[col].fillna(m)
                filled[col] = (n, f"media={m:.3g}")
        label = "media por columna"

    elif strategy == 'median':
        num_cols = df.select_dtypes(include='number').columns
        for col in num_cols:
            n = int(df[col].isnull().sum())
            if n > 0:
                m = df[col].median()
                df[col] = df[col].fillna(m)
                filled[col] = (n, f"mediana={m:.3g}")
        label = "mediana por columna"

    elif strategy == 'mode':
        for col in df.columns:
            n = int(df[col].isnull().sum())
            if n > 0:
                m = df[col].mode()
                if len(m) > 0:
                    df[col] = df[col].fillna(m[0])
                    filled[col] = (n, f"moda={m[0]}")
        label = "moda por columna"

    else:
        # Valor fijo
        for col in df.columns:
            n = int(df[col].isnull().sum())
            if n > 0:
                try:
                    df[col] = df[col].fillna(value)
                    filled[col] = (n, str(value))
                except Exception:
                    pass
        label = str(value)

    forth._ai['dataset'] = df

    print(f"✓ Nulos rellenados con {label}:")
    for col, (n, val) in filled.items():
        print(f"    {col}: {n} nulos → {val}")

    if not filled:
        print("  No se encontraron nulos en columnas compatibles con ese valor.")

    forth._ai['last_op'] = {
        'type':    'data-fill',
        'data':    {'strategy': label, 'filled': {k: v[0] for k, v in filled.items()}},
        'metrics': {'total_filled': sum(v[0] for v in filled.values())},
    }

    if forth._ai.get('verbose') and filled:
        total = sum(v[0] for v in filled.values())
        print()
        print(f"  Se han rellenado {total} valores que faltaban usando '{label}'.")
        print("  Esto evita errores al entrenar el modelo con datos incompletos.")
