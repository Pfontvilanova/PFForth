# FORTH CODE WORD: code/ai/model/modeleval
# Evalúa el modelo entrenado sobre el conjunto de prueba

WORD_NAME = 'model-eval'
#
# === STACK EFFECT ===
# ( -- ) Muestra métricas en test_set; deja score en la pila
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


def _rating(score, task):
    """Etiqueta cualitativa del score."""
    if task == 'classification':
        if score >= 0.95: return "excelente"
        if score >= 0.85: return "bueno    "
        if score >= 0.70: return "aceptable"
        if score >= 0.55: return "débil    "
        return                   "muy débil"
    else:   # regression R²
        if score >= 0.90: return "excelente"
        if score >= 0.75: return "bueno    "
        if score >= 0.50: return "aceptable"
        if score >= 0.20: return "débil    "
        return                   "muy débil"


def _bar(v, width=16):
    v = max(0.0, min(1.0, v))
    filled = round(v * width)
    return '█' * filled + '░' * (width - filled)


def execute(forth):
    _ensure_ai(forth)
    ai = forth._ai

    # Validaciones
    model_cfg = ai.get('model')
    if not isinstance(model_cfg, dict) or model_cfg.get('fitted') is None:
        print("Error: modelo no entrenado — usa model-train primero")
        return

    test_df = ai.get('test_set')
    if test_df is None:
        print("Error: no hay conjunto de prueba — usa data-split primero")
        return

    target   = ai.get('target_col')
    fitted   = model_cfg['fitted']
    task     = model_cfg['task']
    features = model_cfg['features']

    # Verificar features disponibles en test
    missing = [f for f in features if f not in test_df.columns]
    if missing:
        print(f"Error: columnas ausentes en test: {', '.join(missing)}")
        return

    X_test = test_df[features].fillna(test_df[features].mean())
    y_test = test_df[target]
    y_pred = fitted.predict(X_test)

    _NAMES = {'rf': 'Random Forest', 'tree': 'Árbol de decisión',
              'knn': 'KNN', 'svm': 'SVM'}
    algo_name = _NAMES.get(model_cfg['algo'], model_cfg['algo'])

    print(f"=== MODEL-EVAL: {algo_name} ===")
    print(f"  Tarea       : {'Clasificación' if task=='classification' else 'Regresión'}")
    print(f"  Filas test  : {len(X_test)}")
    print()

    metrics = {}

    if task == 'classification':
        from sklearn.metrics import (accuracy_score, f1_score,
                                     precision_score, recall_score,
                                     classification_report)

        acc  = accuracy_score(y_test, y_pred)
        f1   = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec  = recall_score(y_test, y_pred, average='weighted', zero_division=0)

        print(f"── Métricas de clasificación ──────────────────────────")
        print(f"  Accuracy   {acc:.3f}  {_bar(acc)}  {_rating(acc, task)}")
        print(f"  F1         {f1:.3f}  {_bar(f1)}")
        print(f"  Precisión  {prec:.3f}  {_bar(prec)}")
        print(f"  Recall     {rec:.3f}  {_bar(rec)}")
        print()
        print(f"  Accuracy  = de cada 100 predicciones, acierta ~{acc*100:.0f}")
        print(f"  Precisión = cuando dice 'sí', acierta el {prec*100:.0f}%")
        print(f"  Recall    = de los 'sí' reales, detecta el {rec*100:.0f}%")

        # Comparar con train score
        X_train  = ai['train_set'][features].fillna(ai['train_set'][features].mean())
        y_train  = ai['train_set'][target]
        train_acc = fitted.score(X_train, y_train)
        gap       = train_acc - acc

        print()
        print(f"── Comparación train vs test ───────────────────────────")
        print(f"  Train : {train_acc:.3f}   Test : {acc:.3f}   "
              f"Diferencia : {gap:+.3f}")
        if gap > 0.15:
            print(f"  ⚠ Sobreajuste probable (gap > 0.15)")
            print(f"    El modelo memoriza los datos de entrenamiento")
            print(f"    Prueba: tree-model con max_depth limitado")
        elif gap < 0.02:
            print(f"  ✓ Sin sobreajuste aparente")

        # Detalle por clase si verbose
        if forth._ai.get('verbose'):
            print()
            print("── Detalle por clase ──────────────────────────────────")
            report = classification_report(y_test, y_pred, zero_division=0)
            for line in report.split('\n'):
                if line.strip():
                    print(f"  {line}")

        metrics = {'accuracy': round(acc, 4), 'f1': round(f1, 4),
                   'precision': round(prec, 4), 'recall': round(rec, 4),
                   'train_acc': round(train_acc, 4)}
        forth.stack.append(round(acc, 4))

    else:  # regression
        import numpy as np
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

        mse  = mean_squared_error(y_test, y_pred)
        rmse = float(np.sqrt(mse))
        mae  = mean_absolute_error(y_test, y_pred)
        r2   = r2_score(y_test, y_pred)
        r2c  = max(0.0, r2)

        print(f"── Métricas de regresión ──────────────────────────────")
        print(f"  R²    {r2:.3f}   {_bar(r2c)}  {_rating(r2, task)}")
        print(f"  RMSE  {rmse:.4g}  (error típico en las mismas unidades)")
        print(f"  MAE   {mae:.4g}  (error medio absoluto)")
        print()
        print(f"  R²   = {r2*100:.0f}% de la variabilidad explicada por el modelo")
        print(f"  RMSE = en promedio el modelo se equivoca ±{rmse:.3g} unidades")

        X_train   = ai['train_set'][features].fillna(ai['train_set'][features].mean())
        y_train   = ai['train_set'][target]
        train_r2  = fitted.score(X_train, y_train)
        gap       = train_r2 - r2

        print()
        print(f"── Comparación train vs test ───────────────────────────")
        print(f"  Train R² : {train_r2:.3f}   Test R² : {r2:.3f}   "
              f"Diferencia : {gap:+.3f}")
        if gap > 0.20:
            print(f"  ⚠ Sobreajuste probable (gap > 0.20)")
        elif gap < 0.05:
            print(f"  ✓ Sin sobreajuste aparente")

        metrics = {'r2': round(r2, 4), 'rmse': round(rmse, 4),
                   'mae': round(mae, 4), 'train_r2': round(train_r2, 4)}
        forth.stack.append(round(r2, 4))

    ai['last_op'] = {
        'type':    'model-eval',
        'data':    {'algo': model_cfg['algo'], 'task': task},
        'metrics': metrics,
    }
