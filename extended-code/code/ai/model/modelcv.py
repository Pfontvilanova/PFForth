# FORTH CODE WORD: code/ai/model/modelcv
# Validación cruzada estratificada / k-fold sobre el conjunto de entrenamiento

WORD_NAME = 'model-cv'
#
# === STACK EFFECT ===
# (   -- ) Valida con 5 pliegues (por defecto)
# ( n -- ) Valida con n pliegues
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


def _bar(v, width=16):
    v = max(0.0, min(1.0, float(v)))
    filled = round(v * width)
    return '█' * filled + '░' * (width - filled)


def _rating(score, task):
    if task == 'classification':
        if score >= 0.95: return "excelente"
        if score >= 0.85: return "bueno    "
        if score >= 0.70: return "aceptable"
        return                   "débil    "
    else:
        if score >= 0.90: return "excelente"
        if score >= 0.75: return "bueno    "
        if score >= 0.50: return "aceptable"
        return                   "débil    "


def execute(forth):
    _ensure_ai(forth)
    ai = forth._ai

    # Número de pliegues desde la pila (opcional)
    n_folds = 5
    if forth.stack and isinstance(forth.stack[-1], int) and 2 <= forth.stack[-1] <= 20:
        n_folds = forth.stack.pop()

    model_cfg = ai.get('model')
    if not isinstance(model_cfg, dict) or model_cfg.get('fitted') is None:
        print("Error: modelo no entrenado — usa model-train primero")
        return

    # Priorizar train_set; si no hay split, usar dataset completo
    source_df = ai.get('train_set')
    if source_df is None:
        source_df = ai.get('dataset')
    if source_df is None:
        print("Error: no hay datos — usa data-load y data-split primero")
        return

    target   = ai.get('target_col')
    fitted   = model_cfg['fitted']
    algo     = model_cfg['algo']
    task     = model_cfg['task']
    features = model_cfg['features']

    missing = [f for f in features if f not in source_df.columns]
    if missing:
        print(f"Error: columnas ausentes: {', '.join(missing)}")
        return

    X = source_df[features].fillna(source_df[features].mean())
    y = source_df[target]

    if len(X) < n_folds * 2:
        print(f"Error: muy pocos datos ({len(X)}) para {n_folds} pliegues")
        print(f"  Reduce n_folds o usa más datos")
        return

    # Reconstruir un estimador fresco (sin el fit anterior) para CV pura
    from sklearn.base import clone
    from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
    import numpy as np

    estimator = clone(fitted)

    if task == 'classification':
        cv      = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
        scoring = 'accuracy'
        label   = 'Accuracy'
    else:
        cv      = KFold(n_splits=n_folds, shuffle=True, random_state=42)
        scoring = 'r2'
        label   = 'R²'

    _NAMES = {'rf': 'Random Forest', 'tree': 'Árbol de decisión',
              'knn': 'KNN', 'svm': 'SVM'}
    algo_name = _NAMES.get(algo, algo)
    source    = "train_set" if ai.get('train_set') is not None else "dataset completo"


    print(f"=== MODEL-CV: {algo_name} — {n_folds} pliegues ===")
    print(f"  Datos   : {source}  ({len(X)} filas)")
    print(f"  Métrica : {label}")
    print(f"  Nota    : el test_set queda reservado para model-eval final")
    print()

    scores = cross_val_score(estimator, X, y, cv=cv, scoring=scoring)

    mean_s = float(np.mean(scores))
    std_s  = float(np.std(scores))
    ci_lo  = mean_s - 1.96 * std_s
    ci_hi  = mean_s + 1.96 * std_s

    print(f"  {'Pliegue':>8}   {label:>8}   {'':16}")
    print(f"  {'─'*8}   {'─'*8}   {'─'*16}")

    for i, s in enumerate(scores, 1):
        bar    = _bar(max(0, s))
        marker = " ← peor" if s == scores.min() else (" ← mejor" if s == scores.max() else "")
        print(f"  {i:>8}   {s:>8.3f}   {bar}{marker}")

    print(f"  {'─'*8}   {'─'*8}   {'─'*16}")
    print(f"  {'Media':>8}   {mean_s:>8.3f}   {_bar(max(0,mean_s))}  {_rating(mean_s, task)}")
    print(f"  {'Std':>8}   {std_s:>8.3f}")
    print()

    print(f"  Intervalo de confianza 95%: [{ci_lo:.3f},  {ci_hi:.3f}]")
    print(f"  → Con datos nuevos, espera {label} entre "
          f"{max(0,ci_lo):.3f} y {min(1,ci_hi):.3f}")

    # Variabilidad alta
    cv_pct = std_s / mean_s * 100 if mean_s > 0 else 0
    if cv_pct > 15:
        print()
        print(f"  ⚠ Alta variabilidad entre pliegues ({cv_pct:.0f}%)")
        print(f"    El rendimiento depende mucho de qué datos se usan para entrenar")
        print(f"    Posibles causas: dataset pequeño, clase desbalanceada o datos ruidosos")
    elif cv_pct < 5:
        print(f"  ✓ Rendimiento consistente entre pliegues ({cv_pct:.1f}% variación)")

    # Comparar con el score de model-train si existe en last_op
    last = ai.get('last_op') or {}
    if last.get('type') == 'model-train' and last.get('metrics'):
        train_score = last['metrics'].get('train_score') or last['metrics'].get('train_r2')
        if train_score:
            gap = train_score - mean_s
            print()
            print(f"  Score en train completo : {train_score:.3f}")
            print(f"  Score CV medio          : {mean_s:.3f}   (diferencia: {gap:+.3f})")
            if gap > 0.15:
                print(f"  ⚠ Gran diferencia — el modelo se ajusta demasiado a los datos")
            elif gap < 0.03:
                print(f"  ✓ Diferencia pequeña — buen equilibrio bias/varianza")

    if forth._ai.get('verbose'):
        print()
        print("  Validación cruzada = el dataset de entrenamiento se divide en")
        print(f"  {n_folds} partes; se entrena con {n_folds-1} y se evalúa con 1, {n_folds} veces.")
        print("  Así obtenemos una estimación más robusta que un solo train/test.")

    ai['last_op'] = {
        'type': 'model-cv',
        'data': {'algo': algo, 'task': task, 'n_folds': n_folds,
                 'scores': [round(s, 4) for s in scores.tolist()]},
        'metrics': {'mean': round(mean_s, 4), 'std': round(std_s, 4),
                    'ci_lo': round(ci_lo, 4), 'ci_hi': round(ci_hi, 4)},
    }

    forth.stack.append(round(mean_s, 4))
