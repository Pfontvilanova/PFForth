# FORTH CODE WORD: code/ai/data/aistatus
# Panel de estado completo del entorno AI

WORD_NAME = 'ai-status'
#
# === STACK EFFECT ===
# ( -- ) Muestra dataset, target, split, modelo, última operación y modo
# === FIN ===

_LINE = "─" * 44


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {
            'dataset': None, 'target_col': None,
            'train_set': None, 'test_set': None,
            'model': None, 'last_op': None,
            'verbose': False, 'image': None,
            'audio': None, 'clip_model': None, 'yolo_model': None,
        }


def _fmt_model(model):
    """Nombre corto del modelo."""
    if model is None:
        return None
    name = type(model).__name__
    _SHORT = {
        'RandomForestClassifier':   'Random Forest (clasificación)',
        'RandomForestRegressor':    'Random Forest (regresión)',
        'LogisticRegression':       'Regresión logística',
        'LinearRegression':         'Regresión lineal',
        'SVC':                      'SVM (clasificación)',
        'SVR':                      'SVM (regresión)',
        'DecisionTreeClassifier':   'Árbol de decisión (clasif.)',
        'DecisionTreeRegressor':    'Árbol de decisión (regres.)',
        'KNeighborsClassifier':     'KNN (clasificación)',
        'KNeighborsRegressor':      'KNN (regresión)',
        'GradientBoostingClassifier': 'Gradient Boosting (clasif.)',
        'GradientBoostingRegressor':  'Gradient Boosting (regres.)',
    }
    return _SHORT.get(name, name)


def execute(forth):
    _ensure_ai(forth)
    ai = forth._ai

    print(_LINE)
    print("  ESTADO DEL ENTORNO AI")
    print(_LINE)

    # ── Dataset ──────────────────────────────────
    df = ai.get('dataset')
    if df is not None:
        nulls = int(df.isnull().sum().sum())
        null_label = f"  {nulls} nulos" if nulls else "  sin nulos"
        print(f"  Dataset   : {len(df)} filas × {len(df.columns)} columnas{null_label}")
        cols_preview = ', '.join(df.columns[:5])
        if len(df.columns) > 5:
            cols_preview += f', ... (+{len(df.columns)-5})'
        print(f"  Columnas  : {cols_preview}")
    else:
        print("  Dataset   : — (sin cargar)")

    # ── Target ───────────────────────────────────
    target = ai.get('target_col')
    if target:
        task = ai.get('last_op', {}) or {}
        task_type = ""
        if df is not None and target in df.columns:
            n_unique = df[target].nunique()
            task_type = "clasificación" if n_unique <= 10 else "regresión"
        print(f"  Objetivo  : '{target}'  [{task_type}]")
    else:
        print("  Objetivo  : — (sin definir)")

    # ── Split ────────────────────────────────────
    train = ai.get('train_set')
    test  = ai.get('test_set')
    if train is not None and test is not None:
        total = len(train) + len(test)
        pct   = round(len(test) / total * 100)
        print(f"  Split     : {len(train)} entreno / {len(test)} prueba  ({100-pct}/{pct}%)")
    else:
        print("  Split     : — (sin dividir)")

    # ── Modelo ───────────────────────────────────
    model_label = _fmt_model(ai.get('model'))
    if model_label:
        print(f"  Modelo    : {model_label}")
        last = ai.get('last_op') or {}
        if last.get('type', '').startswith('model-') and last.get('metrics'):
            m = last['metrics']
            parts = []
            for k, v in m.items():
                if isinstance(v, float):
                    parts.append(f"{k}={v:.3f}")
                else:
                    parts.append(f"{k}={v}")
            if parts:
                print(f"  Métricas  : {', '.join(parts)}")
    else:
        print("  Modelo    : — (sin entrenar)")

    # ── Visión ───────────────────────────────────
    img = ai.get('image')
    if img is not None:
        shape = getattr(img, 'shape', None)
        if shape:
            h, w = shape[:2]
            print(f"  Imagen    : {w}×{h} px")
        else:
            print(f"  Imagen    : cargada")
    clip = ai.get('clip_model')
    yolo = ai.get('yolo_model')
    if clip or yolo:
        models = []
        if clip: models.append("CLIP")
        if yolo: models.append("YOLO")
        print(f"  Modelos   : {', '.join(models)} listos")

    # ── Audio ────────────────────────────────────
    audio = ai.get('audio')
    if audio is not None:
        print(f"  Audio     : cargado")

    # ── Última operación ─────────────────────────
    last_op = ai.get('last_op')
    if last_op and last_op.get('type'):
        print(f"  Última op : {last_op['type']}")
    else:
        print("  Última op : —")

    # ── Modo ─────────────────────────────────────
    verbose = ai.get('verbose', False)
    print(f"  Verbose   : {'activado' if verbose else 'desactivado'}  "
          f"(usa verbose-on / verbose-off)")

    print(_LINE)

    forth._ai['last_op'] = {
        'type':    'ai-status',
        'data':    {},
        'metrics': {},
    }
