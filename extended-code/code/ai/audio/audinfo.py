# FORTH CODE WORD: code/ai/audio/audinfo
# Muestra información del audio activo

WORD_NAME = 'aud-info'
#
# === STACK EFFECT ===
# ( -- )  Muestra duración, sr, muestras, amplitud máxima
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('audio', None)
    forth._ai.setdefault('audio_path', None)
    forth._ai.setdefault('last_op', None)


def execute(forth):
    import os
    _ensure_ai(forth)

    audio = forth._ai.get('audio')
    if audio is None:
        print("Error: no hay audio activo — usa aud-load primero")
        return

    y, sr    = audio
    path     = forth._ai.get('audio_path', '')
    duration = len(y) / sr
    mins, secs = divmod(duration, 60)

    try:
        import numpy as np
        amp_max  = float(np.max(np.abs(y)))
        amp_rms  = float(np.sqrt(np.mean(y ** 2)))
    except Exception:
        amp_max  = max(abs(float(v)) for v in y)
        amp_rms  = (sum(float(v)**2 for v in y) / len(y)) ** 0.5

    print(f"=== Audio activo ===")
    if path:
        print(f"  Archivo    : {os.path.basename(path)}")
    print(f"  Duración   : {int(mins)}:{secs:04.1f}  ({duration:.2f}s)")
    print(f"  Frecuencia : {sr} Hz")
    print(f"  Muestras   : {len(y)}")
    print(f"  Amplitud   : máx={amp_max:.4f}  RMS={amp_rms:.4f}")

    forth._ai['last_op'] = {
        'type':    'aud-info',
        'data':    {'path': path},
        'metrics': {'duration': round(duration, 2), 'sr': sr,
                    'amp_max': round(amp_max, 4), 'amp_rms': round(amp_rms, 4)},
    }
