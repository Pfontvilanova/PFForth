# FORTH CODE WORD: code/ai/model/modeltrain
# Entrena el modelo configurado con el conjunto de entrenamiento

WORD_NAME = 'model-train'
#
# === STACK EFFECT ===
# ( -- ) Entrena el modelo activo con train_set
# === FIN ===

import time


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {
            'dataset': None, 'target_col': None,
            'train_set': None, 'test_set': None,
            'model': None, 'last_op': None,
            'verbose': False, 'image': None,
            'audio': None, 'clip_model': None, 'yolo_model': None,
        }


def _make_sklearn_model(algo, task, params, n_train):
    """Crea el objeto sklearn según algoritmo y tarea."""
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.tree   import DecisionTreeClassifier, DecisionTreeRegressor
    from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
    from sklearn.svm    import SVC, SVR

    if algo == 'rf':
        cls = RandomForestClassifier if task == 'classification' else RandomForestRegressor
        return cls(**{k: v for k, v in params.items()
                      if k in ('n_estimators', 'random_state', 'max_depth')})

    if algo == 'tree':
        cls = DecisionTreeClassifier if task == 'classification' else DecisionTreeRegressor
        return cls(**{k: v for k, v in params.items()
                      if k in ('max_depth', 'random_state')})

    if algo == 'knn':
        # Ajustar k si el dataset es muy pequeño
        k = params.get('n_neighbors', 5)
        k = min(k, max(1, n_train - 1))
        cls = KNeighborsClassifier if task == 'classification' else KNeighborsRegressor
        return cls(n_neighbors=k)

    if algo == 'svm':
        p = {k: v for k, v in params.items() if k in ('C', 'kernel')}
        if task == 'classification':
            return SVC(**p, probability=True)
        else:
            return SVR(**p)

    raise ValueError(f"Algoritmo desconocido: {algo}")


def execute(forth):
    _ensure_ai(forth)
    ai = forth._ai

    # Validaciones
    model_cfg = ai.get('model')
    if model_cfg is None:
        print("Error: no hay modelo configurado")
        print("  Usa: rf-model / tree-model / knn-model / svm-model")
        return

    if isinstance(model_cfg, dict) and model_cfg.get('fitted') is not None:
        algo = model_cfg.get('algo', '?')
        print(f"  (reentrenando {algo}-model con los datos actuales)")

    train_df = ai.get('train_set')
    if train_df is None:
        print("Error: no hay conjunto de entrenamiento")
        print("  Usa: 0.2 data-split  antes de entrenar")
        return

    target = ai.get('target_col')
    if target is None:
        print("Error: no hay columna objetivo definida")
        print("  Usa: s\" columna\" data-target")
        return

    if target not in train_df.columns:
        print(f"Error: columna objetivo '{target}' no está en el dataset")
        return

    # Detectar tarea
    n_unique = train_df[target].nunique()
    task = 'classification' if n_unique <= 10 else 'regression'

    # Extraer features numéricas (excluye objetivo y columnas de texto)
    feature_cols = [c for c in train_df.select_dtypes(include='number').columns
                    if c != target]

    if not feature_cols:
        print("Error: no hay columnas numéricas para entrenar (aparte del objetivo)")
        print("  Comprueba que has hecho data-norm o que existen variables numéricas")
        return

    # Avisar de columnas ignoradas
    all_cols   = [c for c in train_df.columns if c != target]
    ignored    = [c for c in all_cols if c not in feature_cols]
    if ignored:
        print(f"  Aviso: columnas de texto ignoradas: {', '.join(ignored)}")

    X_train = train_df[feature_cols].fillna(train_df[feature_cols].mean())
    y_train = train_df[target]

    # Crear y entrenar el modelo
    algo   = model_cfg['algo']
    params = model_cfg.get('params', {})

    try:
        fitted = _make_sklearn_model(algo, task, params, len(X_train))
        t0     = time.time()
        fitted.fit(X_train, y_train)
        elapsed = time.time() - t0
    except Exception as e:
        print(f"Error al entrenar: {e}")
        return

    # Guardar modelo entrenado
    ai['model'] = {
        'algo':     algo,
        'fitted':   fitted,
        'task':     task,
        'features': feature_cols,
        'params':   params,
    }

    # Puntuación sobre entrenamiento
    train_score = fitted.score(X_train, y_train)

    # Nombres legibles
    _NAMES = {
        'rf':   'Random Forest',
        'tree': 'Árbol de decisión',
        'knn':  'KNN',
        'svm':  'SVM',
    }
    algo_name = _NAMES.get(algo, algo)
    task_name = 'Clasificación' if task == 'classification' else 'Regresión'

    print(f"✓ Entrenamiento completado")
    print(f"  Algoritmo   : {algo_name}")
    print(f"  Tarea       : {task_name}")
    print(f"  Variables   : {len(feature_cols)}  ({', '.join(feature_cols[:4])}"
          f"{'...' if len(feature_cols) > 4 else ''})")
    print(f"  Filas train : {len(X_train)}")
    print(f"  Tiempo      : {elapsed*1000:.1f} ms")

    if task == 'classification':
        print(f"  Score train : {train_score:.3f}  (accuracy en entrenamiento)")
        if train_score > 0.99 and len(X_train) < 50:
            print("  Aviso: accuracy 1.0 en dataset pequeño puede indicar sobreajuste")
            print("         Comprueba model-eval con el conjunto de prueba")
    else:
        print(f"  R² train    : {train_score:.3f}")
        if train_score < 0:
            print("  Aviso: R² negativo — el modelo es peor que predecir la media")

    if forth._ai.get('verbose'):
        print()
        print(f"  El modelo ha aprendido de {len(X_train)} ejemplos.")
        print(f"  Ahora usa model-eval para ver su rendimiento real")
        print(f"  con los {len(ai.get('test_set', []))} ejemplos de prueba.")

    ai['last_op'] = {
        'type': 'model-train',
        'data': {
            'algo':     algo,
            'task':     task,
            'features': feature_cols,
            'n_train':  len(X_train),
        },
        'metrics': {
            'train_score': round(train_score, 4),
            'elapsed_ms':  round(elapsed * 1000, 1),
        },
    }
