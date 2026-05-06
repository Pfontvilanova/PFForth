# FORTH CODE WORD: code/camera/caminfo
# Muestra informacion sobre la fuente de camara activa

WORD_NAME = 'cam-info'
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

    if cam['cap'] is None:
        print("(ninguna camara abierta)")
        return

    try:
        import cv2
        cap   = cam['cap']
        w     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        ht    = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps   = cap.get(cv2.CAP_PROP_FPS)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        pos   = int(cap.get(cv2.CAP_PROP_POS_MSEC))
        try:
            backend = cap.getBackendName()
        except Exception:
            backend = 'desconocido'

        print("=== cam-info ===")
        print(f"  Fuente     : {cam['source']}")
        print(f"  Resolucion : {w} x {ht} px")
        print(f"  FPS        : {fps:.1f}")
        print(f"  Backend    : {backend}")
        if total > 0:
            dur = total / fps if fps > 0 else 0
            print(f"  Duracion   : {total} frames  ({dur:.1f} s)")
            mins = int(pos // 60000)
            secs = (pos % 60000) / 1000
            print(f"  Posicion   : {pos} ms  ({mins}:{secs:05.2f})")
        print(f"  MOG2 activo: {'si' if cam.get('bg_sub') else 'no'}")
        zone = cam.get('zone')
        if zone:
            print(f"  Zona ROI   : x1={zone[0]} y1={zone[1]} x2={zone[2]} y2={zone[3]}")
        else:
            print("  Zona ROI   : toda la imagen")
        display = h._has_display()
        print(f"  Modo ventana: {'cv2.imshow' if display else 'MJPEG HTTP'}")
        if not display and cam.get('mjpeg_running'):
            print(f"  MJPEG URL  : http://localhost:{cam['mjpeg_port']}")

    except Exception as e:
        print(f"Error cam-info: {e}")
