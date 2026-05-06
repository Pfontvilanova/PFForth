# FORTH CODE WORD: code/ai/data/datashape
# Muestra y pone en la pila las dimensiones del dataset activo

WORD_NAME = 'data-shape'
#
# === STACK EFFECT ===
# ( -- rows cols ) Muestra dimensiones y las deja en la pila
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
    print(f"  {rows} filas x {cols} columnas")

    forth.stack.append(rows)
    forth.stack.append(cols)

    forth._ai['last_op'] = {
        'type':    'data-shape',
        'data':    {},
        'metrics': {'rows': rows, 'cols': cols},
    }

    if forth._ai.get('verbose'):
        print(f"  El dataset tiene {rows} casos (filas) y {cols} variables (columnas).")
