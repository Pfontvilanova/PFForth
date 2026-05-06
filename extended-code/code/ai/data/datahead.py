# FORTH CODE WORD: code/ai/data/datahead
# Muestra las primeras n filas del dataset activo

WORD_NAME = 'data-head'
#
# === STACK EFFECT ===
# ( n -- ) Muestra las primeras n filas (si n=0 usa 5 por defecto)
# === FIN ===

_MAX_COL_WIDTH = 14
_MAX_COLS      = 6


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {
            'dataset': None, 'target_col': None,
            'train_set': None, 'test_set': None,
            'model': None, 'last_op': None,
            'verbose': False, 'image': None,
            'audio': None, 'clip_model': None, 'yolo_model': None,
        }


def _truncate(val, width):
    s = str(val)
    return s if len(s) <= width else s[:width - 2] + '..'


def execute(forth):
    _ensure_ai(forth)

    df = forth._ai.get('dataset')
    if df is None:
        print("Error: no hay dataset cargado — usa data-load primero")
        return

    n = 5
    if forth.stack:
        top = forth.stack[-1]
        if isinstance(top, int) and top > 0:
            n = forth.stack.pop()
        elif top == 0:
            forth.stack.pop()

    n = min(n, len(df))
    subset = df.head(n)
    cols   = list(df.columns)

    # Si hay demasiadas columnas, mostrar las primeras y últimas
    truncated = False
    if len(cols) > _MAX_COLS:
        show_cols  = cols[:_MAX_COLS]
        truncated  = True
    else:
        show_cols = cols

    # Calcular anchos de columna
    col_widths = {}
    for col in show_cols:
        max_val_w = max(len(_truncate(v, _MAX_COL_WIDTH)) for v in subset[col])
        col_widths[col] = max(len(col), max_val_w, 6)

    # Cabecera
    header = '  '.join(f"{c:<{col_widths[c]}}" for c in show_cols)
    sep    = '  '.join('-' * col_widths[c] for c in show_cols)
    if truncated:
        header += f"  ... (+{len(cols) - _MAX_COLS} cols)"

    print(f"Primeras {n} filas:")
    print(f"  {header}")
    print(f"  {sep}")

    for _, row in subset.iterrows():
        line = '  '.join(
            f"{_truncate(row[c], _MAX_COL_WIDTH):<{col_widths[c]}}"
            for c in show_cols
        )
        print(f"  {line}")

    if len(df) > n:
        print(f"  ... ({len(df) - n} filas más)")

    forth._ai['last_op'] = {
        'type':    'data-head',
        'data':    {'n': n},
        'metrics': {'shown': n, 'total': len(df)},
    }
