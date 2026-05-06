# FORTH CODE WORD: code/camera/camshow
# Muestra el frame actual en ventana (no bloquea)

WORD_NAME = 'cam-show'
# === STACK EFFECT ===
# ( -- )  Muestra forth._ai['image'] con detecciones superpuestas si las hay.
#         En iPad inicia el servidor MJPEG si no estaba activo.
#         No bloquea: devuelve control inmediatamente.
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


def execute(forth):
    h   = _load_h(__file__)
    cam = h._ensure_cam(forth)

    frame = cam.get('frame')
    if frame is None:
        print("Error: no hay frame — usa cam-read primero")
        return

    try:
        import cv2
    except ImportError:
        print("Error: opencv-python no instalado")
        return

    det   = forth._ai.get('detections')
    disp  = h._draw_detections(frame, det) if det else frame

    if h._has_display():
        win = cam['window_name']
        if not cam['window_open']:
            cv2.namedWindow(win, cv2.WINDOW_NORMAL)
            cam['window_open'] = True
        cv2.imshow(win, disp)
        cv2.waitKey(1)
    else:
        if not cam.get('mjpeg_running'):
            port = cam.get('mjpeg_port', 8765)
            srv = h._start_mjpeg_server(forth, port)
            if srv is not None:
                print(f"Stream MJPEG listo:")
                print(f"  http://127.0.0.1:{port}")
                print(f"  http://localhost:{port}")
                print("  Abre una de esas URLs en Safari")
