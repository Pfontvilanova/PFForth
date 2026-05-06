# FORTH CODE WORD: code/ai/data/datatarget
# Marca la columna objetivo para el modelo

WORD_NAME = 'data-target'
#
# === STACK EFFECT ===
# ( colname -- ) Define la columna objetivo para entrenamiento y evaluación
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
        print("Error: data-target requiere el nombre de la columna en la pila")
        return

    col = forth.stack.pop()

    if col not in df.columns:
        available = ', '.join(df.columns.tolist())
        print(f"Error: columna '{col}' no existe")
        print(f"  Columnas disponibles: {available}")
        return

    forth._ai['target_col'] = col
    forth._ai['train_set']  = None
    forth._ai['test_set']   = None

    # Información sobre la columna objetivo
    n_unique = df[col].nunique()
    dtype    = str(df[col].dtype)

    print(f"✓ Objetivo: '{col}'")

    if n_unique <= 10:
        counts = df[col].value_counts()
        print(f"  {n_unique} clases:")
        for val, cnt in counts.items():
            pct = cnt / len(df) * 100
            print(f"    {str(val):<15} {cnt} casos ({pct:.1f}%)")
        task_type = 'clasificacion'
    else:
        mn  = df[col].min()
        mx  = df[col].max()
        avg = df[col].mean()
        print(f"  Rango: {mn:.3g} — {mx:.3g}  (media: {avg:.3g})")
        task_type = 'regresion'

    forth._ai['last_op'] = {
        'type':    'data-target',
        'data':    {'column': col, 'task_type': task_type},
        'metrics': {'n_unique': n_unique, 'dtype': dtype},
    }

    if forth._ai.get('verbose'):
        print()
        if task_type == 'clasificacion':
            print(f"  El modelo aprenderá a clasificar en {n_unique} categorías distintas.")
        else:
            print(f"  El modelo aprenderá a predecir un valor numérico continuo.")
