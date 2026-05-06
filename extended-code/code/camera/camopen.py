# FORTH CODE WORD: code/camera/camopen
# Abre una camara, stream IP, ESP32-CAM o archivo de video

WORD_NAME = 'cam-open'
# === STACK EFFECT ===
# ( source -- )
#   source: entero 0..N = camara local
#           string = URL RTSP / HTTP / ruta de archivo MP4 MOV AVI etc.
# === FIN ===

import os
import sys


def _load_h(caller_file):
    key = '_cam_helper'
    if key in sys.modules:
        return sys.modules[key]
    import importlib.util
    here  = os.path.dirname(os.path.abspath(caller_file))
    fpath = os.path.join(here, '_cam.py')
    spec  = importlib.util.spec_from_file_location(key, fpath)
    mod   = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _resolve_path(src):
    """
    Busca el archivo en varios directorios habituales.
    Devuelve la ruta completa si existe, o None.
    """
    candidates = [
        src,
        os.path.join(os.getcwd(), src),
        os.path.join(os.path.expanduser('~'), src),
        os.path.join(os.path.expanduser('~'), 'Documents', src),
        os.path.join(os.path.expanduser('~'), 'pfforth', src),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return os.path.abspath(c)
    return None


def execute(forth):
    if not forth.stack:
        print("Error: cam-open requiere fuente en la pila")
        print("  0 cam-open                          (camara local)")
        print('  s" rtsp://ip/stream" cam-open        (camara IP RTSP)')
        print('  s" http://ip:81/stream" cam-open     (ESP32-CAM)')
        print('  s" video.mp4" cam-open               (archivo de video)')
        return

    h   = _load_h(__file__)
    cam = h._ensure_cam(forth)

    try:
        import cv2
    except ImportError:
        print("Error: opencv-python no instalado — pip install opencv-python")
        return

    source = forth.stack.pop()

    if cam['cap'] is not None:
        cam['cap'].release()
        cam['cap']   = None
        cam['frame'] = None

    try:
        if isinstance(source, int):
            cap       = cv2.VideoCapture(source)
            src_label = f"camara local #{source}"
            resolved  = None
        else:
            src = str(source)

            if src.startswith('rtsp://') or src.startswith('http://') or src.startswith('https://'):
                cap       = cv2.VideoCapture(src)
                src_label = src
                resolved  = None
            else:
                resolved = _resolve_path(src)
                if resolved is None:
                    print(f"Error: archivo no encontrado — '{src}'")
                    print(f"  Directorio actual: {os.getcwd()}")
                    print(f"  Prueba con la ruta completa, por ejemplo:")
                    print(f'    s" {os.path.join(os.getcwd(), src)}" cam-open')
                    ext = os.path.splitext(src)[1].lower()
                    if ext in ('.mov', '.m4v', '.hevc', '.heic'):
                        print(f"  Nota: formato {ext} puede necesitar conversion en Linux.")
                        print(f"  Convierte con: ffmpeg -i {src} salida.mp4")
                    return
                cap       = cv2.VideoCapture(resolved)
                src_label = f"archivo: {os.path.basename(resolved)}"
                ext = os.path.splitext(resolved)[1].lower()
                if ext in ('.mov', '.m4v') and sys.platform.startswith('linux'):
                    print(f"  Aviso: formato {ext} puede no abrirse en Linux sin ffmpeg.")
                    print(f"  Si falla, convierte con: ffmpeg -i {resolved} salida.mp4")

        if not cap.isOpened():
            print(f"Error: no se pudo abrir — {src_label}")
            if resolved:
                print(f"  Ruta completa: {resolved}")
                ext = os.path.splitext(resolved)[1].lower()
                if ext in ('.mov', '.m4v') and sys.platform.startswith('linux'):
                    print(f"  El formato .mov necesita ffmpeg en Linux.")
                    print(f"  Convierte: ffmpeg -i \"{resolved}\" salida.mp4")
            return

        cam['cap']    = cap
        cam['source'] = resolved or source
        cam['frame']  = None

        w     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        ht    = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps   = cap.get(cv2.CAP_PROP_FPS)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"+ Abierto: {src_label}")
        if resolved:
            print(f"  Ruta: {resolved}")
        print(f"  {w} x {ht} px  |  {fps:.1f} fps", end='')
        if total > 0:
            secs = total / fps if fps > 0 else 0
            print(f"  |  {total} frames  ({secs:.1f} s)", end='')
        print()

    except Exception as e:
        print(f"Error cam-open: {e}")
