# FORTH CODE WORD: code/ai/model/modelpredict
# Genera y muestra predicciones sobre el conjunto de prueba

WORD_NAME = 'model-predict'
#
# === STACK EFFECT ===
# ( -- ) Muestra tabla real vs predicho para el test_set
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


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.3g}"
    return str(v)


def execute(forth):
    _ensure_ai(forth)
    ai = forth._ai

    model_cfg = ai.get('model')
    if not isinstance(model_cfg, dict) or model_cfg.get('fitted') is None:
        print("Error: modelo no entrenado — usa model-train primero")
        return

    test_df  = ai.get('test_set')
    if test_df is None:
        print("Error: no hay conjunto de prueba — usa data-split primero")
        return

    target   = ai.get('target_col')
    fitted   = model_cfg['fitted']
    task     = model_cfg['task']
    features = model_cfg['features']

    X_test = test_df[features].fillna(test_df[features].mean())
    y_real = list(test_df[target])
    y_pred = list(fitted.predict(X_test))

    # Probabilidades si el modelo las soporta (clasificación)
    has_proba = task == 'classification' and hasattr(fitted, 'predict_proba')
    if has_proba:
        try:
            proba = fitted.predict_proba(X_test)
            classes = list(fitted.classes_)
        except Exception:
            has_proba = False

    _NAMES = {'rf': 'Random Forest', 'tree': 'Árbol de decisión',
              'knn': 'KNN', 'svm': 'SVM'}
    algo_name = _NAMES.get(model_cfg['algo'], model_cfg['algo'])

    print(f"=== MODEL-PREDICT: {algo_name} ({len(y_real)} ejemplos de prueba) ===")
    print()

    if task == 'classification':
        # Tabla: fila | real | pred | correcto | confianza
        n_ok  = sum(1 for r, p in zip(y_real, y_pred) if r == p)
        n_err = len(y_real) - n_ok

        if has_proba:
            print(f"  {'#':>3}  {'Real':>8}  {'Pred':>8}  {'OK':>4}  {'Confianza':>10}")
            print(f"  {'─'*3}  {'─'*8}  {'─'*8}  {'─'*4}  {'─'*10}")
        else:
            print(f"  {'#':>3}  {'Real':>8}  {'Pred':>8}  {'OK':>4}")
            print(f"  {'─'*3}  {'─'*8}  {'─'*8}  {'─'*4}")

        for i, (r, p) in enumerate(zip(y_real, y_pred)):
            ok  = "✓" if r == p else "✗"
            if has_proba:
                # Confianza en la clase predicha
                pred_idx = classes.index(p)
                conf     = proba[i][pred_idx]
                conf_bar = '█' * round(conf * 8) + '░' * (8 - round(conf * 8))
                print(f"  {i+1:>3}  {_fmt(r):>8}  {_fmt(p):>8}  {ok:>4}  "
                      f"{conf:.2f} {conf_bar}")
            else:
                print(f"  {i+1:>3}  {_fmt(r):>8}  {_fmt(p):>8}  {ok:>4}")

        print()
        print(f"  Correctos : {n_ok}/{len(y_real)}  "
              f"({100*n_ok/len(y_real):.0f}%)")
        if n_err:
            print(f"  Errores   : {n_err}/{len(y_real)}  "
                  f"({100*n_err/len(y_real):.0f}%)")
            # Mostrar los casos fallidos
            errors = [(i+1, y_real[i], y_pred[i])
                      for i in range(len(y_real)) if y_real[i] != y_pred[i]]
            print(f"  Fallos    : filas {', '.join(str(e[0]) for e in errors)}")

        ai['last_op'] = {
            'type': 'model-predict',
            'data': {'task': task, 'n': len(y_real),
                     'y_real': y_real, 'y_pred': y_pred},
            'metrics': {'n_correct': n_ok, 'n_error': n_err,
                        'accuracy': round(n_ok/len(y_real), 4)},
        }

    else:  # regression
        import numpy as np

        errors_abs = [abs(r - p) for r, p in zip(y_real, y_pred)]
        mean_err   = float(np.mean(errors_abs))
        max_err    = float(np.max(errors_abs))

        print(f"  {'#':>3}  {'Real':>10}  {'Predicho':>10}  {'Error':>10}  {'%error':>8}")
        print(f"  {'─'*3}  {'─'*10}  {'─'*10}  {'─'*10}  {'─'*8}")

        for i, (r, p) in enumerate(zip(y_real, y_pred)):
            err    = p - r
            pct    = abs(err) / abs(r) * 100 if r != 0 else 0
            sign   = '+' if err >= 0 else ''
            marker = " ← mayor error" if abs(err) == max_err else ""
            print(f"  {i+1:>3}  {_fmt(r):>10}  {_fmt(p):>10}  "
                  f"{sign}{_fmt(err):>10}  {pct:>7.1f}%{marker}")

        print()
        print(f"  Error medio : {mean_err:.4g}")
        print(f"  Error máx.  : {max_err:.4g}")

        # Tendencia: ¿sobreestima o subestima?
        bias = float(np.mean([p - r for r, p in zip(y_real, y_pred)]))
        if abs(bias) > mean_err * 0.3:
            direction = "sobreestima" if bias > 0 else "subestima"
            print(f"  Sesgo medio : {bias:+.4g}  (el modelo {direction} sistemáticamente)")

        ai['last_op'] = {
            'type': 'model-predict',
            'data': {'task': task, 'n': len(y_real),
                     'y_real': y_real, 'y_pred': [round(p, 4) for p in y_pred]},
            'metrics': {'mean_abs_error': round(mean_err, 4),
                        'max_abs_error': round(max_err, 4),
                        'bias': round(bias, 4)},
        }

    if forth._ai.get('verbose'):
        print()
        print("  Estas predicciones se han obtenido con el conjunto de prueba,")
        print("  datos que el modelo NO vio durante el entrenamiento.")
        print("  Por eso reflejan el rendimiento real esperado con datos nuevos.")
