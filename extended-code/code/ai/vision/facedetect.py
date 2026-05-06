# FORTH CODE WORD: code/ai/vision/facedetect
# Detecta caras en la imagen activa

WORD_NAME = 'face-detect'
#
# === STACK EFFECT ===
# ( -- n )  Detecta caras en imagen activa, deja cantidad en pila
#           Resultados en forth._ai['detections']
#           Sensibilidad configurable con face-neighbors! (por defecto 10)
#           Usa OpenCV haarcascade (si disponible) o YOLOv8n-face
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    for k, v in {
        'image': None, 'detections': None,
        'yolo_detect_model': None, 'last_op': None,
        'face_min_neighbors': 10,
    }.items():
        forth._ai.setdefault(k, v)


def _detect_with_opencv(img, min_neighbors=10):
    """Usa haarcascade de OpenCV."""
    import cv2
    import numpy as np

    rgb  = img.convert('RGB')
    arr  = np.array(rgb)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    cascade      = cv2.CascadeClassifier(cascade_path)
    faces        = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=min_neighbors,
        minSize=(50, 50),
    )

    detections = []
    for (x, y, w, h) in faces:
        detections.append({
            'label': 'face',
            'conf':  0.9,
            'box':   [float(x), float(y), float(x + w), float(y + h)],
        })
    return detections, 'OpenCV haarcascade'


def _detect_with_yolo(img, model_cache):
    """Usa YOLOv8n-face si existe, o YOLOv8n filtrando 'person' como proxy."""
    from ultralytics import YOLO

    model = model_cache.get('yolo_detect_model')
    if model is None:
        print("Cargando modelo YOLOv8n (primera vez ~6 MB)...")
        model = YOLO('yolov8n.pt')
        model_cache['yolo_detect_model'] = model

    results = model(img, verbose=False)
    detections = []
    for r in results:
        for box in r.boxes:
            label = model.names[int(box.cls[0])]
            if label == 'person':
                conf   = round(float(box.conf[0]), 3)
                coords = [round(v, 1) for v in box.xyxy[0].tolist()]
                detections.append({'label': 'face/person', 'conf': conf, 'box': coords})
    return detections, 'YOLO (proxy persona)'


def execute(forth):
    _ensure_ai(forth)

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        forth.stack.append(0)
        return

    min_neighbors = forth._ai.get('face_min_neighbors', 10)

    try:
        detections, method = _detect_with_opencv(img, min_neighbors)
        print(f"✓ Caras detectadas: {len(detections)}  (método: {method}, minNeighbors={min_neighbors})")
    except ImportError:
        try:
            detections, method = _detect_with_yolo(img, forth._ai)
            print(f"✓ Personas detectadas: {len(detections)}  (método: {method})")
            if detections:
                print(f"  Nota: para caras exactas instala opencv-python")
        except ImportError:
            print("Error: instala opencv-python o ultralytics para detectar caras")
            forth.stack.append(0)
            return
    except Exception as e:
        print(f"Error face-detect: {e}")
        forth.stack.append(0)
        return

    forth._ai['detections'] = detections
    forth._ai['last_op'] = {
        'type':    'face-detect',
        'data':    {'method': method},
        'metrics': {'count': len(detections)},
    }

    for i, d in enumerate(detections, 1):
        b = d['box']
        print(f"  {i}. conf={d['conf']:.2f}  caja=({b[0]:.0f},{b[1]:.0f},{b[2]:.0f},{b[3]:.0f})")

    forth.stack.append(len(detections))
