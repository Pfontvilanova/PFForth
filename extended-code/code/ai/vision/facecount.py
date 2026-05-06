# FORTH CODE WORD: code/ai/vision/facecount
# Cuenta caras en la imagen activa (versión silenciosa de face-detect)

WORD_NAME = 'face-count'
#
# === STACK EFFECT ===
# ( -- n )  Cuenta caras en la imagen activa (sin mostrar detalles)
#           Equivalent a face-detect pero solo imprime el total
# === FIN ===


def _ensure_ai(forth):
    if not hasattr(forth, '_ai'):
        forth._ai = {}
    for k, v in {
        'image': None, 'detections': None,
        'yolo_detect_model': None, 'last_op': None,
    }.items():
        forth._ai.setdefault(k, v)


def _detect_faces(img, ai_state):
    try:
        import cv2
        import numpy as np
        rgb      = img.convert('RGB')
        arr      = np.array(rgb)
        gray     = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        cascade  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces    = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
        return [{'label': 'face', 'conf': 0.9,
                 'box': [float(x), float(y), float(x+w), float(y+h)]}
                for (x, y, w, h) in faces]
    except ImportError:
        pass

    try:
        from ultralytics import YOLO
        model = ai_state.get('yolo_detect_model')
        if model is None:
            model = YOLO('yolov8n.pt')
            ai_state['yolo_detect_model'] = model
        results = model(img, verbose=False)
        return [{'label': 'face/person',
                 'conf': round(float(b.conf[0]), 3),
                 'box': [round(v, 1) for v in b.xyxy[0].tolist()]}
                for r in results for b in r.boxes
                if model.names[int(b.cls[0])] == 'person']
    except ImportError:
        return []


def execute(forth):
    _ensure_ai(forth)

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        forth.stack.append(0)
        return

    try:
        detections = _detect_faces(img, forth._ai)
        forth._ai['detections'] = detections
        forth._ai['last_op'] = {
            'type': 'face-count',
            'data': {},
            'metrics': {'count': len(detections)},
        }
        print(f"✓ Caras: {len(detections)}")
        forth.stack.append(len(detections))
    except Exception as e:
        print(f"Error face-count: {e}")
        forth.stack.append(0)
