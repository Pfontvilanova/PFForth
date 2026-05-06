# FORTH CODE WORD: code/camera/camzonereset
# Elimina la zona ROI y vuelve a vigilar toda la imagen

WORD_NAME = 'cam-zone-reset'
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
    h   = _load_h(__file__)
    cam = h._ensure_cam(forth)
    cam['zone'] = None
    print("+ Zona ROI eliminada — cam-motion? vigila toda la imagen")
