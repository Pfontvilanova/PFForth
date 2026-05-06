# FORTH CODE WORD: code/ai/model/modelmatrix
# Muestra la matriz de confusión (clasificación) o distribución de errores (regresión)

WORD_NAME = 'model-matrix'
#
# === STACK EFFECT ===
# ( -- ) Matriz de confusión para clasificación; histograma de errores para regresión
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


def _bar(v, total, width=20):
    if total == 0:
        return '░' * width
    filled = round(v / total * width)
    return '█' * filled + '░' * (width - filled)


def _confusion_matrix_ascii(cm, labels):
    """Dibuja la matriz de confusión en texto."""
    n = len(labels)
    cell  = max(6, max(len(str(l)) for l in labels) + 2)
    lbl_w = max(8, max(len(str(l)) for l in labels) + 2)
    sep   = '─' * (lbl_w + 8 + n * (cell + 2))

    col_header = '  '.join(("{:" + "^" + str(cell) + "}").format(str(l)) for l in labels)
    print(("          {:^" + str(n * (cell + 2)) + "}").format("Predicho"))
    print("          " + col_header)
    print("  " + sep)

    for i, true_lbl in enumerate(labels):
        parts = []
        for j in range(n):
            raw = "[ " + str(cm[i][j]) + " ]" if i == j else str(cm[i][j])
            parts.append(("{:" + "^" + str(cell) + "}").format(raw))
        row_vals = '  '.join(parts)
        prefix   = "Real " + str(true_lbl) if i == 0 else "     " + str(true_lbl)
        print(("  {:<" + str(lbl_w + 8) + "}{}").format(prefix, row_vals))

    print("  " + sep)


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

    _NAMES = {'rf': 'Random Forest', 'tree': 'Árbol de decisión',
              'knn': 'KNN', 'svm': 'SVM'}
    algo_name = _NAMES.get(model_cfg['algo'], model_cfg['algo'])

    if task == 'classification':
        from sklearn.metrics import confusion_matrix

        labels   = sorted(set(y_real) | set(y_pred))
        cm       = confusion_matrix(y_real, y_pred, labels=labels)
        n        = len(labels)
        total    = len(y_real)
        correct  = int(cm.trace())

        print(f"=== MODEL-MATRIX: {algo_name} ===")
        print(f"  Clases : {labels}")
        print(f"  Total  : {total} ejemplos de prueba")
        print()

        _confusion_matrix_ascii(cm.tolist(), labels)
        print()
        print("  [ N ] = diagonal = predicciones correctas")
        print("  resto = errores (fila=real, columna=predicho)")
        print()

        if n == 2:
            # Análisis binario completo
            tn, fp, fn, tp = cm.ravel()
            print(f"── Análisis binario ─────────────────────────────────")
            print(f"  Verdaderos Positivos (TP) : {tp:>4}  — predijo '{labels[1]}' y era '{labels[1]}'")
            print(f"  Verdaderos Negativos (TN) : {tn:>4}  — predijo '{labels[0]}' y era '{labels[0]}'")
            print(f"  Falsos Positivos     (FP) : {fp:>4}  — predijo '{labels[1]}' pero era '{labels[0]}'")
            print(f"  Falsos Negativos     (FN) : {fn:>4}  — predijo '{labels[0]}' pero era '{labels[1]}'")
            print()

            sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
            precision   = tp / (tp + fp) if (tp + fp) > 0 else 0
            npv         = tn / (tn + fn) if (tn + fn) > 0 else 0

            print(f"  Sensibilidad  : {sensitivity:.3f}  {_bar(sensitivity*100,100,12)}")
            print(f"    (recall de '{labels[1]}': detecta el {sensitivity*100:.0f}% de los casos positivos)")
            print(f"  Especificidad : {specificity:.3f}  {_bar(specificity*100,100,12)}")
            print(f"    (recall de '{labels[0]}': descarta el {specificity*100:.0f}% de los negativos)")
            print(f"  Precisión     : {precision:.3f}  {_bar(precision*100,100,12)}")
            print(f"    (cuando dice '{labels[1]}', acierta el {precision*100:.0f}% de las veces)")
            print(f"  VPN           : {npv:.3f}  {_bar(npv*100,100,12)}")
            print(f"    (cuando dice '{labels[0]}', acierta el {npv*100:.0f}% de las veces)")

            if fp > fn:
                print()
                print(f"  ⚠ El modelo tiende a generar más Falsos Positivos ({fp})")
                print(f"    — avisa de '{labels[1]}' cuando en realidad era '{labels[0]}'")
            elif fn > fp:
                print()
                print(f"  ⚠ El modelo tiende a generar más Falsos Negativos ({fn})")
                print(f"    — falla en detectar '{labels[1]}' reales")

            metrics = {
                'tp': int(tp), 'tn': int(tn), 'fp': int(fp), 'fn': int(fn),
                'sensitivity': round(sensitivity, 4),
                'specificity': round(specificity, 4),
                'precision':   round(precision, 4),
            }
        else:
            # Multiclase: precisión y recall por clase
            print(f"── Precisión y Recall por clase ─────────────────────")
            metrics = {}
            for i, lbl in enumerate(labels):
                tp_i = int(cm[i, i])
                fp_i = int(cm[:, i].sum() - tp_i)
                fn_i = int(cm[i, :].sum() - tp_i)
                prec_i = tp_i / (tp_i + fp_i) if (tp_i + fp_i) > 0 else 0
                rec_i  = tp_i / (tp_i + fn_i) if (tp_i + fn_i) > 0 else 0
                print(f"  Clase {str(lbl):>6} — Precisión: {prec_i:.3f}  "
                      f"Recall: {rec_i:.3f}  {_bar(rec_i*100,100,10)}")
                metrics[str(lbl)] = {'precision': round(prec_i, 4),
                                     'recall': round(rec_i, 4)}

        print()
        print(f"  Accuracy global : {correct}/{total} = {correct/total:.3f}")

        if forth._ai.get('verbose'):
            print()
            print("  Cómo leer la matriz:")
            print("  • Cada fila representa la clase REAL")
            print("  • Cada columna representa lo que el modelo PREDIJO")
            print("  • La diagonal principal ([ N ]) son los aciertos")
            print("  • Los errores están fuera de la diagonal")

        ai['last_op'] = {
            'type': 'model-matrix',
            'data': {'algo': model_cfg['algo'], 'task': task, 'labels': labels},
            'metrics': metrics,
        }

    else:  # regression — distribución de errores
        import numpy as np

        errors = [p - r for r, p in zip(y_real, y_pred)]
        abs_e  = [abs(e) for e in errors]
        mean_e = float(np.mean(errors))
        std_e  = float(np.std(errors))
        mae    = float(np.mean(abs_e))
        n_bins = min(8, len(errors))

        print(f"=== MODEL-MATRIX: {algo_name} (distribución de errores) ===")
        print(f"  Errores = predicho − real  ({len(errors)} ejemplos)")
        print()

        # Histograma manual de errores
        mn, mx = min(errors), max(errors)
        rng    = mx - mn if mx != mn else 1.0
        bin_w  = rng / n_bins
        bins   = [0] * n_bins

        for e in errors:
            idx = min(int((e - mn) / bin_w), n_bins - 1)
            bins[idx] += 1

        max_count = max(bins) if bins else 1
        bar_w     = 16

        print("  Distribución de errores (predicho − real):")
        for i, count in enumerate(bins):
            lo  = mn + i * bin_w
            hi  = lo + bin_w
            bar = '█' * round(count / max_count * bar_w)
            mid = (lo + hi) / 2
            print(f"  {mid:>+8.3g}  {bar:<{bar_w}}  {count}")

        print()
        sesgo = "sin sesgo aparente"
        if mean_e > std_e * 0.5:
            sesgo = f"sesgo positivo (sobreestima en {mean_e:+.3g} de media)"
        elif mean_e < -std_e * 0.5:
            sesgo = f"sesgo negativo (subestima en {mean_e:+.3g} de media)"

        print(f"  Media  : {mean_e:+.4g}   ({sesgo})")
        print(f"  Std    : {std_e:.4g}")
        print(f"  MAE    : {mae:.4g}")

        # Errores centrados en 0?
        pct_ok = sum(1 for e in abs_e if e < mae) / len(abs_e) * 100
        print(f"  {pct_ok:.0f}% de predicciones con error < {mae:.3g}")

        ai['last_op'] = {
            'type': 'model-matrix',
            'data': {'algo': model_cfg['algo'], 'task': task},
            'metrics': {'mean_error': round(mean_e, 4), 'std': round(std_e, 4),
                        'mae': round(mae, 4)},
        }
