# FORTH CODE WORD: code/ai/text/txtgenerate
# Genera texto con GPT-2 local

WORD_NAME = 'txt-generate'
#
# === STACK EFFECT ===
# (  prompt maxlen -- text ) Genera texto con GPT-2 local
# === FIN ===


def _ensure_ai(forth):
    """Inicializa el estado AI si no existe."""
    if not hasattr(forth, '_ai'):
        forth._ai = {
            'dataset':    None,
            'target_col': None,
            'train_set':  None,
            'test_set':   None,
            'model':      None,
            'last_op':    None,
            'verbose':    False,
            'image':      None,
            'audio':      None,
            'clip_model': None,
            'yolo_model': None,
        }


def execute(forth):
    _ensure_ai(forth)

    if len(forth.stack) < 2:
        print("Error: txt-generate requiere ( prompt maxlen ) en la pila")
        forth.stack.append('')
        return

    maxlen = int(forth.stack.pop())
    prompt = str(forth.stack.pop())

    try:
        from transformers import pipeline
        gen = forth._ai.get('_gen_pipeline')
        if gen is None:
            print("Cargando GPT-2 (primera vez ~500 MB)...")
            gen = pipeline('text-generation', model='gpt2')
            forth._ai['_gen_pipeline'] = gen
        result = gen(prompt, max_new_tokens=maxlen, num_return_sequences=1)[0]['generated_text']
        method = 'GPT-2'
    except ImportError:
        print("Error: txt-generate requiere transformers")
        print("  pip install transformers")
        forth.stack.append('')
        return
    except Exception as e:
        print(f"Error txt-generate: {e}")
        forth.stack.append('')
        return

    print(f"✓ Generado ({method}):")
    print(f"  {result}")

    forth._ai['last_op'] = {
        'type':    'txt-generate',
        'data':    {'prompt': prompt, 'method': method},
        'metrics': {'chars': len(result)},
    }
    forth.stack.append(result)
