# FORTH CODE WORD: code/ai/model/svmmodel
# Configura un modelo Support Vector Machine

WORD_NAME = 'svm-model'
#
# === STACK EFFECT ===
# ( -- ) Prepara SVM con kernel RBF; model-train lo entrena
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
        'algo':     'svm',
        'fitted':   None,
        'task':     None,
        'features': None,
        'params':   {'C': 1.0, 'kernel': 'rbf', 'probability': True},
    }

    print("✓ Algoritmo: Support Vector Machine (kernel RBF)")
    print("  Ventajas : potente en espacios de alta dimensión,")
    print("             bueno con pocos datos y muchas variables")
    print("  Nota     : requiere datos normalizados (data-norm)")
    print("  Uso      : svm-model  model-train  model-eval")

    forth._ai['last_op'] = {
        'type': 'svm-model',
        'data': {'algo': 'svm'},
        'metrics': {},
    }
