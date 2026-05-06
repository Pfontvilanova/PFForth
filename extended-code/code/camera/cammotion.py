# FORTH CODE WORD: code/camera/cammotion
# Detecta si hay un objeto nuevo y suficientemente grande en la escena

WORD_NAME = 'cam-motion?'
# === STACK EFFECT ===
# ( min-area -- flag )
#   min-area : area minima del blob en pixeles cuadrados (ej: 500)
#   flag     : -1 si hay movimiento significativo, 0 si no
#
#   Usa MOG2 (cam-bg-init) que aprende el fondo y filtra:
#     - hojas / viento / cambios de luz → ignorados (fondo aprendido)
#     - persona u objeto grande nuevo   → detectado
#   Si cam-bg-init no se llamo, siempre devuelve 0.
#   Respeta la zona ROI definida con cam-zone! si la hay.
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

    min_area = forth.stack.pop() if forth.stack else 500

    if cam.get('bg_sub') is None:
        print("Aviso: cam-bg-init no llamado — cam-motion? siempre devuelve 0")
        forth.stack.append(0)
        return

    frame = cam.get('frame')
    if frame is None:
        forth.stack.append(0)
        return

    try:
        import cv2

        zone = cam.get('zone')
        if zone:
            x1, y1, x2, y2 = zone
            roi = frame[y1:y2, x1:x2]
        else:
            roi = frame

        mask = cam['bg_sub'].apply(roi)

        _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
        mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        max_area = max((cv2.contourArea(c) for c in contours), default=0)

        forth.stack.append(-1 if max_area >= min_area else 0)

    except Exception as e:
        print(f"Error cam-motion?: {e}")
        forth.stack.append(0)
