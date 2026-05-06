# FORTH CODE WORD: code/camera/camzone
# Define la zona de interes (ROI) para cam-motion?

WORD_NAME = 'cam-zone!'
# === STACK EFFECT ===
# ( x1 y1 x2 y2 -- )  Define rectangulo de vigilancia en pixeles.
#                      cam-motion? solo analiza esta zona, ignorando el resto.
#                      Util para ignorar arboles, calle, zona sin interes.
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

    if len(forth.stack) < 4:
        print("Error: cam-zone! requiere x1 y1 x2 y2 en la pila")
        return

    y2 = int(forth.stack.pop())
    x2 = int(forth.stack.pop())
    y1 = int(forth.stack.pop())
    x1 = int(forth.stack.pop())

    if x1 >= x2 or y1 >= y2:
        print(f"Error: zona invalida — x1 < x2 y y1 < y2 requeridos")
        return

    cam['zone'] = (x1, y1, x2, y2)
    print(f"+ Zona ROI definida: x1={x1} y1={y1} x2={x2} y2={y2}")
    print(f"  cam-motion? solo vigilara esa area")
