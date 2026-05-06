# FORTH CODE WORD: code/ai/audio/audpitch
# Estima la frecuencia fundamental del audio activo

WORD_NAME = 'aud-pitch'
#
# === STACK EFFECT ===
# ( -- hz )  Frecuencia fundamental en Hz (float) en la pila
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('audio', None)
    forth._ai.setdefault('last_op', None)


def _hz_to_note(hz):
    if hz <= 0:
        return '?'
    import math
    notes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    semis = 12 * math.log2(hz / 440.0) + 57
    idx   = int(round(semis)) % 12
    octave = (int(round(semis)) // 12)
    return f"{notes[idx]}{octave}"


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
        f0, voiced_flag, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'), sr=sr)
        voiced = f0[voiced_flag] if voiced_flag is not None else f0
        voiced = voiced[~np.isnan(voiced)]
        hz     = float(np.median(voiced)) if len(voiced) > 0 else 0.0
        method = 'pYIN'
    except Exception:
        try:
            import librosa
            import numpy as np
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            idx = int(np.argmax(magnitudes))
            hz  = float(pitches.flat[idx])
            method = 'piptrack'
        except ImportError:
            print("Error: aud-pitch requiere librosa")
            print("  pip install librosa")
            forth.stack.append(0.0)
            return

    hz   = round(hz, 2)
    note = _hz_to_note(hz) if hz > 0 else '?'
    print(f"✓ Pitch fundamental: {hz:.1f} Hz  ({note})  [{method}]")

    forth._ai['last_op'] = {
        'type':    'aud-pitch',
        'data':    {'method': method},
        'metrics': {'hz': hz, 'note': note},
    }
    forth.stack.append(hz)
