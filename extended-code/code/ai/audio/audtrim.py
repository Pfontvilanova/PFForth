# FORTH CODE WORD: code/ai/audio/audtrim
# Elimina silencio del inicio y final del audio activo

WORD_NAME = 'aud-trim'
#
# === STACK EFFECT ===
# ( -- )  Elimina silencio al inicio/final del audio activo (in-place)
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('audio', None)
    forth._ai.setdefault('last_op', None)


def execute(forth):
    _ensure_ai(forth)

    audio = forth._ai.get('audio')
    if audio is None:
        print("Error: no hay audio activo — usa aud-load primero")
        return

    y, sr = audio

    try:
        import librosa
        y_trim, index = librosa.effects.trim(y, top_db=20)
    except ImportError:
        print("Error: aud-trim requiere librosa")
        print("  pip install librosa")
        return

    before   = len(y) / sr
    after    = len(y_trim) / sr
    removed  = before - after

    forth._ai['audio'] = (y_trim, sr)

    print(f"✓ Silencio eliminado:")
    print(f"  Antes: {before:.2f}s  →  Después: {after:.2f}s  (recortado {removed:.2f}s)")

    forth._ai['last_op'] = {
        'type':    'aud-trim',
        'data':    {},
        'metrics': {'before': round(before, 2), 'after': round(after, 2),
                    'removed': round(removed, 2)},
    }
