# FORTH CODE WORD: code/ai/model/knnmodel
# Configura un modelo K-Nearest Neighbors

WORD_NAME = 'knn-model'
#
# === STACK EFFECT ===
# (   -- ) Prepara KNN con k=5; model-train lo entrena
# ( k -- ) Prepara KNN con k vecinos específico
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

    # Número de vecinos opcional desde la pila
    k = 5
    if forth.stack and isinstance(forth.stack[-1], int) and forth.stack[-1] > 0:
        k = forth.stack.pop()

    forth._ai['model'] = {
        'algo':     'knn',
        'fitted':   None,
        'task':     None,
        'features': None,
        'params':   {'n_neighbors': k},
    }

    print(f"✓ Algoritmo: K-Nearest Neighbors (k={k})")
    print("  Ventajas : simple, intuitivo, sin suposiciones")
    print("  Nota     : requiere datos normalizados (data-norm)")
    print(f"  Uso      : knn-model  model-train  model-eval")
    print(f"             O: {k} knn-model  para especificar k")

    forth._ai['last_op'] = {
        'type': 'knn-model',
        'data': {'algo': 'knn', 'k': k},
        'metrics': {},
    }
