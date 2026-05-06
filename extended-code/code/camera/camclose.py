# FORTH CODE WORD: code/camera/camclose
# Libera la camara o video activo

WORD_NAME = 'cam-close'
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
        print("(ninguna camara abierta)")
        return
    cam = forth._cam
    if cam.get('cap') is not None:
        cam['cap'].release()
        cam['cap']    = None
        cam['frame']  = None
        cam['source'] = None
        print("+ Camara cerrada")
    else:
        print("(ninguna camara abierta)")
