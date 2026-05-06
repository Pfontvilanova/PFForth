# FORTH CODE WORD: code/ai/data/datashuffle
# Mezcla aleatoriamente las filas del dataset activo

WORD_NAME = 'data-shuffle'
#
# === STACK EFFECT ===
# ( -- ) Reorganiza las filas en orden aleatorio
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

    forth._ai['dataset']   = df.sample(frac=1).reset_index(drop=True)
    forth._ai['train_set'] = None
    forth._ai['test_set']  = None

    print(f"✓ Mezcladas {len(df)} filas aleatoriamente")

    forth._ai['last_op'] = {
        'type':    'data-shuffle',
        'data':    {},
        'metrics': {'rows': len(df)},
    }

    if forth._ai.get('verbose'):
        print("  El orden de las filas es ahora aleatorio.")
        print("  Esto evita que el modelo aprenda patrones del orden original.")
