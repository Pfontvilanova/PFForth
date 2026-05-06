# FORTH CODE WORD: code/camera/camread
# Lee el siguiente frame de la camara o video activo

WORD_NAME = 'cam-read'
# === STACK EFFECT ===
# ( -- flag )  flag = -1 si hay frame, 0 si fin de video o error
#              El frame queda en forth._ai['image'] (PIL Image)
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

    if cam['cap'] is None:
        print("Error: no hay camara abierta — usa cam-open primero")
        forth.stack.append(0)
        return

    try:
        import cv2
        ret, frame = cam['cap'].read()
        if not ret:
            forth.stack.append(0)
            return

        cam['frame']          = frame
        forth._ai['image']    = h._frame_to_pil(frame)
        forth._ai['detections'] = None
        forth.stack.append(-1)

    except Exception as e:
        print(f"Error cam-read: {e}")
        forth.stack.append(0)
