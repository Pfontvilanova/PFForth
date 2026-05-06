"""Motor rule-based de explicaciones para el módulo AI de PFForth.
Importado por explain.py, aiwhy.py y ainext.py desde el mismo directorio."""


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _algo_name(algo):
    return {'rf': 'Random Forest', 'tree': 'Árbol de decisión',
            'knn': 'K-Vecinos (KNN)', 'svm': 'SVM'}.get(algo, algo.upper())


def _score_label(score, task):
    if task == 'classification':
        if score >= 0.95: return "excelente"
        if score >= 0.85: return "bueno"
        if score >= 0.70: return "aceptable"
        return "bajo"
    else:
        if score >= 0.90: return "excelente"
        if score >= 0.75: return "bueno"
        if score >= 0.50: return "aceptable"
        return "bajo"


def _silhouette_label(sil):
    if sil >= 0.70: return "excelente"
    if sil >= 0.50: return "bueno"
    if sil >= 0.30: return "regular"
    return "débil"


def _sep(title):
    line = "─" * max(0, 46 - len(title))
    print(f"── {title} {line}")


def _top_importance(metrics):
    """Devuelve (nombre, valor) del feature más importante en metrics."""
    if not metrics:
        return None, 0.0
    top = max(metrics.items(), key=lambda kv: kv[1])
    return top


# ─────────────────────────────────────────────────────────────────────────────
# EXPLAIN — narra lo que ocurrió
# ─────────────────────────────────────────────────────────────────────────────

def _ex_data_load(d, m):
    print(f"  Se cargó '{d.get('filename', '?')}' con {m.get('rows', '?')} filas "
          f"y {m.get('cols', '?')} columnas.")
    print(f"  El estado anterior (target, conjuntos, modelo) fue reiniciado.")


def _ex_data_fill(d, m):
    total = m.get('total_filled', 0)
    if total == 0:
        print("  No se encontraron valores nulos — el dataset ya estaba completo.")
    else:
        print(f"  Se rellenaron {total} valores nulos con la estrategia '{d.get('strategy', '?')}'.")
        filled = d.get('filled', {})
        if filled and len(filled) <= 6:
            for col, val in filled.items():
                print(f"    '{col}' → {val} nulos rellenados")


def _ex_data_norm(d, m):
    n = m.get('n_normalized', 0)
    cols = d.get('columns', [])
    print(f"  Se normalizaron {n} columnas al rango [0, 1].")
    if cols and len(cols) <= 6:
        print(f"  Columnas: {', '.join(cols)}")
    elif cols:
        print(f"  Columnas: {', '.join(cols[:5])} … (+{len(cols)-5} más)")


def _ex_data_split(d, m):
    ratio = d.get('ratio', 0.2)
    strat = d.get('strategy', '')
    target = d.get('target', '')
    n_train = m.get('n_train', '?')
    n_test  = m.get('n_test', '?')
    n_total = m.get('n_total', '?')
    pct_train = int(round((1 - ratio) * 100))
    pct_test  = int(round(ratio * 100))
    print(f"  Dataset dividido: {n_total} ejemplos totales.")
    print(f"    Entrenamiento : {n_train} ejemplos ({pct_train}%)")
    print(f"    Prueba        : {n_test} ejemplos ({pct_test}%)")
    if strat:
        print(f"    Estrategia    : {strat}")
    if target:
        print(f"    Variable obj. : {target}")


def _ex_pat_find(d, m):
    n_num  = m.get('n_numeric', len(d.get('numeric_cols', [])))
    n_txt  = len(d.get('text_cols', []))
    nulls  = d.get('total_nulls', 0)
    print(f"  Análisis estadístico del dataset:")
    print(f"    {n_num} variables numéricas, {n_txt} de texto")
    print(f"    {nulls} valores nulos en total" if nulls else "    Sin valores nulos")


def _ex_pat_corr(d, m):
    n_pairs = m.get('n_high_pairs', 0)
    n_num   = m.get('n_numeric', '?')
    target  = d.get('target')
    print(f"  Correlaciones calculadas entre {n_num} variables numéricas.")
    print(f"  {n_pairs} par(es) con correlación alta (|r| > 0.80).")
    if target:
        print(f"  Correlaciones con variable objetivo '{target}' incluidas.")


def _ex_pat_cluster(d, m):
    n   = d.get('n_clusters', '?')
    sil = m.get('silhouette', 0.0)
    lbl = _silhouette_label(sil)
    sizes = d.get('sizes', [])
    print(f"  Agrupación K-Means en {n} clusters. Calidad silhouette: {sil:.3f} ({lbl}).")
    if sizes:
        parts = [f"cluster {i}→{s}" for i, s in enumerate(sizes)]
        print(f"  Tamaños: {', '.join(parts)}")
    feats = d.get('features', [])
    if feats and len(feats) <= 5:
        print(f"  Variables usadas: {', '.join(feats)}")


def _ex_pat_pca(d, m):
    n     = m.get('n_components', '?')
    total = m.get('total_variance', 0.0)
    var   = d.get('variance', [])
    comps = d.get('components', [])
    print(f"  PCA con {n} componentes. Varianza total explicada: {total:.1%}.")
    if var and comps:
        for name, v in zip(comps[:5], var[:5]):
            print(f"    {name}: {v:.1%}")


def _ex_pat_anomaly(d, m):
    n_tot = m.get('n_total', '?')
    n_ano = m.get('n_anomaly', 0)
    cont  = d.get('contamination', 0.0)
    pct   = n_ano / n_tot if isinstance(n_tot, int) and n_tot > 0 else 0.0
    print(f"  Detección de anomalías: {n_ano} anómalos de {n_tot} ({pct:.1%}).")
    print(f"  Contaminación configurada: {cont:.1%}.")
    print(f"  Columna 'anomalia' añadida al dataset (1=normal, -1=anómalo).")


def _ex_pat_sequence(d, m):
    col   = d.get('column', '?')
    n     = d.get('n', '?')
    trend = d.get('trend', '?')
    cv    = m.get('cv_pct', 0.0)
    ac1   = m.get('ac1', 0.0)
    print(f"  Análisis de serie temporal en '{col}' ({n} puntos).")
    print(f"  Tendencia: {trend}.  Variación relativa: {cv:.1f}%.  Autocorr(1): {ac1:.3f}.")


def _ex_model_train(d, m):
    algo  = _algo_name(d.get('algo', '?'))
    task  = d.get('task', '?')
    n     = d.get('n_train', '?')
    score = m.get('train_score', 0.0)
    lbl   = _score_label(score, task)
    ms    = m.get('elapsed_ms', 0.0)
    print(f"  Entrenamiento de {algo} para {task}.")
    print(f"  {n} ejemplos de entrenamiento. Score en train: {score:.3f} ({lbl}).")
    print(f"  Tiempo: {ms:.0f} ms.")


def _ex_model_eval(d, m):
    algo = _algo_name(d.get('algo', '?'))
    task = d.get('task', '?')
    print(f"  Evaluación de {algo} con el conjunto de prueba:")
    if task == 'classification':
        acc = m.get('accuracy', m.get('test_score', 0.0))
        f1  = m.get('f1', 0.0)
        prec = m.get('precision', 0.0)
        rec  = m.get('recall', 0.0)
        print(f"    Accuracy  : {acc:.3f}  ({_score_label(acc, task)})")
        if f1:   print(f"    F1        : {f1:.3f}")
        if prec: print(f"    Precisión : {prec:.3f}")
        if rec:  print(f"    Recall    : {rec:.3f}")
    else:
        r2   = m.get('r2', 0.0)
        rmse = m.get('rmse', 0.0)
        mae  = m.get('mae', 0.0)
        print(f"    R²   : {r2:.3f}  ({_score_label(r2, task)})")
        print(f"    RMSE : {rmse:.4f}")
        print(f"    MAE  : {mae:.4f}")


def _ex_model_predict(d, m):
    task = d.get('task', '?')
    n    = d.get('n', '?')
    if task == 'classification':
        ok  = m.get('n_correct', 0)
        err = m.get('n_error', 0)
        acc = m.get('accuracy', 0.0)
        print(f"  Predicciones sobre {n} ejemplos del conjunto de prueba.")
        print(f"    Correctas : {ok}/{n}  (accuracy {acc:.1%})")
        print(f"    Errores   : {err}/{n}")
    else:
        mae  = m.get('mean_abs_error', 0.0)
        maxe = m.get('max_abs_error', 0.0)
        bias = m.get('bias', 0.0)
        print(f"  Predicciones sobre {n} ejemplos del conjunto de prueba.")
        print(f"    Error medio  : {mae:.4f}")
        print(f"    Error máximo : {maxe:.4f}")
        print(f"    Sesgo (bias) : {bias:+.4f}")


def _ex_model_importance(d, m):
    algo   = _algo_name(d.get('algo', '?'))
    method = d.get('method', '?')
    top_f, top_v = _top_importance(m)
    print(f"  Importancia de variables para {algo} (método: {method}).")
    if top_f:
        print(f"  Variable más influyente: '{top_f}' → {top_v:.1%} de importancia.")


def _ex_model_cv(d, m):
    algo    = _algo_name(d.get('algo', '?'))
    task    = d.get('task', '?')
    folds   = d.get('n_folds', '?')
    mean_s  = m.get('mean', 0.0)
    std_s   = m.get('std', 0.0)
    ci_lo   = m.get('ci_lo', 0.0)
    ci_hi   = m.get('ci_hi', 0.0)
    lbl     = _score_label(mean_s, task)
    print(f"  Validación cruzada de {algo} con {folds} pliegues.")
    print(f"  Score medio: {mean_s:.3f} ± {std_s:.3f}  ({lbl})")
    print(f"  IC 95%: [{ci_lo:.3f}, {ci_hi:.3f}]")


def _ex_model_save(d, m):
    algo = _algo_name(d.get('algo', '?'))
    path = d.get('path', '?')
    kb   = m.get('size_kb', 0.0)
    print(f"  Modelo {algo} guardado en '{path}' ({kb:.1f} KB).")


def _ex_model_load(d, m):
    algo = _algo_name(d.get('algo', '?'))
    task = d.get('task', '?')
    path = d.get('path', '?')
    kb   = m.get('size_kb', 0.0)
    print(f"  Modelo {algo} ({task}) cargado desde '{path}' ({kb:.1f} KB).")
    print(f"  El modelo está listo para predecir.")


def _ex_data_target(d, m):
    col    = d.get('column', '?')
    task   = d.get('task_type', '?')
    n_uniq = m.get('n_unique', '?')
    task_es = 'clasificación' if 'clasif' in task else 'regresión'
    print(f"  Variable objetivo establecida: '{col}'.")
    print(f"  Tarea detectada: {task_es}  ({n_uniq} valores únicos).")


def _ex_data_info(d, m):
    rows  = m.get('rows', '?')
    cols  = m.get('cols', '?')
    nulls = m.get('nulls', 0)
    nums  = d.get('numeric', [])
    print(f"  Resumen del dataset: {rows} filas, {cols} columnas.")
    print(f"  Variables numéricas: {len(nums)}.  Valores nulos: {nulls}.")


def _ex_data_head(d, m):
    n     = d.get('n', '?')
    total = m.get('total', '?')
    print(f"  Se mostraron las {n} primeras filas de {total} totales.")


def _ex_data_shape(d, m):
    rows = m.get('rows', '?')
    cols = m.get('cols', '?')
    print(f"  Dimensiones del dataset: {rows} filas × {cols} columnas.")


def _ex_data_shuffle(d, m):
    rows = m.get('rows', '?')
    print(f"  Se aleatorizó el orden de {rows} filas.")


def _ex_data_drop(d, m):
    col  = d.get('dropped', '?')
    ncol = m.get('n_cols', '?')
    print(f"  Columna '{col}' eliminada. Quedan {ncol} columnas.")


def _ex_data_select(d, m):
    n_after  = m.get('n_after', '?')
    n_before = m.get('n_before', '?')
    removed  = d.get('removed', [])
    print(f"  Selección de columnas: {n_before} → {n_after} columnas.")
    if removed:
        print(f"  Eliminadas: {', '.join(str(c) for c in removed[:5])}")


def _ex_algo_select(d, m):
    algo = _algo_name(d.get('algo', '?'))
    print(f"  Algoritmo seleccionado: {algo}.")
    print(f"  Ejecuta model-train para entrenar con los datos actuales.")


def _ex_model_matrix(d, m):
    task   = d.get('task', '?')
    algo   = _algo_name(d.get('algo', '?'))
    if task == 'classification':
        labels = d.get('labels', [])
        print(f"  Matriz de confusión de {algo} ({len(labels)} clases).")
    else:
        mae = m.get('mae', 0.0)
        std = m.get('std', 0.0)
        print(f"  Distribución de errores de {algo}.")
        print(f"  Error medio absoluto: {mae:.4f},  desviación: {std:.4f}.")


_EXPLAIN_HANDLERS = {
    'data-load':        _ex_data_load,
    'data-fill':        _ex_data_fill,
    'data-norm':        _ex_data_norm,
    'data-split':       _ex_data_split,
    'data-target':      _ex_data_target,
    'data-info':        _ex_data_info,
    'data-head':        _ex_data_head,
    'data-shape':       _ex_data_shape,
    'data-shuffle':     _ex_data_shuffle,
    'data-drop':        _ex_data_drop,
    'data-select':      _ex_data_select,
    'rf-model':         _ex_algo_select,
    'tree-model':       _ex_algo_select,
    'knn-model':        _ex_algo_select,
    'svm-model':        _ex_algo_select,
    'model-matrix':     _ex_model_matrix,
    'pat-find':         _ex_pat_find,
    'pat-corr':         _ex_pat_corr,
    'pat-cluster':      _ex_pat_cluster,
    'pat-pca':          _ex_pat_pca,
    'pat-anomaly':      _ex_pat_anomaly,
    'pat-sequence':     _ex_pat_sequence,
    'model-train':      _ex_model_train,
    'model-eval':       _ex_model_eval,
    'model-predict':    _ex_model_predict,
    'model-importance': _ex_model_importance,
    'model-cv':         _ex_model_cv,
    'model-save':       _ex_model_save,
    'model-load':       _ex_model_load,
}


def explain(forth):
    ai = getattr(forth, '_ai', {})
    op = ai.get('last_op')
    if op is None:
        print("Nada que explicar — ejecuta alguna operación AI primero.")
        return
    t   = op.get('type', '')
    d   = op.get('data', {})
    m   = op.get('metrics', {})
    fn  = _EXPLAIN_HANDLERS.get(t)
    _sep(f"Explicación: {t}")
    if fn:
        fn(d, m)
    else:
        print(f"  Última operación: {t}")
        print(f"  (Sin narrativa detallada para este tipo de operación)")


# ─────────────────────────────────────────────────────────────────────────────
# AI-WHY — interpreta los resultados, añade contexto cualitativo
# ─────────────────────────────────────────────────────────────────────────────

def _why_data_load(d, m, ai):
    rows = m.get('rows', 0)
    cols = m.get('cols', 0)
    if rows < 100:
        print("  ⚠ Dataset pequeño (<100 filas) — los modelos pueden tener alta varianza.")
        print("    Considera usar model-cv en lugar de un solo train/test.")
    elif rows > 10000:
        print("  ✓ Dataset grande — buena base para entrenar modelos robustos.")
    else:
        print("  ✓ Tamaño razonable para la mayoría de algoritmos de sklearn.")
    if cols > 50:
        print(f"  ⚠ Muchas columnas ({cols}) — considera pat-pca para reducir dimensionalidad.")


def _why_data_fill(d, m, ai):
    total = m.get('total_filled', 0)
    strat = d.get('strategy', '')
    if total == 0:
        print("  Dataset ya completo — no fue necesario imputar.")
        return
    print(f"  Los valores nulos impedirían entrenar el modelo sin preprocesado.")
    if strat == 'media':
        print("  'Media' es segura para distribuciones simétricas.")
        print("  Si hay outliers, 'mediana' es más robusta.")
    elif strat == 'mediana':
        print("  'Mediana' es robusta frente a outliers — buena elección.")
    elif strat == 'moda':
        print("  'Moda' es adecuada para variables categóricas.")
    elif strat == 'cero':
        print("  Rellenar con cero asume que la ausencia equivale a 0.")
        print("  Comprueba que esta hipótesis tiene sentido en tu dominio.")


def _why_data_norm(d, m, ai):
    n = m.get('n_normalized', 0)
    print(f"  La normalización pone todas las variables en la misma escala.")
    print(f"  Imprescindible para KNN y SVM, recomendable para la mayoría.")
    print(f"  Random Forest y árboles de decisión no la necesitan, pero no la perjudica.")


def _why_data_split(d, m, ai):
    ratio  = d.get('ratio', 0.2)
    strat  = d.get('strategy', '')
    n_test = m.get('n_test', 0)
    if n_test < 20:
        print(f"  ⚠ Conjunto de prueba pequeño ({n_test} ejemplos) — el score puede variar mucho.")
        print("    Usa model-cv para una estimación más fiable.")
    if 'estratificado' in strat:
        print("  ✓ Split estratificado garantiza que la proporción de clases se mantiene.")
        print("    Esto evita que el test tenga muy pocas muestras de alguna clase.")
    else:
        print("  Split aleatorio — las clases pueden quedar desbalanceadas en datasets pequeños.")


def _why_pat_find(d, m, ai):
    nulls = d.get('total_nulls', 0)
    n_num = m.get('n_numeric', 0)
    if nulls > 0:
        print(f"  ⚠ {nulls} valores nulos detectados — usa data-fill antes de entrenar.")
    if n_num == 0:
        print("  ⚠ Sin variables numéricas — la mayoría de modelos sklearn requieren números.")
        print("    Transforma las variables de texto con codificación antes de entrenar.")
    elif n_num > 20:
        print(f"  {n_num} variables numéricas — considera pat-pca para reducir dimensionalidad")
        print("  y eliminar redundancias antes de entrenar.")


def _why_pat_corr(d, m, ai):
    n_pairs = m.get('n_high_pairs', 0)
    pairs   = d.get('pairs', [])
    if n_pairs == 0:
        print("  Sin pares altamente correlacionados — las variables son relativamente independientes.")
        print("  Buena señal: cada variable aporta información distinta al modelo.")
    else:
        print(f"  {n_pairs} par(es) con correlación alta:")
        for c1, c2, v in pairs[:4]:
            direction = "positiva" if v > 0 else "negativa"
            print(f"    '{c1}' ↔ '{c2}': {v:+.3f} ({direction})")
        if n_pairs > 4:
            print(f"    … y {n_pairs-4} más")
        print("  Variables muy correlacionadas pueden introducir multicolinealidad.")
        print("  Considera eliminar una de cada par redundante.")


def _why_pat_cluster(d, m, ai):
    n   = d.get('n_clusters', 0)
    sil = m.get('silhouette', 0.0)
    if sil >= 0.70:
        print(f"  ✓ Silhouette {sil:.3f} — clusters muy bien separados.")
        print("  Los grupos encontrados son naturales y distintos en los datos.")
    elif sil >= 0.50:
        print(f"  ✓ Silhouette {sil:.3f} — clusters razonablemente separados.")
        print("  Puedes experimentar con N±1 para ver si mejora.")
    elif sil >= 0.30:
        print(f"  ~ Silhouette {sil:.3f} — clusters con cierto solapamiento.")
        print(f"  Prueba N entre 2 y {min(8, n+3)} para encontrar el valor óptimo.")
    else:
        print(f"  ⚠ Silhouette {sil:.3f} — los clusters se solapan mucho.")
        print("  Puede que los datos no tengan estructura de grupos clara,")
        print(f"  o que N={n} no sea el número adecuado. Prueba pat-pca primero.")


def _why_pat_pca(d, m, ai):
    total = m.get('total_variance', 0.0)
    n     = m.get('n_components', 0)
    if total >= 0.90:
        print(f"  ✓ {n} componentes explican {total:.0%} de la varianza — reducción eficiente.")
        print("  Puedes usar estas componentes para entrenar con menos variables.")
    elif total >= 0.70:
        print(f"  ~ {n} componentes explican {total:.0%} — aceptable.")
        print("  Añade 1-2 componentes más si quieres capturar más información.")
    else:
        print(f"  ⚠ Solo {total:.0%} de varianza con {n} componentes.")
        print("  Los datos pueden ser intrínsecamente de alta dimensión.")
        print("  Considera aumentar el número de componentes.")


def _why_pat_anomaly(d, m, ai):
    n_tot = m.get('n_total', 1)
    n_ano = m.get('n_anomaly', 0)
    pct   = n_ano / n_tot if n_tot > 0 else 0.0
    cont  = d.get('contamination', 0.1)
    if pct > 0.20:
        print(f"  ⚠ Tasa de anomalías alta ({pct:.0%}) — puede ser demasiado permisivo.")
        print("  Reduce 'contamination' (actualmente {cont:.0%}) para ser más selectivo.")
    elif pct < 0.02:
        print(f"  ~ Muy pocas anomalías ({n_ano}) — puede que el umbral sea demasiado estricto.")
        print("  Aumenta 'contamination' si esperas más casos atípicos.")
    else:
        print(f"  ✓ Tasa de anomalías ({pct:.1%}) coherente con la contaminación configurada.")
    if n_ano > 0:
        print("  Las anomalías pueden ser errores de datos O casos genuinamente especiales.")
        print("  Revísalas antes de decidir si eliminarlas del entrenamiento.")


def _why_pat_sequence(d, m, ai):
    trend = d.get('trend', '')
    ac1   = m.get('ac1', 0.0)
    cv    = m.get('cv_pct', 0.0)
    n_j   = m.get('n_jumps', 0)
    if abs(ac1) > 0.7:
        print(f"  Alta autocorrelación ({ac1:.3f}) — valores consecutivos muy dependientes.")
        print("  Modelos de series temporales (ARIMA, etc.) serían más adecuados que sklearn.")
    elif abs(ac1) < 0.2:
        print(f"  Autocorrelación baja ({ac1:.3f}) — la serie se parece a ruido aleatorio.")
    if cv > 50:
        print(f"  Alta variabilidad ({cv:.1f}%) — la serie es muy irregular.")
    if n_j > 0:
        print(f"  {n_j} saltos bruscos detectados — posibles cambios de régimen o errores de datos.")
    if 'creciente' in trend or 'ascendente' in trend:
        print("  Tendencia creciente — los valores aumentan con el tiempo.")
    elif 'decreciente' in trend or 'descendente' in trend:
        print("  Tendencia decreciente — los valores disminuyen con el tiempo.")


def _why_model_train(d, m, ai):
    score = m.get('train_score', 0.0)
    task  = d.get('task', 'classification')
    algo  = _algo_name(d.get('algo', '?'))
    n     = d.get('n_train', 0)
    if score >= 0.99:
        print(f"  ⚠ Score perfecto ({score:.3f}) en entrenamiento — posible sobreajuste.")
        print("  El modelo puede haber memorizado los datos de entrenamiento.")
        print("  Usa model-cv o model-eval para ver el rendimiento real.")
    elif score >= 0.85:
        print(f"  ✓ Buen score de entrenamiento ({score:.3f}).")
        print("  Ahora comprueba con model-eval si generaliza bien a datos nuevos.")
    elif score >= 0.60:
        print(f"  ~ Score moderado ({score:.3f}) — el modelo ha aprendido patrones parciales.")
        print("  Prueba más features, más datos o un algoritmo diferente.")
    else:
        print(f"  ⚠ Score bajo ({score:.3f}) — el modelo tiene dificultades.")
        print("  Posibles causas:")
        print("    · Variables irrelevantes — usa pat-corr o pat-find")
        print("    · Datos sin normalizar — usa data-norm antes de entrenar")
        print("    · Dataset demasiado pequeño o ruidoso")
    if n < 50:
        print(f"  ⚠ Solo {n} ejemplos de entrenamiento — dataset muy pequeño.")


def _why_model_eval(d, m, ai):
    task = d.get('task', 'classification')
    if task == 'classification':
        acc  = m.get('accuracy', m.get('test_score', 0.0))
        f1   = m.get('f1', 0.0)
        lbl  = _score_label(acc, task)
        print(f"  Accuracy {acc:.3f} ({lbl}) en datos que el modelo NO vio durante el entrenamiento.")
        if f1 and acc - f1 > 0.10:
            print(f"  ⚠ F1 ({f1:.3f}) mucho menor que accuracy — posible desbalance de clases.")
            print("    El modelo puede estar prediciendo siempre la clase mayoritaria.")
        train_score = (ai.get('last_op') or {}).get('metrics', {}).get('train_score')
        if train_score:
            gap = train_score - acc
            if gap > 0.15:
                print(f"  ⚠ Gran diferencia train/test ({gap:+.3f}) — sobreajuste probable.")
                print("    Usa model-cv para confirmar o prueba un modelo más simple.")
            elif gap < 0.03:
                print(f"  ✓ Diferencia train/test mínima ({gap:+.3f}) — buen equilibrio.")
        if acc < 0.60:
            print("  Considera:")
            print("    · Revisar las features con pat-corr o model-importance")
            print("    · Probar un algoritmo diferente (rf-model, svm-model...)")
    else:
        r2   = m.get('r2', 0.0)
        rmse = m.get('rmse', 0.0)
        if r2 < 0:
            print(f"  ⚠ R² negativo ({r2:.3f}) — el modelo es peor que predecir la media.")
            print("  Revisa las features y considera normalizar con data-norm.")
        elif r2 >= 0.75:
            print(f"  ✓ R² {r2:.3f} — el modelo explica bien la varianza de los datos.")
        else:
            print(f"  ~ R² {r2:.3f} — el modelo explica parte de la varianza.")
            print("  Añadir más features relevantes podría mejorar el rendimiento.")


def _why_model_predict(d, m, ai):
    task = d.get('task', 'classification')
    if task == 'classification':
        acc = m.get('accuracy', 0.0)
        err = m.get('n_error', 0)
        n   = d.get('n', 1)
        if acc >= 0.90:
            print(f"  ✓ {acc:.0%} de aciertos — predicciones muy fiables.")
        elif acc >= 0.70:
            print(f"  ~ {acc:.0%} de aciertos — rendimiento aceptable.")
        else:
            print(f"  ⚠ {acc:.0%} de aciertos — muchos errores.")
        if err > 0:
            print(f"  Usa model-matrix para ver qué clases se confunden más.")
    else:
        mae  = m.get('mean_abs_error', 0.0)
        bias = m.get('bias', 0.0)
        if abs(bias) > mae * 0.5:
            direction = "sobreestima" if bias > 0 else "subestima"
            print(f"  ⚠ El modelo {direction} sistemáticamente (bias {bias:+.4f}).")
        else:
            print("  ✓ Sesgo (bias) pequeño — sin tendencia sistemática a sobre/subestimar.")


def _why_model_importance(d, m, ai):
    method = d.get('method', '')
    top_f, top_v = _top_importance(m)
    sorted_imp = sorted(m.items(), key=lambda kv: kv[1], reverse=True)
    n_low = sum(1 for _, v in sorted_imp if v < 0.05)
    printed = False
    if top_v > 0.5:
        print(f"  ⚠ '{top_f}' domina con {top_v:.0%} — el modelo depende mucho de una sola variable.")
        print("  Comprueba si esta variable podría estar causando sobreajuste.")
        printed = True
    if n_low > 0:
        print(f"  {n_low} variable(s) con importancia < 5% — considera eliminarlas.")
        print("  Menos variables suelen mejorar la generalización del modelo.")
        printed = True
    if method == 'permutation':
        print("  (Importancia por permutación: mide el impacto de desordenar cada variable.)")
        printed = True
    if not printed and top_f:
        print(f"  ✓ Importancias bien distribuidas — ninguna variable domina en exceso.")
        print(f"  Las {len(sorted_imp)} variables contribuyen de forma equilibrada al modelo.")


def _why_model_cv(d, m, ai):
    mean_s = m.get('mean', 0.0)
    std_s  = m.get('std', 0.0)
    task   = d.get('task', 'classification')
    cv_pct = (std_s / mean_s * 100) if mean_s > 0 else 0
    lbl    = _score_label(mean_s, task)
    print(f"  Score CV: {mean_s:.3f} ({lbl}). Variación entre pliegues: {cv_pct:.1f}%.")
    if cv_pct > 15:
        print("  ⚠ Alta varianza entre pliegues — el modelo es sensible a los datos de entrenamiento.")
        print("  Causas posibles: dataset pequeño, clases desbalanceadas, modelo complejo.")
    elif cv_pct < 5:
        print("  ✓ Rendimiento muy consistente — el modelo generaliza bien.")
    if mean_s < 0.60:
        print("  El score CV confirma que el modelo no captura bien los patrones.")
        print("  Considera cambiar de algoritmo o añadir más features.")


def _why_model_save(d, m, ai):
    kb = m.get('size_kb', 0.0)
    print("  El modelo está guardado y puede restaurarse en cualquier momento.")
    if kb > 500:
        print(f"  ⚠ Archivo grande ({kb:.0f} KB) — RF con muchos árboles puede ser pesado en iOS.")


def _why_model_load(d, m, ai):
    print("  El modelo cargado incluye la configuración del scaler (si se usó).")
    print("  Los datos nuevos se normalizarán automáticamente igual que en el entrenamiento.")


def _why_data_target(d, m, ai):
    task   = d.get('task_type', '')
    n_uniq = m.get('n_unique', 0)
    col    = d.get('column', '?')
    if 'clasif' in task:
        print(f"  Tarea de clasificación ({n_uniq} clases).")
        if n_uniq == 2:
            print("  Clasificación binaria — los algoritmos estándar funcionan bien.")
        elif n_uniq > 10:
            print(f"  ⚠ {n_uniq} clases — muchas categorías pueden dificultar el aprendizaje.")
    else:
        print(f"  Tarea de regresión — '{col}' tiene más de 10 valores distintos.")
        print("  El modelo predecirá un valor numérico continuo.")


def _why_data_info(d, m, ai):
    nulls = m.get('nulls', 0)
    rows  = m.get('rows', 0)
    if nulls > 0:
        pct = nulls / max(rows, 1) * 100
        print(f"  ⚠ {nulls} valores nulos detectados ({pct:.1f}% del total).")
        print("  Usa data-fill para rellenarlos antes de entrenar.")
    else:
        print("  ✓ Sin valores nulos — el dataset está limpio.")
    nums = d.get('numeric', [])
    if len(nums) == 0:
        print("  ⚠ Sin columnas numéricas — la mayoría de modelos no podrán entrenar.")


def _why_data_head(d, m, ai):
    print("  Previsualización de datos — útil para detectar errores de formato")
    print("  (fechas leídas como texto, separadores incorrectos, etc.).")


def _why_data_shape(d, m, ai):
    rows = m.get('rows', 0)
    cols = m.get('cols', 0)
    if rows < 100:
        print(f"  ⚠ Solo {rows} filas — dataset pequeño, considera model-cv.")
    if cols > 20:
        print(f"  {cols} columnas — muchas variables; pat-pca puede reducir dimensionalidad.")


def _why_data_shuffle(d, m, ai):
    print("  El orden original puede introducir sesgos en el entrenamiento.")
    print("  Mezclar las filas garantiza que train/test sean representativos.")


def _why_data_drop(d, m, ai):
    col = d.get('dropped', '?')
    print(f"  Eliminar '{col}' reduce el ruido si esa columna no aportaba información.")
    print("  Si el rendimiento baja al entrenar, considera restaurarla.")


def _why_data_select(d, m, ai):
    removed = d.get('removed', [])
    if removed:
        print(f"  Se descartaron {len(removed)} columna(s) no seleccionadas.")
        print("  Menos variables suelen producir modelos más simples y generalizables.")


def _why_algo_select(d, m, ai):
    algo = d.get('algo', '')
    tips = {
        'rf':   ("Random Forest es robusto y funciona bien sin normalizar los datos.\n"
                 "  Buen punto de partida para casi cualquier problema."),
        'tree': ("El árbol de decisión es el más interpretable — puedes ver exactamente\n"
                 "  qué reglas usa para clasificar."),
        'knn':  ("KNN es sensible a la escala — usa data-norm antes de entrenar.\n"
                 "  Lento con datasets grandes (>10 000 filas)."),
        'svm':  ("SVM suele ser potente en datasets pequeños/medianos.\n"
                 "  Requiere data-norm para buen rendimiento."),
    }
    print(f"  {tips.get(algo, 'Algoritmo seleccionado.')}")


def _why_model_matrix(d, m, ai):
    task = d.get('task', '')
    if task == 'classification':
        print("  La matriz de confusión muestra qué clases confunde el modelo.")
        print("  Diagonal principal = aciertos. Resto = errores.")
        print("  Si una fila tiene muchos errores, esa clase es difícil de predecir.")
    else:
        mae = m.get('mae', 0.0)
        print(f"  Error medio absoluto: {mae:.4f}.")
        print("  El histograma muestra si los errores son simétricos (buen modelo)")
        print("  o si hay un sesgo claro hacia sobreestimar o subestimar.")


_WHY_HANDLERS = {
    'data-load':        _why_data_load,
    'data-fill':        _why_data_fill,
    'data-norm':        _why_data_norm,
    'data-split':       _why_data_split,
    'data-target':      _why_data_target,
    'data-info':        _why_data_info,
    'data-head':        _why_data_head,
    'data-shape':       _why_data_shape,
    'data-shuffle':     _why_data_shuffle,
    'data-drop':        _why_data_drop,
    'data-select':      _why_data_select,
    'rf-model':         _why_algo_select,
    'tree-model':       _why_algo_select,
    'knn-model':        _why_algo_select,
    'svm-model':        _why_algo_select,
    'model-matrix':     _why_model_matrix,
    'pat-find':         _why_pat_find,
    'pat-corr':         _why_pat_corr,
    'pat-cluster':      _why_pat_cluster,
    'pat-pca':          _why_pat_pca,
    'pat-anomaly':      _why_pat_anomaly,
    'pat-sequence':     _why_pat_sequence,
    'model-train':      _why_model_train,
    'model-eval':       _why_model_eval,
    'model-predict':    _why_model_predict,
    'model-importance': _why_model_importance,
    'model-cv':         _why_model_cv,
    'model-save':       _why_model_save,
    'model-load':       _why_model_load,
}


def ai_why(forth):
    ai = getattr(forth, '_ai', {})
    op = ai.get('last_op')
    if op is None:
        print("Ninguna operación previa — no hay resultados que interpretar.")
        return
    t  = op.get('type', '')
    d  = op.get('data', {})
    m  = op.get('metrics', {})
    fn = _WHY_HANDLERS.get(t)
    _sep(f"Por qué: {t}")
    if fn:
        fn(d, m, ai)
    else:
        print(f"  (Sin interpretación específica para '{t}')")


# ─────────────────────────────────────────────────────────────────────────────
# AI-NEXT — sugiere el paso lógico siguiente
# ─────────────────────────────────────────────────────────────────────────────

def _next_data_load(d, m, ai):
    print("  Explora el dataset antes de entrenar:")
    print('    data-info           \\ estadísticas básicas')
    print('    data-head           \\ primeras filas')
    print()
    print("  Luego configura la variable objetivo:")
    print('    s" columna" data-target')
    print('    data-split          \\ divide en train/test')


def _next_data_fill(d, m, ai):
    target = ai.get('target_col')
    if not target:
        print("  Establece la variable objetivo:")
        print('    s" columna" data-target')
    else:
        train = ai.get('train_set')
        if train is None:
            print("  Divide los datos antes de entrenar:")
            print('    data-split')
        else:
            print("  Entrena el modelo:")
            print('    rf-model model-train    \\ Random Forest (recomendado)')


def _next_data_norm(d, m, ai):
    train = ai.get('train_set')
    if train is None:
        print("  Divide en train/test:")
        print('    data-split')
    else:
        print("  Listo para entrenar:")
        print('    rf-model  model-train')


def _next_data_split(d, m, ai):
    print("  Los conjuntos están listos — elige un algoritmo y entrena:")
    print('    rf-model   model-train  \\ Random Forest (versátil)')
    print('    tree-model model-train  \\ Árbol de decisión (interpretable)')
    print('    knn-model  model-train  \\ K-Vecinos (simple)')
    print('    svm-model  model-train  \\ SVM (potente con data-norm)')


def _next_pat_find(d, m, ai):
    nulls = d.get('total_nulls', 0)
    n_num = len(d.get('numeric_cols', []))
    if nulls > 0:
        print("  Primero rellena los valores nulos:")
        print('    data-fill')
        print()
    print("  Continúa con el análisis de patrones:")
    print('    pat-corr            \\ correlaciones entre variables')
    if n_num >= 3:
        print('    pat-cluster         \\ busca grupos naturales')
    print()
    print("  O pasa directamente a modelar:")
    print('    s" objetivo" data-target')
    print('    data-split')
    print('    rf-model model-train')


def _next_pat_corr(d, m, ai):
    n_pairs = m.get('n_high_pairs', 0)
    if n_pairs > 0:
        print("  Hay variables muy correlacionadas — considera eliminar redundancias:")
        print('    \\ Ejemplo: data-drop con las columnas redundantes')
        print()
    print("  Siguientes pasos:")
    print('    pat-cluster         \\ busca grupos en los datos')
    print('    pat-anomaly         \\ detecta casos atípicos')
    print('    data-split          \\ si ya tienes target, entrena')


def _next_pat_cluster(d, m, ai):
    sil = m.get('silhouette', 0.0)
    print("  La columna 'cluster' ya está en el dataset.")
    if sil < 0.40:
        n = d.get('n_clusters', 3)
        print(f"  El silhouette es bajo — prueba N diferente (actualmente {n}):")
        print(f'    {n+1} pat-cluster      \\ o {max(2,n-1)} pat-cluster')
        print()
    print("  Continúa con:")
    print('    model-train         \\ usa cluster como feature adicional')
    print('    pat-corr            \\ correlaciones dentro de cada cluster')


def _next_pat_pca(d, m, ai):
    total = m.get('total_variance', 0.0)
    print("  Las componentes PCA están añadidas al dataset.")
    if total < 0.80:
        print("  ~ Varianza explicada baja — considera aumentar el número de componentes.")
    print("  Siguientes pasos:")
    print('    data-split          \\ divide usando las componentes PCA')
    print('    rf-model model-train')


def _next_pat_anomaly(d, m, ai):
    n_ano = m.get('n_anomaly', 0)
    print("  Columna 'anomalia' añadida (-1 = anómalo, 1 = normal).")
    if n_ano > 0:
        print(f"  Revisa manualmente los {n_ano} casos marcados.")
        print()
    print("  Opciones:")
    print('    model-train         \\ entrena incluyendo las anomalías')
    print('    \\ O filtra las anomalías primero con py{ }')


def _next_pat_sequence(d, m, ai):
    print("  Análisis de serie temporal completado.")
    print("  Opciones:")
    print('    pat-corr            \\ correlaciones con otras variables')
    print('    model-train         \\ predice valores futuros (ventana deslizante)')
    print('    pat-sequence        \\ analiza otra columna temporal')


def _next_model_train(d, m, ai):
    score = m.get('train_score', 0.0)
    task  = d.get('task', 'classification')
    print("  El modelo está entrenado. Evalúa su rendimiento real:")
    print('    model-eval          \\ score en el conjunto de prueba')
    print('    model-cv            \\ validación cruzada (más robusto)')
    print()
    print("  O explora directamente:")
    print('    model-predict       \\ predicciones individuales con confianza')
    print('    model-importance    \\ variables más influyentes')
    if score >= 0.99:
        print()
        print("  ⚠ Score muy alto en train — verifica el sobreajuste:")
        print('    model-cv 5          \\ validación cruzada con 5 pliegues')


def _next_model_eval(d, m, ai):
    task = d.get('task', 'classification')
    if task == 'classification':
        score = m.get('accuracy', m.get('test_score', 0.0))
    else:
        score = m.get('r2', 0.0)
    lbl = _score_label(score, task)

    if lbl in ('excelente', 'bueno'):
        print("  Buen rendimiento — guarda el modelo y analiza la importancia:")
        print('    model-importance    \\ ¿qué variables importan más?')
        print('    model-save          \\ guarda para uso futuro')
    else:
        print("  El rendimiento es mejorable. Opciones:")
        print('    model-importance    \\ elimina variables irrelevantes')
        algo = d.get('algo', '')
        if algo == 'tree':
            print('    rf-model model-train \\ Random Forest suele superar a un solo árbol')
        elif algo == 'knn':
            print('    rf-model model-train \\ prueba Random Forest')
        elif algo == 'rf':
            print('    svm-model model-train \\ prueba SVM (con data-norm)')
        print('    pat-corr             \\ busca más features correlacionadas')
    print()
    print("  También puedes ver las predicciones individuales:")
    print('    model-predict')


def _next_model_predict(d, m, ai):
    task = d.get('task', 'classification')
    print("  Predicciones visualizadas.")
    if task == 'classification':
        print('    model-matrix        \\ matriz de confusión detallada')
    print('    model-importance    \\ ¿qué features influyen en esas predicciones?')
    print('    model-save          \\ guarda el modelo si estás satisfecho')


def _next_model_importance(d, m, ai):
    print("  Importancias calculadas.")
    sorted_imp = sorted(m.items(), key=lambda kv: kv[1], reverse=True)
    low = [f for f, v in sorted_imp if v < 0.05]
    if low:
        print(f"  Variables con baja importancia (<5%): {', '.join(low[:4])}")
        print("  Considera re-entrenar sin ellas para un modelo más simple.")
        print()
    print('    model-save          \\ guarda el modelo actual')
    print('    model-cv            \\ validación cruzada si aún no la hiciste')


def _next_model_cv(d, m, ai):
    mean_s = m.get('mean', 0.0)
    std_s  = m.get('std', 0.0)
    task   = d.get('task', 'classification')
    lbl    = _score_label(mean_s, task)
    cv_pct = (std_s / mean_s * 100) if mean_s > 0 else 0

    if lbl in ('excelente', 'bueno') and cv_pct < 10:
        print("  ✓ Modelo robusto y consistente. Siguiente paso:")
        print('    model-save          \\ guarda el modelo')
        print('    model-importance    \\ analiza qué variables importan')
    else:
        print("  El modelo puede mejorar. Opciones:")
        algo = d.get('algo', 'rf')
        if algo == 'rf':
            print('    svm-model model-train \\ prueba SVM')
        else:
            print('    rf-model  model-train \\ prueba Random Forest')
        print('    data-norm model-train \\ asegúrate de normalizar')
        print('    pat-corr              \\ revisa features redundantes')


def _next_model_save(d, m, ai):
    path = d.get('path', 'modelo.pkl')
    print("  Modelo guardado. Para recuperarlo en otra sesión:")
    print(f'    s" {path}" model-load')
    print('    model-predict       \\ predicciones con el modelo restaurado')


def _next_model_load(d, m, ai):
    print("  Modelo listo. Opciones:")
    print('    model-eval          \\ evalúa con los datos actuales')
    print('    model-predict       \\ genera predicciones')
    print('    model-importance    \\ revisa qué variables usa el modelo')


def _next_data_target(d, m, ai):
    train = ai.get('train_set')
    if train is None:
        print("  Variable objetivo establecida. Divide los datos:")
        print('    0.2 data-split')
    else:
        print("  Ya tienes train/test. Entrena el modelo:")
        print('    rf-model model-train')


def _next_data_info(d, m, ai):
    nulls = m.get('nulls', 0)
    if nulls > 0:
        print("  Hay valores nulos — rellénalos antes de entrenar:")
        print('    data-fill')
        print()
    target = ai.get('target_col')
    if not target:
        print("  Define la variable objetivo:")
        print('    s" columna" data-target')
    else:
        print("  Ya tienes objetivo. Divide y entrena:")
        print('    0.2 data-split')
        print('    rf-model model-train')


def _next_data_head(d, m, ai):
    print("  Explora más o prepara el entrenamiento:")
    print('    data-info           \\ estadísticas completas')
    print('    s" col" data-target \\ define el objetivo')


def _next_data_shape(d, m, ai):
    print('    data-info           \\ estadísticas y nulos')
    print('    s" col" data-target \\ define el objetivo')


def _next_data_shuffle(d, m, ai):
    train = ai.get('train_set')
    if train is None:
        print('    0.2 data-split')
    else:
        print('    rf-model model-train')


def _next_data_drop(d, m, ai):
    target = ai.get('target_col')
    if not target:
        print('    s" col" data-target')
    else:
        print('    0.2 data-split')
        print('    rf-model model-train')


def _next_data_select(d, m, ai):
    target = ai.get('target_col')
    if not target:
        print('    s" col" data-target \\ define el objetivo')
    else:
        print('    0.2 data-split')
        print('    rf-model model-train')


def _next_algo_select(d, m, ai):
    algo = d.get('algo', '')
    train = ai.get('train_set')
    if train is None:
        print("  Aún no hay conjuntos train/test:")
        print('    s" col" data-target')
        print('    0.2 data-split')
        print('    model-train')
    else:
        print("  Listo para entrenar:")
        print('    model-train')
    if algo in ('knn', 'svm'):
        print()
        print(f"  Recuerda: {algo.upper()} funciona mejor con datos normalizados:")
        print('    data-norm           \\ antes de model-train')


def _next_model_matrix(d, m, ai):
    task = d.get('task', '')
    if task == 'classification':
        print("  Tras revisar la matriz de confusión:")
        print('    model-importance    \\ ¿qué variables causan los errores?')
        print('    model-save          \\ guarda si el rendimiento es aceptable')
    else:
        print('    model-importance    \\ variables más influyentes')
        print('    model-save          \\ guarda el modelo')


_NEXT_HANDLERS = {
    'data-load':        _next_data_load,
    'data-fill':        _next_data_fill,
    'data-norm':        _next_data_norm,
    'data-split':       _next_data_split,
    'data-target':      _next_data_target,
    'data-info':        _next_data_info,
    'data-head':        _next_data_head,
    'data-shape':       _next_data_shape,
    'data-shuffle':     _next_data_shuffle,
    'data-drop':        _next_data_drop,
    'data-select':      _next_data_select,
    'rf-model':         _next_algo_select,
    'tree-model':       _next_algo_select,
    'knn-model':        _next_algo_select,
    'svm-model':        _next_algo_select,
    'model-matrix':     _next_model_matrix,
    'pat-find':         _next_pat_find,
    'pat-corr':         _next_pat_corr,
    'pat-cluster':      _next_pat_cluster,
    'pat-pca':          _next_pat_pca,
    'pat-anomaly':      _next_pat_anomaly,
    'pat-sequence':     _next_pat_sequence,
    'model-train':      _next_model_train,
    'model-eval':       _next_model_eval,
    'model-predict':    _next_model_predict,
    'model-importance': _next_model_importance,
    'model-cv':         _next_model_cv,
    'model-save':       _next_model_save,
    'model-load':       _next_model_load,
}


def ai_next(forth):
    ai = getattr(forth, '_ai', {})
    op = ai.get('last_op')
    if op is None:
        print("Sin operación previa. Empieza cargando datos:")
        print('    s" datos.csv" data-load')
        return
    t  = op.get('type', '')
    d  = op.get('data', {})
    m  = op.get('metrics', {})
    fn = _NEXT_HANDLERS.get(t)
    _sep(f"Siguiente paso tras: {t}")
    if fn:
        fn(d, m, ai)
    else:
        print(f"  No hay sugerencias específicas para '{t}'.")
        print("  Usa 'words' para ver todas las operaciones disponibles.")
