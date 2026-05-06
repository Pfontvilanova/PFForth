# FORTH CODE WORD: code/ai/pattern/patfind
# Resumen estadístico profundo: media, std, percentiles, sesgo, nulos

WORD_NAME = 'pat-find'
#
# === STACK EFFECT ===
# ( -- ) Muestra estadísticas completas de todas las columnas
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


def _bar(v, lo=-1.0, hi=1.0, width=10):
    """Barra proporcional entre lo y hi."""
    v = max(lo, min(hi, v))
    filled = round((v - lo) / (hi - lo) * width)
    return '█' * filled + '░' * (width - filled)


def _fmt(v):
    """Formato numérico compacto."""
    if v is None:
        return '—'
    if isinstance(v, float):
        if abs(v) >= 1000 or (abs(v) < 0.01 and v != 0):
            return f"{v:.2e}"
        return f"{v:.3g}"
    return str(v)


def _skew_label(s):
    if s >  1.0: return "muy sesgado +"
    if s >  0.5: return "sesgado +"
    if s < -1.0: return "muy sesgado -"
    if s < -0.5: return "sesgado -"
    return "simétrico"


def execute(forth):
    _ensure_ai(forth)

    df = forth._ai.get('dataset')
    if df is None:
        print("Error: no hay dataset cargado — usa data-load primero")
        return

    target = forth._ai.get('target_col')
    num_df = df.select_dtypes(include='number')
    txt_df = df.select_dtypes(exclude='number')

    print(f"=== PAT-FIND: {len(df)} filas × {len(df.columns)} columnas ===")
    print()

    # ── Columnas numéricas ─────────────────────────────────
    if not num_df.empty:
        print("── Columnas numéricas ─────────────────────────────────")
        W = 14
        header = (f"  {'columna':<{W}}  {'nulos':>5}  {'min':>8}  "
                  f"{'p25':>8}  {'media':>8}  {'p75':>8}  {'max':>8}  "
                  f"{'std':>8}  sesgo")
        print(header)
        print("  " + "─" * (len(header) - 2))

        stats = num_df.describe(percentiles=[.25, .75]).T
        skews = num_df.skew()

        for col in num_df.columns:
            s     = stats.loc[col]
            nulls = int(df[col].isnull().sum())
            sk    = skews[col]
            mark  = " ←" if col == target else ""
            print(
                f"  {(col+mark):<{W}}  {nulls:>5}  "
                f"{_fmt(s['min']):>8}  {_fmt(s['25%']):>8}  "
                f"{_fmt(s['mean']):>8}  {_fmt(s['75%']):>8}  "
                f"{_fmt(s['max']):>8}  {_fmt(s['std']):>8}  "
                f"{_skew_label(sk)}"
            )

    # ── Columnas de texto ──────────────────────────────────
    if not txt_df.empty:
        print()
        print("── Columnas de texto ──────────────────────────────────")
        for col in txt_df.columns:
            nulls   = int(df[col].isnull().sum())
            unique  = df[col].nunique()
            top     = df[col].value_counts()
            top_val = top.index[0] if len(top) else '—'
            top_n   = top.iloc[0]  if len(top) else 0
            mark    = " ←" if col == target else ""
            print(f"  {col+mark:<{14}}  {nulls} nulos  "
                  f"{unique} únicos  más frecuente: '{top_val}' ({top_n}×)")

    # ── Hallazgos automáticos ──────────────────────────────
    print()
    print("── Hallazgos ──────────────────────────────────────────")
    findings = []

    total_nulls = int(df.isnull().sum().sum())
    if total_nulls:
        findings.append(f"· {total_nulls} valores nulos en total — considera data-fill")

    for col in num_df.columns:
        sk = skews[col]
        if abs(sk) > 1.0:
            findings.append(f"· '{col}' tiene sesgo alto ({sk:+.2f}) — puede afectar al modelo")

    for col in num_df.columns:
        s = stats.loc[col]
        if s['std'] == 0:
            findings.append(f"· '{col}' es constante (std=0) — no aporta información")

    if len(num_df.columns) > 10:
        findings.append(f"· Muchas columnas numéricas ({len(num_df.columns)}) — considera pat-pca")

    if not findings:
        findings.append("· Sin anomalías estadísticas evidentes")

    for f in findings:
        print(f"  {f}")

    forth._ai['last_op'] = {
        'type': 'pat-find',
        'data': {
            'numeric_cols': list(num_df.columns),
            'text_cols':    list(txt_df.columns),
            'total_nulls':  total_nulls,
        },
        'metrics': {
            'n_numeric': len(num_df.columns),
            'n_text':    len(txt_df.columns),
            'n_nulls':   total_nulls,
        },
    }
