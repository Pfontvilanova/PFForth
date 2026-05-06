# FORTH CODE WORD: code/ai/model/modelload
# Carga un modelo guardado previamente con model-save

WORD_NAME = 'model-load'
#
# === STACK EFFECT ===
# ( nombre -- ) Carga models/<nombre>.pkl y restaura el estado AI
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
        print("  Uso: s\" mi_modelo\" model-load")
        return

    raw_name = forth.stack.pop()
    if not isinstance(raw_name, str) or not raw_name.strip():
        print("Error: el nombre debe ser una cadena no vacía")
        return

    name = raw_name.strip()
    if not name.endswith('.pkl'):
        name += '.pkl'

    base = os.path.basename(name)

    # Buscar en models/ primero, luego ruta absoluta/relativa dada
    candidates = [
        os.path.join(os.getcwd(), 'models', base),
        os.path.abspath(name),
    ]
    path = next((p for p in candidates if os.path.isfile(p)), None)

    if path is None:
        models_dir = os.path.join(os.getcwd(), 'models')
        print(f"Error: archivo no encontrado: '{base}'")
        print(f"  Buscado en: {models_dir}")
        # Listar modelos disponibles
        if os.path.isdir(models_dir):
            pkls = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
            if pkls:
                print(f"  Modelos disponibles: {', '.join(pkls)}")
            else:
                print(f"  No hay modelos guardados aún")
        return

    try:
        import joblib
        payload = joblib.load(path)
    except Exception as e:
        print(f"Error al cargar: {e}")
        return

    # Validar estructura del payload
    if not isinstance(payload, dict) or 'model_cfg' not in payload:
        print("Error: archivo no reconocido o versión incompatible")
        return

    model_cfg  = payload['model_cfg']
    target_col = payload.get('target_col')
    scaler     = payload.get('scaler')

    if not isinstance(model_cfg, dict) or model_cfg.get('fitted') is None:
        print("Error: el archivo no contiene un modelo entrenado válido")
        return

    # Restaurar estado AI
    ai['model']      = model_cfg
    ai['target_col'] = target_col
    if scaler is not None:
        ai['scaler'] = scaler

    _NAMES = {'rf': 'Random Forest', 'tree': 'Árbol de decisión',
              'knn': 'KNN', 'svm': 'SVM'}
    algo_name = _NAMES.get(model_cfg['algo'], model_cfg['algo'])
    task_name = 'Clasificación' if model_cfg['task'] == 'classification' else 'Regresión'
    size_kb   = os.path.getsize(path) / 1024

    print(f"✓ Modelo cargado: {path}")
    print(f"  Algoritmo : {algo_name}  ({task_name})")
    print(f"  Variables : {', '.join(model_cfg['features'])}")
    print(f"  Objetivo  : {target_col}")
    print(f"  Tamaño    : {size_kb:.1f} KB")
    if scaler is not None:
        print(f"  Scaler    : restaurado — los datos nuevos se normalizarán igual")
    print()
    print(f"  El modelo está listo para:")
    print(f"    model-eval     — evaluar con test_set")
    print(f"    model-predict  — ver predicciones")
    print(f"    model-cv       — validación cruzada")

    ai['last_op'] = {
        'type':    'model-load',
        'data':    {'path': path, 'algo': model_cfg['algo'], 'task': model_cfg['task']},
        'metrics': {'size_kb': round(size_kb, 1)},
    }
