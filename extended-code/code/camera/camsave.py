# FORTH CODE WORD: code/camera/camsave
# Guarda el frame actual a un archivo de imagen

WORD_NAME = 'cam-save'
# === STACK EFFECT ===
# ( filename -- )  Guarda el frame activo con detecciones superpuestas si las hay.
#                  Formatos: .jpg .png .bmp (segun extension del nombre)
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
        print("Error: cam-save requiere nombre de archivo en la pila")
        return

    filename = str(forth.stack.pop())
    frame    = cam.get('frame')

    if frame is None:
        print("Error: no hay frame — usa cam-read primero")
        return

    try:
        import cv2
        det  = forth._ai.get('detections')
        save = h._draw_detections(frame, det) if det else frame
        ok   = cv2.imwrite(filename, save)
        if ok:
            h_px, w, _ = save.shape
            n = len(det) if det else 0
            print(f"+ Guardado: {filename}  ({w} x {h_px} px)", end='')
            if n:
                print(f"  [{n} detecciones]", end='')
            print()
        else:
            print(f"Error: no se pudo guardar {filename}")
    except Exception as e:
        print(f"Error cam-save: {e}")
