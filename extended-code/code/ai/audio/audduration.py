# FORTH CODE WORD: code/ai/audio/audduration
# Deja duración del audio activo en segundos en la pila

WORD_NAME = 'aud-duration'
#
# === STACK EFFECT ===
# ( -- seconds )  Duración del audio activo en segundos (float)
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('audio', None)


def execute(forth):
    _ensure_ai(forth)

    audio = forth._ai.get('audio')
    if audio is None:
        print("Error: no hay audio activo — usa aud-load primero")
        forth.stack.append(0.0)
        return

    y, sr    = audio
    duration = round(len(y) / sr, 3)
    forth.stack.append(duration)
