# FORTH CODE WORD: code/ai/vision/imgdetect
# Detecta objetos con YOLOv8n ONNX (sin PyTorch)

WORD_NAME = 'img-detect'
#
# === STACK EFFECT ===
# ( -- n )  Detecta objetos en imagen activa, deja cantidad en pila
#           Resultados en forth._ai['detections']
#           Motor: YOLOv8n ONNX  (se descarga ~6 MB la primera vez)
# === FIN ===

import os
import sys
import importlib.util

COCO_CLASSES = [
    'person','bicycle','car','motorcycle','airplane','bus','train','truck',
    'boat','traffic light','fire hydrant','stop sign','parking meter','bench',
    'bird','cat','dog','horse','sheep','cow','elephant','bear','zebra',
    'giraffe','backpack','umbrella','handbag','tie','suitcase','frisbee',
    'skis','snowboard','sports ball','kite','baseball bat','baseball glove',
    'skateboard','surfboard','tennis racket','bottle','wine glass','cup',
    'fork','knife','spoon','bowl','banana','apple','sandwich','orange',
    'broccoli','carrot','hot dog','pizza','donut','cake','chair','couch',
    'potted plant','bed','dining table','toilet','tv','laptop','mouse',
    'remote','keyboard','cell phone','microwave','oven','toaster','sink',
    'refrigerator','book','clock','vase','scissors','teddy bear',
    'hair drier','toothbrush',
]


def _helper():
    key = '_onnxvision_helper'
    if key in sys.modules:
        return sys.modules[key]
    here  = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.join(here, '..', '_onnxvision.py')
    spec  = importlib.util.spec_from_file_location(key, fpath)
    mod   = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    for k, v in {
        'image': None, 'detections': None, 'last_op': None,
        '_onnx_detect_sess': None,
    }.items():
        forth._ai.setdefault(k, v)


def _load_session(forth):
    import onnxruntime as ort
    sess = forth._ai.get('_onnx_detect_sess')
    if sess is None:
        h    = _helper()
        path = h.ensure_onnx_model('yolov5n.onnx', task='detect')
        print("Cargando YOLOv5n ONNX...")
        sess = ort.InferenceSession(path, providers=['CPUExecutionProvider'])
        forth._ai['_onnx_detect_sess'] = sess
    return sess


def _detect_hog_haar(img_pil, forth):
    """
    Fallback sin onnxruntime: detecta personas (HOG) y rostros (Haar).
    Solo OpenCV, sin descargas ni modelos externos.
    """
    import cv2
    import numpy as np

    if not getattr(forth, '_imgdetect_hog_warned', False):
        print("img-detect: onnxruntime no disponible — usando HOG+Haar (personas y rostros)")
        print("  Para detectar cualquier objeto: pip install onnxruntime")
        forth._imgdetect_hog_warned = True

    frame = cv2.cvtColor(np.array(img_pil.convert('RGB')), cv2.COLOR_RGB2BGR)
    h_px, w = frame.shape[:2]
    scale = min(1.0, 640 / max(w, h_px))
    small = cv2.resize(frame, (int(w * scale), int(h_px * scale)))

    detections = []

    # HOG — personas
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    boxes, weights = hog.detectMultiScale(
        small, winStride=(8, 8), padding=(8, 8), scale=1.05,
    )
    if len(boxes) > 0:
        for i, (x, y, bw, bh) in enumerate(boxes):
            conf = float(weights[i]) if i < len(weights) else 0.5
            detections.append({
                'label': 'person',
                'conf':  round(min(conf / 2.0, 1.0), 2),
                'box':   [round(x / scale), round(y / scale),
                          round((x + bw) / scale), round((y + bh) / scale)],
            })

    # Haar — rostros
    haar_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    if os.path.exists(haar_path):
        cascade = cv2.CascadeClassifier(haar_path)
        gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30),
        )
        if len(faces) > 0:
            for (x, y, fw, fh) in faces:
                detections.append({
                    'label': 'face',
                    'conf':  0.70,
                    'box':   [round(x / scale), round(y / scale),
                              round((x + fw) / scale), round((y + fh) / scale)],
                })

    from collections import Counter
    counts = Counter(d['label'] for d in detections)
    silent = forth._ai.get('_silent', False)
    if not silent:
        if detections:
            print(f"✓ Detectados: {len(detections)} objetos  (HOG+Haar)")
            print(f"  {'Objeto':<20} {'Cant':>5}")
            print(f"  {'─'*20} {'─'*5}")
            for lbl, cnt in sorted(counts.items(), key=lambda x: -x[1]):
                print(f"  {lbl:<20} {cnt:>5}")
        else:
            print("✓ No se detectaron personas ni rostros  (HOG+Haar)")
    if silent and detections:
        acc = forth._ai.setdefault('_total_counts', {})
        for lbl, cnt in counts.items():
            acc[lbl] = max(acc.get(lbl, 0), cnt)

    forth._ai['detections'] = detections
    forth._ai['last_op'] = {
        'type':    'img-detect',
        'data':    {'counts': dict(counts), 'motor': 'HOG+Haar'},
        'metrics': {'total': len(detections), 'classes': len(counts)},
    }
    forth.stack.append(len(detections))


def execute(forth):
    _ensure_ai(forth)
    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        forth.stack.append(0)
        return

    _onnx_ok = False
    try:
        import onnxruntime  # noqa
        import numpy as np
        _onnx_ok = True
    except ImportError:
        pass

    if not _onnx_ok:
        _detect_hog_haar(img, forth)
        return

    try:
        h    = _helper()
        sess = _load_session(forth)

        # Preprocesar con letterbox 640x640
        canvas, scale, pad_x, pad_y = h.letterbox(img, 640)
        inp = canvas.transpose(2, 0, 1)[np.newaxis]          # [1,3,640,640]

        inp_name = sess.get_inputs()[0].name
        # YOLOv5n salida: [1, 25200, 85]
        # 85 = cx cy w h obj_conf + 80 clases
        # El modelo v7.0 usa float16 — detectar tipo esperado
        expected_dtype = sess.get_inputs()[0].type
        if 'float16' in expected_dtype:
            feed = inp.astype(np.float16)
        else:
            feed = inp.astype(np.float32)
        raw = sess.run(None, {inp_name: feed})[0][0].astype(np.float32)

        conf_thr = 0.25
        obj_conf = raw[:, 4]
        cls_raw  = raw[:, 5:]
        cls_ids  = np.argmax(cls_raw, axis=1)
        cls_conf = cls_raw[np.arange(len(raw)), cls_ids]
        confs    = obj_conf * cls_conf
        mask     = confs > conf_thr
        raw, confs, cls_ids = raw[mask], confs[mask], cls_ids[mask]

        if len(raw) == 0:
            forth._ai['detections'] = []
            if not forth._ai.get('_silent', False):
                print("✓ No se detectaron objetos  (YOLOv5n ONNX)")
            forth.stack.append(0)
            return

        # xywh → xyxy, deshacer letterbox
        cx, cy, bw, bh = raw[:,0], raw[:,1], raw[:,2], raw[:,3]
        x1 = ((cx - bw/2) - pad_x) / scale
        y1 = ((cy - bh/2) - pad_y) / scale
        x2 = ((cx + bw/2) - pad_x) / scale
        y2 = ((cy + bh/2) - pad_y) / scale
        boxes = np.stack([x1, y1, x2, y2], axis=1)

        keep       = h.nms(boxes, confs)
        detections = []
        for i in keep:
            label = (COCO_CLASSES[cls_ids[i]]
                     if cls_ids[i] < len(COCO_CLASSES) else str(cls_ids[i]))
            detections.append({
                'label': label,
                'conf':  round(float(confs[i]), 3),
                'box':   [round(float(v), 1) for v in boxes[i]],
            })

        from collections import Counter
        counts = Counter(d['label'] for d in detections)
        silent = forth._ai.get('_silent', False)
        if not silent:
            print(f"✓ Detectados: {len(detections)} objetos  (YOLOv5n ONNX)")
            if detections:
                print(f"  {'Objeto':<20} {'Cant':>5}  {'Conf. media':>11}")
                print(f"  {'─'*20} {'─'*5}  {'─'*11}")
                for lbl, cnt in sorted(counts.items(), key=lambda x: -x[1]):
                    cs     = [d['conf'] for d in detections if d['label'] == lbl]
                    mean_c = round(sum(cs)/len(cs), 2)
                    print(f"  {lbl:<20} {cnt:>5}  {mean_c:>10.2f}")
        if silent and detections:
            acc = forth._ai.setdefault('_total_counts', {})
            for lbl, cnt in counts.items():
                acc[lbl] = max(acc.get(lbl, 0), cnt)

        forth._ai['detections'] = detections
        forth._ai['last_op'] = {
            'type':    'img-detect',
            'data':    {'counts': dict(counts)},
            'metrics': {'total': len(detections), 'classes': len(counts)},
        }
        forth.stack.append(len(detections))

    except Exception as e:
        print(f"Error img-detect: {e}")
        forth.stack.append(0)
