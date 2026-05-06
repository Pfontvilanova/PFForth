# FORTH CODE WORD: code/ai/model/modelimportance
# Muestra la importancia de cada feature en el modelo entrenado

WORD_NAME = 'model-importance'
#
# === STACK EFFECT ===
# ( -- ) Importancia de features (nativa para RF/Tree, permutación para KNN/SVM)
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


def _bar(v, width=24):
    v = max(0.0, min(1.0, v))
    filled = round(v * width)
    return '█' * filled + '░' * (width - filled)


def execute(forth):
    _ensure_ai(forth)
    ai = forth._ai

    model_cfg = ai.get('model')
    if not isinstance(model_cfg, dict) or model_cfg.get('fitted') is None:
        print("Error: modelo no entrenado — usa model-train primero")
        return

    test_df  = ai.get('test_set')
    train_df = ai.get('train_set')
    if test_df is None or train_df is None:
        print("Error: no hay split — usa data-split primero")
        return

    target   = ai.get('target_col')
    fitted   = model_cfg['fitted']
    algo     = model_cfg['algo']
    task     = model_cfg['task']
    features = model_cfg['features']

    _NAMES = {'rf': 'Random Forest', 'tree': 'Árbol de decisión',
              'knn': 'KNN', 'svm': 'SVM'}
    algo_name = _NAMES.get(algo, algo)

    print(f"=== MODEL-IMPORTANCE: {algo_name} ===")

    # ── Importancia nativa (RF y Tree) ──────────────────────────────────────
    if algo in ('rf', 'tree') and hasattr(fitted, 'feature_importances_'):
        importances = list(fitted.feature_importances_)
        method      = "impureza de Gini (nativa del modelo)"

    # ── Permutation importance (KNN y SVM) ──────────────────────────────────
    else:
        from sklearn.inspection import permutation_importance
        print("  (Calculando importancia por permutación — puede tardar unos segundos...)")

        X_test = test_df[features].fillna(test_df[features].mean())
        y_test = test_df[target]

        result      = permutation_importance(fitted, X_test, y_test,
                                             n_repeats=10, random_state=42)
        raw         = result.importances_mean
        # Normalizar a [0,1] para comparar; negativo → irrelevante → 0
        raw         = [max(0.0, v) for v in raw]
        total       = sum(raw) or 1.0
        importances = [v / total for v in raw]
        method      = "permutación (reducción de score al permutar cada feature)"

    print(f"  Método : {method}")
    print(f"  Tarea  : {'Clasificación' if task=='classification' else 'Regresión'}")
    print()

    # Ordenar de mayor a menor
    ranked = sorted(zip(importances, features), reverse=True)

    # Longitud del nombre más largo
    max_lbl = max(len(f) for f in features)

    print(f"  {'Feature':<{max_lbl}}   {'Importancia':>11}   {'':24}   Acumulado")
    print(f"  {'─'*max_lbl}   {'─'*11}   {'─'*24}   {'─'*9}")

    cumulative = 0.0
    importance_dict = {}

    for rank, (imp, feat) in enumerate(ranked, 1):
        cumulative += imp
        bar         = _bar(imp)
        marker      = ""
        if cumulative - imp < 0.80 <= cumulative:
            marker = " ← 80%"
        elif cumulative - imp < 0.90 <= cumulative:
            marker = " ← 90%"
        print(f"  {feat:<{max_lbl}}   {imp:>10.3f}   {bar}   {cumulative:>7.1%}{marker}")
        importance_dict[feat] = round(imp, 4)

    # Análisis automático
    top1_imp, top1_feat = ranked[0]
    print()
    print(f"── Interpretación ──────────────────────────────────────────────")
    print(f"  Variable más influyente : '{top1_feat}'  ({top1_imp:.1%} del peso total)")

    # Cuántas features para llegar al 80%
    cum = 0.0
    n80 = 0
    for imp, feat in ranked:
        cum += imp
        n80 += 1
        if cum >= 0.80:
            break

    if n80 == 1:
        print(f"  Solo '{ranked[0][1]}' explica el 80% — modelo muy concentrado en una variable")
    elif n80 < len(features):
        top_feats = ', '.join(f"'{f}'" for _, f in ranked[:n80])
        print(f"  {n80} variable(s) explican el 80%: {top_feats}")
    else:
        print(f"  Todas las variables contribuyen de forma similar")

    # Detectar variables irrelevantes
    threshold  = 1.0 / len(features) * 0.25   # menos del 25% de la media
    weak_feats = [feat for imp, feat in ranked if imp < threshold]
    if weak_feats:
        print(f"  Variables casi irrelevantes : {', '.join(weak_feats)}")
        print(f"  → Podrías eliminarlas con data-drop para simplificar el modelo")

    # Comparar con resultados de correlación si existen
    if (forth._ai.get('verbose') and ai.get('last_op') and
            isinstance(ai.get('last_op'), dict)):
        print()
        print("  Consejo: compara esta lista con pat-corr para ver si")
        print("  la importancia del modelo coincide con las correlaciones.")

    ai['last_op'] = {
        'type':    'model-importance',
        'data':    {'algo': algo, 'task': task, 'method': method},
        'metrics': importance_dict,
    }

    # Dejar en la pila: importancia de la variable #1 (útil para scripting)
    forth.stack.append(round(top1_imp, 4))
