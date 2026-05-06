# FORTH CODE WORD: code/ai/data/datatypes
# Muestra el tipo de cada columna en lenguaje claro

WORD_NAME = 'data-types'
#
# === STACK EFFECT ===
# ( -- ) Lista columnas con su tipo en lenguaje natural
# === FIN ===

_TYPE_MAP = {
    'int8': 'entero', 'int16': 'entero', 'int32': 'entero', 'int64': 'entero',
    'uint8': 'entero', 'uint16': 'entero', 'uint32': 'entero', 'uint64': 'entero',
    'float16': 'decimal', 'float32': 'decimal', 'float64': 'decimal',
    'bool': 'booleano',
    'object': 'texto',
    'string': 'texto',
    'str': 'texto',
    'category': 'categoria',
}


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {
            'dataset': None, 'target_col': None,
            'train_set': None, 'test_set': None,
            'model': None, 'last_op': None,
            'verbose': False, 'image': None,
            'audio': None, 'clip_model': None, 'yolo_model': None,
        }


def _friendly_type(dtype):
    name = str(dtype)
    if name.startswith('datetime'):
        return 'fecha'
    return _TYPE_MAP.get(name, name)


def execute(forth):
    _ensure_ai(forth)

    df = forth._ai.get('dataset')
    if df is None:
        print("Error: no hay dataset cargado — usa data-load primero")
        return

    target = forth._ai.get('target_col')
    col_w  = max(len(c) for c in df.columns) + 2

    counts = {'entero': 0, 'decimal': 0, 'texto': 0,
              'booleano': 0, 'fecha': 0, 'categoria': 0, 'otro': 0}

    print("Tipos de columnas:")
    print(f"  {'columna':<{col_w}} {'tipo':<12} {'valores únicos':>14}")
    print("  " + "-" * (col_w + 28))

    for col in df.columns:
        ftype   = _friendly_type(df[col].dtype)
        uniques = df[col].nunique()
        marker  = " <- objetivo" if col == target else ""
        key     = ftype if ftype in counts else 'otro'
        counts[key] += 1
        print(f"  {col:<{col_w}} {ftype:<12} {uniques:>14}{marker}")

    print()
    summary = [f"{v} {k}" for k, v in counts.items() if v > 0]
    print(f"  Total: {', '.join(summary)}")

    forth._ai['last_op'] = {
        'type':    'data-types',
        'data':    {col: _friendly_type(df[col].dtype) for col in df.columns},
        'metrics': counts,
    }

    if forth._ai.get('verbose'):
        text_cols = [c for c in df.columns if _friendly_type(df[c].dtype) == 'texto']
        num_cols  = [c for c in df.columns
                     if _friendly_type(df[c].dtype) in ('entero', 'decimal')]
        print()
        if num_cols:
            print(f"  Columnas numericas ({len(num_cols)}): {', '.join(num_cols)}")
        if text_cols:
            print(f"  Columnas de texto ({len(text_cols)}): {', '.join(text_cols)}")
        print("  Las columnas de texto necesitan codificarse antes de entrenar un modelo.")
