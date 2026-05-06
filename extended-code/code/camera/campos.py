# FORTH CODE WORD: code/camera/campos
# Devuelve la posicion actual en el video (milisegundos)

WORD_NAME = 'cam-pos'
# === STACK EFFECT ===
# ( -- ms )  Posicion actual en milisegundos.
#            Solo util con archivos de video (cam-open con ruta de archivo).
#            Con camara en vivo devuelve 0.
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

    if cam.get('cap') is None:
        forth.stack.append(0)
        return

    try:
        import cv2
        ms = int(cam['cap'].get(cv2.CAP_PROP_POS_MSEC))
        forth.stack.append(ms)
    except Exception as e:
        print(f"Error cam-pos: {e}")
        forth.stack.append(0)
