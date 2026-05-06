# FORTH CODE WORD: code/ai/pattern/patsequence
# Analiza tendencias temporales en una columna numérica

WORD_NAME = 'pat-sequence'
#
# === STACK EFFECT ===
# ( colname -- ) Tendencia, autocorrelación, cambios bruscos y sparkline
# === FIN ===

_SPARK = '▁▂▃▄▅▆▇█'


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {
            'dataset': None, 'target_col': None,
            'train_set': None, 'test_set': None,
            'model': None, 'last_op': None,
            'verbose': False, 'image': None,
            'audio': None, 'clip_model': None, 'yolo_model': None,
        }


def _sparkline(values, width=40):
    """Genera una línea de caracteres de bloque que representa la serie."""
    lo, hi = min(values), max(values)
    rng    = hi - lo if hi != lo else 1
    levels = len(_SPARK)
    chars  = []
    step   = max(1, len(values) // width)
    for i in range(0, len(values), step):
        v = values[i]
        idx = int((v - lo) / rng * (levels - 1))
        chars.append(_SPARK[idx])
    return ''.join(chars)


def _trend_label(slope_norm):
    """Interpreta la pendiente normalizada."""
    if slope_norm >  0.05: return "creciente  ↑"
    if slope_norm < -0.05: return "decreciente ↓"
    return                         "estable    →"


def _autocorr(series, lag):
    """Autocorrelación simple en un lag dado."""
    if len(series) <= lag:
        return 0.0
    s  = series
    s1 = s[:-lag]
    s2 = s[lag:]
    mean1, mean2 = s1.mean(), s2.mean()
    num  = ((s1 - mean1) * (s2 - mean2)).sum()
    den  = (((s1 - mean1)**2).sum() * ((s2 - mean2)**2).sum()) ** 0.5
    return float(num / den) if den != 0 else 0.0


def execute(forth):
    _ensure_ai(forth)

    df = forth._ai.get('dataset')
    if df is None:
        print("Error: no hay dataset cargado — usa data-load primero")
        return

    if not forth.stack:
        print("Error: pat-sequence requiere el nombre de columna en la pila")
        print("  Uso: s\" ventas\" pat-sequence")
        return

    col = forth.stack.pop()
    if col not in df.columns:
        print(f"Error: columna '{col}' no encontrada")
        print(f"  Disponibles: {', '.join(df.columns)}")
        return

    if col not in df.select_dtypes(include='number').columns:
        print(f"Error: '{col}' no es numérica — pat-sequence solo analiza números")
        return

    series = df[col].dropna().reset_index(drop=True)
    n      = len(series)

    if n < 4:
        print(f"Error: '{col}' tiene solo {n} valores — se necesitan al menos 4")
        return

    import numpy as np

    vals  = series.values.astype(float)
    mean  = float(vals.mean())
    std   = float(vals.std())
    rng   = float(vals.max() - vals.min())

    # Tendencia lineal (regresión mínimos cuadrados)
    x         = np.arange(n, dtype=float)
    slope, intercept = np.polyfit(x, vals, 1)
    slope_norm = slope / (rng if rng != 0 else 1)   # normalizada al rango

    # Predicción al final de la serie (extrapolación simple)
    pred_next = intercept + slope * n

    # Autocorrelación en lags 1, 2, 3
    ac1 = _autocorr(series, 1)
    ac2 = _autocorr(series, 2)
    ac3 = _autocorr(series, 3)

    # Variación entre puntos consecutivos
    diffs    = np.diff(vals)
    avg_chg  = float(np.abs(diffs).mean())
    max_chg  = float(np.abs(diffs).max())
    chg_pct  = avg_chg / (mean if mean != 0 else 1) * 100

    # Cambios bruscos (donde la variación supera 2×std de los diffs)
    diff_std   = diffs.std()
    jumps      = [(i+1, float(diffs[i])) for i in range(len(diffs))
                  if abs(diffs[i]) > 2 * diff_std]

    # Monotonía
    n_up   = int((diffs > 0).sum())
    n_down = int((diffs < 0).sum())
    if n_up   == n-1: mono = "siempre creciente (monotónica ↑)"
    elif n_down == n-1: mono = "siempre decreciente (monotónica ↓)"
    elif n_up > 0.8*(n-1): mono = "mayormente creciente"
    elif n_down > 0.8*(n-1): mono = "mayormente decreciente"
    else: mono = "oscilante"

    # Coeficiente de variación
    cv = std / abs(mean) * 100 if mean != 0 else 0

    print(f"=== PAT-SEQUENCE: '{col}' ({n} puntos) ===")
    print()

    # Sparkline
    spark = _sparkline(list(vals))
    print(f"  {spark}")
    print(f"  min={vals.min():.3g}  max={vals.max():.3g}  "
          f"media={mean:.3g}  std={std:.3g}")
    print()

    print(f"── Tendencia ──────────────────────────────────────────")
    print(f"  Dirección    : {_trend_label(slope_norm)}")
    print(f"  Pendiente    : {slope:+.4g} por paso")
    print(f"  Patrón       : {mono}")
    print(f"  Siguiente    : ~{pred_next:.3g}  (extrapolación lineal)")
    print()

    print(f"── Variabilidad ───────────────────────────────────────")
    print(f"  Variación media : {avg_chg:.3g} por paso  ({chg_pct:.1f}% de la media)")
    print(f"  Variación máx.  : {max_chg:.3g}")
    print(f"  Coef. variación : {cv:.1f}%  "
          f"({'alta' if cv > 30 else 'media' if cv > 10 else 'baja'})")
    print()

    print(f"── Autocorrelación ────────────────────────────────────")
    for lag, ac in [(1, ac1), (2, ac2), (3, ac3)]:
        bar = '█' * round(abs(ac) * 10) + '░' * (10 - round(abs(ac) * 10))
        lbl = ("alta" if abs(ac) > 0.7 else
               "media" if abs(ac) > 0.4 else "baja")
        sign = '+' if ac >= 0 else '-'
        print(f"  Lag {lag}: {sign}{abs(ac):.3f}  {bar}  {lbl}")

    if abs(ac1) > 0.7:
        print(f"  → Autocorrelación alta: el valor siguiente depende mucho del actual")
        print(f"    (patrón repetitivo o tendencia fuerte)")
    elif abs(ac1) < 0.2:
        print(f"  → Autocorrelación baja: valores casi independientes entre sí (ruido)")

    if jumps:
        print()
        print(f"── Cambios bruscos ({len(jumps)}) ─────────────────────────────")
        for pos, delta in jumps[:5]:
            arrow = "↑" if delta > 0 else "↓"
            print(f"  Posición {pos:>3}: {arrow}{abs(delta):.3g}  "
                  f"(de {vals[pos-1]:.3g} → {vals[pos]:.3g})")
        if len(jumps) > 5:
            print(f"  ... ({len(jumps)-5} más)")

    forth._ai['last_op'] = {
        'type': 'pat-sequence',
        'data': {
            'column':   col,
            'n':        n,
            'trend':    _trend_label(slope_norm),
            'pattern':  mono,
        },
        'metrics': {
            'slope':    round(slope, 6),
            'ac1':      round(ac1, 4),
            'cv_pct':   round(cv, 2),
            'n_jumps':  len(jumps),
        },
    }
