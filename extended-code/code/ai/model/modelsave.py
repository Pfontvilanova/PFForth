# FORTH CODE WORD: code/ai/model/modelsave
# Guarda el modelo entrenado en disco con joblib

WORD_NAME = 'model-save'
#
# === STACK EFFECT ===
# ( nombre -- ) Guarda en models/<nombre>.pkl
# === FIN ===

import os


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
    ai = forth._ai

    if not forth.stack:
        print("Error: falta el nombre del archivo en la pila")
        print("  Uso: s\" mi_modelo\" model-save")
        return

    raw_name = forth.stack.pop()
    if not isinstance(raw_name, str) or not raw_name.strip():
        print("Error: el nombre debe ser una cadena no vacía")
        return

    model_cfg = ai.get('model')
    if not isinstance(model_cfg, dict) or model_cfg.get('fitted') is None:
        print("Error: modelo no entrenado — usa model-train primero")
        return

    # Construir ruta: models/<nombre>.pkl
    name = raw_name.strip()
    if not name.endswith('.pkl'):
        name += '.pkl'

    models_dir = os.path.join(os.getcwd(), 'models')
    os.makedirs(models_dir, exist_ok=True)

    # Sanear nombre (sin traversal de directorios)
    base = os.path.basename(name)
    path = os.path.join(models_dir, base)

    # Payload completo para poder restaurar el estado AI
    payload = {
        'model_cfg':  model_cfg,          # algo, fitted, task, features, params
        'target_col': ai.get('target_col'),
        'scaler':     ai.get('scaler'),   # MinMaxScaler si data-norm fue usado
        'version':    1,
    }

    try:
        import joblib
        joblib.dump(payload, path)
        size_kb = os.path.getsize(path) / 1024

        _NAMES = {'rf': 'Random Forest', 'tree': 'Árbol de decisión',
                  'knn': 'KNN', 'svm': 'SVM'}
        algo_name = _NAMES.get(model_cfg['algo'], model_cfg['algo'])
        task_name = 'Clasificación' if model_cfg['task'] == 'classification' else 'Regresión'

        print(f"✓ Modelo guardado: {path}")
        print(f"  Algoritmo : {algo_name}  ({task_name})")
        print(f"  Variables : {', '.join(model_cfg['features'])}")
        print(f"  Objetivo  : {ai.get('target_col')}")
        print(f"  Tamaño    : {size_kb:.1f} KB")
        if ai.get('scaler'):
            print(f"  Scaler    : incluido (datos normalizados)")
        print(f"  Recuperar : s\" {base}\" model-load")

    except ImportError:
        print("Error: joblib no está disponible")
        print("  joblib viene incluido con scikit-learn")
        print("  Comprueba la instalación: import code/ai/data/dataload")
    except Exception as e:
        print(f"Error al guardar: {e}")
        return

    ai['last_op'] = {
        'type':    'model-save',
        'data':    {'path': path, 'algo': model_cfg['algo']},
        'metrics': {'size_kb': round(size_kb, 1)},
    }
