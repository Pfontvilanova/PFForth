# FORTH CODE WORD: code/ai/model/treemodel
# Configura un árbol de decisión (clasificación o regresión)

WORD_NAME = 'tree-model'
#
# === STACK EFFECT ===
# ( -- ) Prepara árbol de decisión; model-train lo entrena
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
        'algo':     'tree',
        'fitted':   None,
        'task':     None,
        'features': None,
        'params':   {'max_depth': None, 'random_state': 42},
    }

    print("✓ Algoritmo: Árbol de decisión")
    print("  Ventajas : interpretable, muestra reglas claras,")
    print("             model-importance muy detallado")
    print("  Uso      : tree-model  model-train  model-eval")

    forth._ai['last_op'] = {
        'type': 'tree-model',
        'data': {'algo': 'tree'},
        'metrics': {},
    }
