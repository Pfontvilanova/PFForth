# FORTH CODE WORD: code/ai/audio/audload
# Carga fichero de audio .wav/.mp3/.flac/.ogg

WORD_NAME = 'aud-load'
#
# === STACK EFFECT ===
# ( filename -- )  Carga fichero de audio como audio activo
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

    if not forth.stack:
        print("Error: aud-load requiere nombre de archivo en la pila")
        return

    path = str(forth.stack.pop())

    try:
        import librosa
        y, sr   = librosa.load(path, sr=None, mono=True)
        method  = 'librosa'
    except ImportError:
        try:
            import soundfile as sf
            import numpy as np
            data, sr = sf.read(path, always_2d=False)
            if data.ndim > 1:
                data = data.mean(axis=1)
            y      = data.astype('float32')
            method = 'soundfile'
        except ImportError:
            print("Error: aud-load requiere librosa o soundfile")
            print("  pip install librosa  o  pip install soundfile")
            return
    except Exception as e:
        print(f"Error aud-load: {e}")
        return

    forth._ai['audio']      = (y, sr)
    forth._ai['audio_path'] = path

    duration = len(y) / sr
    mins, secs = divmod(duration, 60)
    print(f"✓ Audio: {os.path.basename(path)}  [{method}]")
    print(f"  {int(mins)}:{secs:04.1f}  |  {sr} Hz  |  {len(y)} muestras")

    forth._ai['last_op'] = {
        'type':    'aud-load',
        'data':    {'path': path, 'filename': os.path.basename(path), 'method': method},
        'metrics': {'duration': round(duration, 2), 'sr': sr, 'samples': len(y)},
    }
