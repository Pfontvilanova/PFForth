# FORTH CODE WORD: code/ai/model/rfmodel
# Configura un modelo Random Forest (clasificación o regresión)

WORD_NAME = 'rf-model'
#
# === STACK EFFECT ===
# ( -- ) Prepara Random Forest; model-train lo entrena
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

    forth._ai['model'] = {
        'algo':     'rf',
        'fitted':   None,
        'task':     None,
        'features': None,
        'params':   {'n_estimators': 100, 'random_state': 42},
    }

    print("✓ Algoritmo: Random Forest")
    print("  Ventajas : robusto, pocas variables que ajustar,")
    print("             maneja bien datos sin normalizar")
    print("  Uso      : rf-model  model-train  model-eval")

    forth._ai['last_op'] = {
        'type': 'rf-model',
        'data': {'algo': 'rf'},
        'metrics': {},
    }
