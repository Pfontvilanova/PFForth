# FORTH CODE WORD: code/camera/camperson
# Detecta si hay una persona en el frame activo

WORD_NAME = 'cam-person?'
# === STACK EFFECT ===
# ( -- flag )  flag = -1 si hay al menos una persona, 0 si no
#              Requiere cam-read previo (imagen en forth._ai['image'])
#
#   Motor 1 (preferido): reutiliza img-detect (YOLOv5n ONNX)
#                        si el modulo ai/vision ya esta cargado
#   Motor 2 (fallback):  HOG de OpenCV, sin dependencias extra
# === FIN ===

import os
import sys
import importlib.util


def _load_h(caller_file):
    key = '_cam_helper'
    if key in sys.modules:
        return sys.modules[key]
    here  = os.path.dirname(os.path.abspath(caller_file))
    fpath = os.path.join(here, '_cam.py')
    spec  = importlib.util.spec_from_file_location(key, fpath)
    mod   = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_imgdetect():
    """Carga el modulo imgdetect del vocabulario vision (ya probado y funcional)."""
    key = '_imgdetect_mod'
    if key in sys.modules:
        return sys.modules[key]
    here  = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.normpath(os.path.join(here, '..', 'ai', 'vision', 'imgdetect.py'))
    if not os.path.isfile(fpath):
        return None
    spec = importlib.util.spec_from_file_location(key, fpath)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _run_hog(forth):
    """
    Detector HOG integrado en OpenCV.
    No necesita onnxruntime ni modelos externos.
    Menos preciso que YOLO pero funciona en cualquier plataforma.
    """
    import cv2
    cam   = getattr(forth, '_cam', {})
    frame = cam.get('frame')
    if frame is None:
        forth.stack.append(0)
        return

    hog = getattr(forth, '_cam_hog', None)
    if hog is None:
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        forth._cam_hog = hog

    try:
        h_px, w, _ = frame.shape
        scale = min(1.0, 640 / max(w, h_px))
        small = cv2.resize(frame, (int(w * scale), int(h_px * scale)))

        boxes, weights = hog.detectMultiScale(
            small, winStride=(8, 8), padding=(8, 8), scale=1.05,
        )

        detections = []
        if len(boxes) > 0:
            for i, (x, y, bw, bh) in enumerate(boxes):
                conf = float(weights[i]) if i < len(weights) else 0.5
                detections.append({
                    'label': 'person',
                    'conf':  round(min(conf / 2.0, 1.0), 2),
                    'box':   [round(x / scale), round(y / scale),
                              round((x + bw) / scale), round((y + bh) / scale)],
                })

        forth._ai['detections'] = detections
        forth.stack.append(-1 if detections else 0)

    except Exception as e:
        print(f"Error cam-person? (HOG): {e}")
        forth.stack.append(0)


def execute(forth):
    _load_h(__file__)

    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai.setdefault('image', None)
    forth._ai.setdefault('detections', None)

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa cam-read primero")
        forth.stack.append(0)
        return

    # --- Motor 1: YOLO via imgdetect (solo si onnxruntime esta disponible) ---
    _onnx_ok = False
    try:
        import onnxruntime  # noqa: F401
        _onnx_ok = True
    except ImportError:
        pass

    if _onnx_ok:
        imgdetect = _load_imgdetect()
        if imgdetect is not None:
            try:
                imgdetect.execute(forth)    # deja n detecciones en pila
                n = forth.stack.pop()       # retira el conteo
                detections = forth._ai.get('detections') or []
                has_person = any(d['label'] == 'person' for d in detections)
                forth.stack.append(-1 if has_person else 0)
                return
            except Exception as e:
                if not getattr(forth, '_camperson_yolo_warned', False):
                    print(f"Aviso cam-person?: YOLO fallo ({e}) — usando HOG")
                    forth._camperson_yolo_warned = True

    # --- Motor 2: HOG (no necesita onnxruntime, solo OpenCV) ---
    if not getattr(forth, '_camperson_hog_warned', False):
        print("cam-person?: usando detector HOG (OpenCV)")
        forth._camperson_hog_warned = True
    _run_hog(forth)
