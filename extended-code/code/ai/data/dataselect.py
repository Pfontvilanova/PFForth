# FORTH CODE WORD: code/ai/data/dataselect
# Selecciona columnas específicas del dataset activo

WORD_NAME = 'data-select'
#
# === STACK EFFECT ===
# ( col1 col2 ... n -- ) Mantiene solo las n columnas indicadas
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
        print("Error: data-select requiere n columnas y un conteo en la pila")
        print("  Uso: \"col1\" \"col2\" 2 data-select")
        return

    n = forth.stack.pop()
    if not isinstance(n, int) or n < 1:
        print(f"Error: el conteo debe ser un entero positivo, recibido: {n}")
        return

    if len(forth.stack) < n:
        print(f"Error: se esperaban {n} nombres de columna en la pila, hay {len(forth.stack)}")
        return

    # Extraer n nombres en orden (el último apilado es el último de la lista)
    selected = []
    for _ in range(n):
        selected.insert(0, forth.stack.pop())

    # Validar que todas existen
    missing = [c for c in selected if c not in df.columns]
    if missing:
        print(f"Error: columnas no encontradas: {', '.join(missing)}")
        print(f"  Disponibles: {', '.join(df.columns)}")
        return

    forth._ai['dataset'] = df[selected].copy()

    # Ajustar target si quedó fuera
    target = forth._ai.get('target_col')
    if target and target not in selected:
        forth._ai['target_col'] = None
        print(f"  (aviso: columna objetivo '{target}' no incluida — se ha borrado)")

    cols_before = list(df.columns)
    print(f"✓ Seleccionadas {n} de {len(cols_before)} columnas:")
    for col in selected:
        marker = " <- objetivo" if col == forth._ai.get('target_col') else ""
        print(f"    {col}{marker}")

    forth._ai['last_op'] = {
        'type':    'data-select',
        'data':    {'selected': selected, 'removed': [c for c in cols_before if c not in selected]},
        'metrics': {'n_before': len(cols_before), 'n_after': n},
    }

    if forth._ai.get('verbose'):
        removed = [c for c in cols_before if c not in selected]
        print()
        print(f"  El dataset ahora tiene solo {n} variables.")
        if removed:
            print(f"  Columnas eliminadas: {', '.join(removed)}")
