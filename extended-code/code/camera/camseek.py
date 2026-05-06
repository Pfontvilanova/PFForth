# FORTH CODE WORD: code/camera/camseek
# Salta a una posicion concreta del video

WORD_NAME = 'cam-seek'
# === STACK EFFECT ===
# ( ms -- )  Salta a la posicion en milisegundos.
#            Solo util con archivos de video.
#            Ejemplo: 90000 cam-seek  → salta al minuto 1:30
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

    if not forth.stack:
        print("Error: cam-seek requiere posicion en ms en la pila")
        return

    ms = int(forth.stack.pop())

    if cam.get('cap') is None:
        print("Error: no hay video abierto — usa cam-open primero")
        return

    try:
        import cv2
        cam['cap'].set(cv2.CAP_PROP_POS_MSEC, ms)
        actual = int(cam['cap'].get(cv2.CAP_PROP_POS_MSEC))
        mins   = actual // 60000
        secs   = (actual % 60000) / 1000
        print(f"+ Posicion: {actual} ms  ({mins}:{secs:05.2f})")
    except Exception as e:
        print(f"Error cam-seek: {e}")
