# FORTH CODE WORD: code/ai/audio/audtempo
# Detecta el tempo (BPM) del audio activo

WORD_NAME = 'aud-tempo'
#
# === STACK EFFECT ===
# ( -- bpm )  Deja el tempo en BPM (float) en la pila
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
        forth.stack.append(0.0)
        return

    y, sr = audio

    try:
        import librosa
        import numpy as np
        tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(np.atleast_1d(tempo_arr)[0])
    except ImportError:
        print("Error: aud-tempo requiere librosa")
        print("  pip install librosa")
        forth.stack.append(0.0)
        return
    except Exception as e:
        print(f"Error aud-tempo: {e}")
        forth.stack.append(0.0)
        return

    bpm = round(bpm, 1)

    if bpm < 60:
        tipo = "lento (adagio)"
    elif bpm < 90:
        tipo = "moderado (andante)"
    elif bpm < 120:
        tipo = "normal (moderato)"
    elif bpm < 160:
        tipo = "rápido (allegro)"
    else:
        tipo = "muy rápido (presto)"

    print(f"✓ Tempo: {bpm:.1f} BPM  ({tipo})")

    forth._ai['last_op'] = {
        'type':    'aud-tempo',
        'data':    {},
        'metrics': {'bpm': bpm},
    }
    forth.stack.append(bpm)
