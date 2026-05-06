# FORTH CODE WORD: code/ai/audio/audwaveform
# Muestra forma de onda ASCII en el terminal

WORD_NAME = 'aud-waveform'
#
# === STACK EFFECT ===
# ( -- )  Dibuja forma de onda del audio activo con caracteres de bloque
# === FIN ===

_BARS = ' ▁▂▃▄▅▆▇█'


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
        import numpy as np
    except ImportError:
        print("Error: aud-waveform requiere numpy")
        return

    cols     = 72
    chunk    = max(1, len(y) // cols)
    amp      = np.array([np.max(np.abs(y[i * chunk:(i + 1) * chunk]))
                         for i in range(cols)])
    peak     = amp.max() or 1.0
    norm     = amp / peak

    upper = ''.join(_BARS[int(v * 8)] for v in norm)
    lower = ''.join(_BARS[int(v * 8)] for v in norm)[::-1]

    duration = len(y) / sr
    mins, secs = divmod(duration, 60)

    print(f"=== Forma de onda ({int(mins)}:{secs:04.1f}  |  {sr} Hz) ===")
    print(f"  +1.0 ┐")
    print(f"       │{upper}")
    print(f"   0.0 ┤{'─' * cols}")
    print(f"       │{lower[::-1]}")
    print(f"  -1.0 ┘")
    print(f"  0s {'─' * (cols - 4)} {duration:.1f}s")

    forth._ai['last_op'] = {
        'type':    'aud-waveform',
        'data':    {},
        'metrics': {'cols': cols, 'duration': round(duration, 2)},
    }
