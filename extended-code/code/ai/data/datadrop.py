# FORTH CODE WORD: code/ai/data/datadrop
# Elimina una columna del dataset activo

WORD_NAME = 'data-drop'
#
# === STACK EFFECT ===
# ( colname -- ) Elimina la columna indicada del dataset
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
        print("Error: data-drop requiere el nombre de la columna en la pila")
        return

    col = forth.stack.pop()

    if col not in df.columns:
        print(f"Error: columna '{col}' no existe")
        print(f"  Disponibles: {', '.join(df.columns)}")
        return

    # Avisar si es la columna objetivo
    target = forth._ai.get('target_col')
    if col == target:
        print(f"  Aviso: eliminando la columna objetivo '{col}' — se borra el objetivo")
        forth._ai['target_col'] = None

    forth._ai['dataset'] = df.drop(columns=[col])
    forth._ai['train_set'] = None
    forth._ai['test_set']  = None

    remaining = len(df.columns) - 1
    print(f"✓ Eliminada: '{col}'  ({remaining} columnas restantes)")

    forth._ai['last_op'] = {
        'type':    'data-drop',
        'data':    {'dropped': col, 'remaining': list(forth._ai['dataset'].columns)},
        'metrics': {'n_cols': remaining},
    }

    if forth._ai.get('verbose'):
        print(f"  La columna '{col}' ha sido eliminada del dataset.")
        print(f"  Columnas restantes: {', '.join(forth._ai['dataset'].columns)}")
