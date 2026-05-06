# FORTH CODE WORD: code/ai/data/datasave
# Guarda el dataset activo en un fichero CSV, JSON o Excel

WORD_NAME = 'data-save'
#
# === STACK EFFECT ===
# ( filename -- ) Guarda el dataset activo en disco
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
        print("Error: data-save requiere un nombre de fichero en la pila")
        return

    path = forth.stack.pop()

    try:
        if path.endswith('.csv'):
            df.to_csv(path, index=False)
        elif path.endswith('.json'):
            df.to_json(path, orient='records', indent=2)
        elif path.endswith('.xlsx') or path.endswith('.xls'):
            df.to_excel(path, index=False)
        else:
            print(f"Error: formato no reconocido '{path}' — usa .csv, .json o .xlsx")
            return
    except Exception as e:
        print(f"Error al guardar {path}: {e}")
        return

    import os
    rows, cols = df.shape
    size_kb = os.path.getsize(path) / 1024
    print(f"✓ Guardado: {os.path.basename(path)}")
    print(f"  {rows} filas x {cols} columnas  ({size_kb:.1f} KB)")

    forth._ai['last_op'] = {
        'type':    'data-save',
        'data':    {'filename': path},
        'metrics': {'rows': rows, 'cols': cols, 'size_kb': round(size_kb, 1)},
    }

    if forth._ai.get('verbose'):
        print(f"  El dataset se ha guardado en '{path}' con {rows} filas y {cols} columnas.")
