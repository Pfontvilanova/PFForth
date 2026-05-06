# FORTH CODE WORD: code/ai/data/datacols
# Lista los nombres de todas las columnas y los deja en la pila

WORD_NAME = 'data-cols'
#
# === STACK EFFECT ===
# ( -- col1 col2 ... n ) Lista columnas y las deja en la pila con su conteo
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

    cols   = list(df.columns)
    target = forth._ai.get('target_col')

    print(f"Columnas ({len(cols)}):")
    for i, col in enumerate(cols, 1):
        marker = " <- objetivo" if col == target else ""
        print(f"  {i:>3}. {col}{marker}")

    # Dejar columnas en la pila: col1 col2 ... n
    for col in cols:
        forth.stack.append(col)
    forth.stack.append(len(cols))

    forth._ai['last_op'] = {
        'type':    'data-cols',
        'data':    {'columns': cols},
        'metrics': {'n_cols': len(cols)},
    }
