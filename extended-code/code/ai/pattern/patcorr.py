# FORTH CODE WORD: code/ai/pattern/patcorr
# Correlación entre columnas numéricas, destacando relación con el objetivo

WORD_NAME = 'pat-corr'
#
# === STACK EFFECT ===
# ( -- ) Muestra correlaciones y señala columnas redundantes
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


def _bar(v, width=12):
    """Barra de correlación centrada: negativo ◄, positivo ►"""
    mid  = width // 2
    fill = round(abs(v) * mid)
    fill = min(fill, mid)
    if v >= 0:
        return '·' * mid + '█' * fill + '░' * (mid - fill)
    else:
        return '░' * (mid - fill) + '█' * fill + '·' * mid


def _strength(v):
    a = abs(v)
    if a >= 0.9: return "muy alta"
    if a >= 0.7: return "alta    "
    if a >= 0.5: return "media   "
    if a >= 0.3: return "baja    "
    return             "muy baja"


def execute(forth):
    _ensure_ai(forth)

    df = forth._ai.get('dataset')
    if df is None:
        print("Error: no hay dataset cargado — usa data-load primero")
        return

    num_df = df.select_dtypes(include='number')
    if num_df.shape[1] < 2:
        print("Error: se necesitan al menos 2 columnas numéricas")
        return

    target = forth._ai.get('target_col')
    corr   = num_df.corr()

    print("=== PAT-CORR: Análisis de correlaciones ===")

    # ── Sección 1: correlación con el objetivo ─────────────
    if target and target in corr.columns:
        print()
        print(f"── Relación con el objetivo '{target}' ────────────────")
        col_corrs = (corr[target]
                     .drop(labels=[target])
                     .sort_values(key=abs, ascending=False))

        W = max(len(c) for c in col_corrs.index)
        for col, val in col_corrs.items():
            sign = '+' if val >= 0 else '-'
            bar  = _bar(val)
            print(f"  {col:<{W}}  {sign}{abs(val):.3f}  {bar}  {_strength(val)}")

        # Consejo rápido
        print()
        best = col_corrs.index[0]
        if abs(col_corrs.iloc[0]) > 0.7:
            print(f"  → '{best}' es el predictor más fuerte del objetivo")
        low = [c for c in col_corrs.index if abs(col_corrs[c]) < 0.1]
        if low:
            print(f"  → Columnas con correlación casi nula: {', '.join(low)}")
            print(f"    (considera eliminarlas con data-drop)")

    # ── Sección 2: pares con alta correlación mutua ────────
    print()
    print("── Pares con alta correlación entre variables ─────────")
    cols   = [c for c in corr.columns if c != target]
    found  = []
    pairs  = []

    for i, c1 in enumerate(cols):
        for c2 in cols[i+1:]:
            v = corr.loc[c1, c2]
            if abs(v) >= 0.7:
                pairs.append((c1, c2, v))

    pairs.sort(key=lambda x: abs(x[2]), reverse=True)

    if pairs:
        for c1, c2, v in pairs:
            sign = '+' if v >= 0 else '-'
            bar  = _bar(v)
            print(f"  {c1} ↔ {c2}:  {sign}{abs(v):.3f}  {bar}  {_strength(v)}")
            found.extend([c1, c2])
        redundant = list(dict.fromkeys(found))   # únicos, en orden
        print()
        print(f"  → Variables posiblemente redundantes: {', '.join(redundant)}")
        print(f"    Si dos variables se correlacionan >0.9 entre sí,")
        print(f"    considera eliminar una con data-drop")
    else:
        print("  Ningún par supera correlación 0.7 — variables independientes")

    # ── Sección 3: tabla compacta completa ────────────────
    verbose = forth._ai.get('verbose', False)
    if verbose:
        print()
        print("── Matriz completa ────────────────────────────────────")
        cols_all = list(corr.columns)
        W2 = max(len(c) for c in cols_all)
        header = ' ' * (W2 + 2) + '  '.join(f"{c[:6]:>6}" for c in cols_all)
        print(f"  {header}")
        for row in cols_all:
            vals = '  '.join(
                f"{'  —   ' if row == col else f'{corr.loc[row,col]:+.2f} ':>6}"
                for col in cols_all
            )
            print(f"  {row:<{W2}}  {vals}")

    forth._ai['last_op'] = {
        'type': 'pat-corr',
        'data': {
            'target':  target,
            'pairs':   [(c1, c2, round(v, 3)) for c1, c2, v in pairs],
        },
        'metrics': {
            'n_high_pairs': len(pairs),
            'n_numeric':    len(num_df.columns),
        },
    }
