# FORTH CODE WORD: code/ai/data/dataload
# Carga CSV/JSON/Excel en el dataset activo

WORD_NAME = 'data-load'
#
# === STACK EFFECT ===
# ( filename -- ) Carga el fichero como dataset activo
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {
            'dataset':    None,
            'target_col': None,
            'train_set':  None,
            'test_set':   None,
            'model':      None,
            'last_op':    None,
            'verbose':    False,
            'image':      None,
            'audio':      None,
            'clip_model': None,
            'yolo_model': None,
        }


def execute(forth):
    _ensure_ai(forth)

    if not forth.stack:
        print("Error: data-load requiere un nombre de fichero en la pila")
        return

    path = forth.stack.pop()

    try:
        import pandas as pd
    except ImportError:
        print("Error: pandas no está instalado (pip install pandas)")
        return

    try:
        if path.endswith('.csv'):
            df = pd.read_csv(path)
        elif path.endswith('.json'):
            df = pd.read_json(path)
        elif path.endswith('.xlsx') or path.endswith('.xls'):
            df = pd.read_excel(path)
        else:
            print(f"Error: formato no reconocido '{path}' — usa .csv, .json o .xlsx")
            return
    except FileNotFoundError:
        print(f"Error: fichero no encontrado — {path}")
        return
    except Exception as e:
        print(f"Error al cargar {path}: {e}")
        return

    forth._ai['dataset']    = df
    forth._ai['target_col'] = None
    forth._ai['train_set']  = None
    forth._ai['test_set']   = None
    forth._ai['model']      = None
    forth._ai['last_op']    = {
        'type':    'data-load',
        'data':    {'filename': path},
        'metrics': {'rows': len(df), 'cols': len(df.columns)},
    }

    import os
    print(f"✓ Cargado: {os.path.basename(path)}")
    print(f"  {len(df)} filas × {len(df.columns)} columnas")

    if forth._ai.get('verbose'):
        _explain(forth._ai['last_op'])


def _explain(last_op):
    d = last_op['data']
    m = last_op['metrics']
    print(f"  Dataset '{d['filename']}' listo: {m['rows']} casos con {m['cols']} variables cada uno.")
