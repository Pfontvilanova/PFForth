# FORTH CODE WORD: code/ai/data/datasplit
# Divide el dataset en conjuntos de entrenamiento y prueba

WORD_NAME = 'data-split'
#
# === STACK EFFECT ===
# ( ratio -- ) Divide en train/test; ratio es la fracción de test (p.ej. 0.2)
#              Deja en la pila: train_rows test_rows
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


def execute(forth):
    _ensure_ai(forth)

    df = forth._ai.get('dataset')
    if df is None:
        print("Error: no hay dataset cargado — usa data-load primero")
        return

    if not forth.stack:
        print("Error: data-split requiere un ratio en la pila")
        print("  Uso: 0.2 data-split   (20% test, 80% entrenamiento)")
        return

    ratio = forth.stack.pop()
    try:
        ratio = float(ratio)
    except (TypeError, ValueError):
        print(f"Error: ratio debe ser un número entre 0 y 1, recibido: {ratio}")
        return

    if not 0.0 < ratio < 1.0:
        print(f"Error: ratio debe estar entre 0 y 1 exclusivos (recibido {ratio})")
        return

    target = forth._ai.get('target_col')

    try:
        from sklearn.model_selection import train_test_split

        if target and target in df.columns:
            y = df[target]
            # Estratificado si hay pocas clases (clasificación)
            n_unique = y.nunique()
            stratify = y if n_unique <= 20 else None
            train_df, test_df = train_test_split(
                df, test_size=ratio, random_state=42, stratify=stratify
            )
            strat_label = "estratificado" if stratify is not None else "aleatorio"
        else:
            train_df, test_df = train_test_split(df, test_size=ratio, random_state=42)
            strat_label = "aleatorio"

    except Exception as e:
        print(f"Error al dividir: {e}")
        return

    train_df = train_df.reset_index(drop=True)
    test_df  = test_df.reset_index(drop=True)

    forth._ai['train_set'] = train_df
    forth._ai['test_set']  = test_df

    n_train = len(train_df)
    n_test  = len(test_df)
    n_total = len(df)

    print(f"✓ División {strat_label}:")
    print(f"    Entrenamiento : {n_train} filas  ({100*(1-ratio):.0f}%)")
    print(f"    Prueba        : {n_test} filas  ({100*ratio:.0f}%)")
    if target:
        print(f"    Objetivo      : '{target}'")

    # Deja tamaños en la pila para uso posterior
    forth.stack.append(n_train)
    forth.stack.append(n_test)

    forth._ai['last_op'] = {
        'type':    'data-split',
        'data':    {'ratio': ratio, 'strategy': strat_label, 'target': target},
        'metrics': {'n_train': n_train, 'n_test': n_test, 'n_total': n_total},
    }

    if forth._ai.get('verbose'):
        print()
        print(f"  El {100*(1-ratio):.0f}% de los datos se usará para entrenar el modelo.")
        print(f"  El {100*ratio:.0f}% restante se reserva para medir su rendimiento real.")
        if strat_label == "estratificado":
            print(f"  La división mantiene la misma proporción de clases en cada parte.")
