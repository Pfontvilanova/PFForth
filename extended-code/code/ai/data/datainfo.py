# FORTH CODE WORD: code/ai/data/datainfo
# Muestra resumen completo del dataset activo

WORD_NAME = 'data-info'
#
# === STACK EFFECT ===
# ( -- ) Muestra forma, tipos, nulos y estadísticas básicas
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

    rows, cols = df.shape
    nulls_total = int(df.isnull().sum().sum())
    target = forth._ai.get('target_col')

    print(f"=== Dataset: {rows} filas x {cols} columnas ===")

    if target:
        print(f"  Columna objetivo: {target}")

    print()
    print("Columnas:")
    col_w = max(len(c) for c in df.columns) + 2
    for col in df.columns:
        dtype  = str(df[col].dtype)
        nulls  = int(df[col].isnull().sum())
        marker = " <- objetivo" if col == target else ""
        null_s = f"  {nulls} nulos" if nulls > 0 else ""
        print(f"  {col:<{col_w}} {dtype:<12}{null_s}{marker}")

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if numeric_cols:
        print()
        print("Estadisticas numericas:")
        desc = df[numeric_cols].describe()
        col_w2 = max(len(c) for c in numeric_cols) + 2
        print(f"  {'columna':<{col_w2}} {'min':>10} {'max':>10} {'media':>10} {'std':>10}")
        print("  " + "-" * (col_w2 + 42))
        for col in numeric_cols:
            mn  = f"{desc.loc['min', col]:.3g}"
            mx  = f"{desc.loc['max', col]:.3g}"
            avg = f"{desc.loc['mean', col]:.3g}"
            std = f"{desc.loc['std', col]:.3g}"
            print(f"  {col:<{col_w2}} {mn:>10} {mx:>10} {avg:>10} {std:>10}")

    if nulls_total > 0:
        print(f"\n  Total valores nulos: {nulls_total} — considera usar data-fill")

    forth._ai['last_op'] = {
        'type':    'data-info',
        'data':    {'columns': list(df.columns), 'numeric': numeric_cols},
        'metrics': {'rows': rows, 'cols': cols, 'nulls': nulls_total},
    }

    if forth._ai.get('verbose'):
        _explain(forth._ai['last_op'])


def _explain(last_op):
    m = last_op['metrics']
    d = last_op['data']
    print()
    print(f"  El dataset tiene {m['rows']} casos y {m['cols']} variables.")
    if m['nulls'] > 0:
        print(f"  Hay {m['nulls']} valores que faltan — conviene rellenarlos antes de analizar.")
    if d['numeric']:
        print(f"  Variables numericas: {', '.join(d['numeric'])}")
