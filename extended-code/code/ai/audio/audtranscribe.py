# FORTH CODE WORD: code/ai/audio/audtranscribe
# Transcribe voz a texto (Whisper local o SpeechRecognition)

WORD_NAME = 'aud-transcribe'
#
# === STACK EFFECT ===
# ( -- text )  Transcribe audio activo a texto; deja string en la pila
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('audio', None)
    forth._ai.setdefault('audio_path', None)
    forth._ai.setdefault('last_op', None)
    forth._ai.setdefault('text', None)


def execute(forth):
    import os, tempfile
    _ensure_ai(forth)

    audio = forth._ai.get('audio')
    if audio is None:
        print("Error: no hay audio activo — usa aud-load primero")
        forth.stack.append('')
        return

    y, sr = audio
    text  = None

    try:
        import whisper
        model_w = forth._ai.get('_whisper_model')
        if model_w is None:
            print("Cargando Whisper tiny (primera vez ~39 MB)...")
            model_w = whisper.load_model('tiny')
            forth._ai['_whisper_model'] = model_w

        path = forth._ai.get('audio_path')
        if not path:
            import soundfile as sf
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            sf.write(tmp.name, y, sr)
            path = tmp.name

        result = model_w.transcribe(path)
        text   = result['text'].strip()
        method = 'Whisper'

    except ImportError:
        try:
            import speech_recognition as sr_lib
            import soundfile as sf

            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            sf.write(tmp.name, y, sr)
            tmp.close()

            recognizer = sr_lib.Recognizer()
            with sr_lib.AudioFile(tmp.name) as src:
                audio_data = recognizer.record(src)
            text   = recognizer.recognize_google(audio_data)
            method = 'SpeechRecognition (Google)'
            os.unlink(tmp.name)

        except ImportError:
            print("Error: aud-transcribe requiere whisper o SpeechRecognition")
            print("  pip install openai-whisper")
            print("  pip install SpeechRecognition soundfile")
            forth.stack.append('')
            return
        except Exception as e:
            print(f"Error aud-transcribe: {e}")
            forth.stack.append('')
            return
    except Exception as e:
        print(f"Error aud-transcribe: {e}")
        forth.stack.append('')
        return

    print(f"✓ Transcripción [{method}]:")
    print(f"  {text}")

    forth._ai['text']     = text
    forth._ai['last_op']  = {
        'type':    'aud-transcribe',
        'data':    {'method': method},
        'metrics': {'chars': len(text), 'words': len(text.split())},
    }
    forth.stack.append(text)
