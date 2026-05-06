# FORTH CODE WORD: code/camera/camwinclose
# Cierra la ventana de visualizacion o para el servidor MJPEG

WORD_NAME = 'cam-window-close'
# === STACK EFFECT ===
# ( -- )
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
    h = _load_h(__file__)
    if not hasattr(forth, '_cam'):
        return
    cam = forth._cam

    if h._has_display():
        try:
            import cv2
            if cam.get('window_open'):
                cv2.destroyWindow(cam['window_name'])
                cam['window_open'] = False
                print("+ Ventana cerrada")
            else:
                print("(ventana ya estaba cerrada)")
        except Exception as e:
            print(f"Error cam-window-close: {e}")
    else:
        if cam.get('mjpeg_running'):
            h._stop_mjpeg_server(forth)
            print("+ Servidor MJPEG detenido")
        else:
            print("(servidor MJPEG no estaba activo)")
