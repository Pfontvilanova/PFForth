# FORTH CODE WORD: code/camera/cambginit
# Inicializa el modelo de fondo adaptativo MOG2 para deteccion de movimiento

WORD_NAME = 'cam-bg-init'
# === STACK EFFECT ===
# ( -- )  Crea el sustractor de fondo MOG2.
#         Los primeros ~500 frames sirven para aprender el fondo normal.
#         Util tanto para interior como para exterior (viento, luces, etc.)
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

    try:
        import cv2
    except ImportError:
        print("Error: opencv-python no instalado")
        return

    cam['bg_sub'] = cv2.createBackgroundSubtractorMOG2(
        history=500,
        varThreshold=16,
        detectShadows=True,
    )
    print("+ Modelo de fondo MOG2 inicializado")
    print("  Los primeros ~500 frames seran de aprendizaje automatico")
    print("  Funciona en exterior: ignora viento, nubes y cambios de luz")
