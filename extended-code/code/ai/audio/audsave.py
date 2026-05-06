# FORTH CODE WORD: code/ai/audio/audsave
# Guarda el audio activo en un archivo

WORD_NAME = 'aud-save'
#
# === STACK EFFECT ===
# ( filename -- )  Guarda el audio activo en filename (.wav recomendado)
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('audio', None)
    forth._ai.setdefault('last_op', None)


def execute(forth):
    import os
    _ensure_ai(forth)

    if not forth.stack:
        print("Error: aud-save requiere nombre de archivo en la pila")
        return

    path  = str(forth.stack.pop())
    audio = forth._ai.get('audio')

    if audio is None:
        print("Error: no hay audio activo — usa aud-load primero")
        return

    y, sr = audio

    try:
        import soundfile as sf
        sf.write(path, y, sr)
    except ImportError:
        try:
            import wave, struct, array
            data = array.array('h', [int(v * 32767) for v in y])
            with wave.open(path, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(data.tobytes())
        except Exception as e:
            print(f"Error aud-save: {e}")
            return

    size = os.path.getsize(path)
    duration = len(y) / sr
    print(f"✓ Guardado: {os.path.basename(path)}  ({size} bytes  |  {duration:.2f}s)")

    forth._ai['audio_path'] = path
    forth._ai['last_op'] = {
        'type':    'aud-save',
        'data':    {'path': path},
        'metrics': {'bytes': size, 'duration': round(duration, 2)},
    }
