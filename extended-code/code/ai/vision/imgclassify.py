# FORTH CODE WORD: code/ai/vision/imgclassify
# Clasifica la imagen activa con MobileNetV2 ONNX (sin PyTorch)

WORD_NAME = 'img-classify'
#
# === STACK EFFECT ===
# ( -- label confidence )  Clasifica imagen activa (top-3 en pantalla)
#                          Motor: MobileNetV2 ONNX (~14 MB, primera vez)
#                          Si no disponible, intenta YOLOv8n-cls via ultralytics
# === FIN ===

import os
import sys
import importlib.util

IMAGENET_LABELS_URL = (
    'https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels'
    '/master/imagenet-simple-labels.json'
)
IMAGENET_LABELS_FILE = 'imagenet_labels.json'

# Normalización ImageNet
IMGNET_MEAN = [0.485, 0.456, 0.406]
IMGNET_STD  = [0.229, 0.224, 0.225]


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
        'image': None, 'last_op': None,
        '_onnx_cls_sess': None,
        '_imagenet_labels': None,
        'yolo_classify_model': None,
    }.items():
        forth._ai.setdefault(k, v)


def _load_labels(forth):
    labels = forth._ai.get('_imagenet_labels')
    if labels:
        return labels
    h    = _helper()
    path = h.model_path(IMAGENET_LABELS_FILE)
    if not os.path.exists(path):
        print("Descargando etiquetas ImageNet (~30 KB)...")
        h.download_file(IMAGENET_LABELS_URL, path, 'imagenet_labels.json')
    import json
    with open(path, 'r') as f:
        labels = json.load(f)
    forth._ai['_imagenet_labels'] = labels
    return labels


def _load_session(forth):
    import onnxruntime as ort
    sess = forth._ai.get('_onnx_cls_sess')
    if sess is None:
        h    = _helper()
        path = h.ensure_onnx_model('mobilenetv2.onnx', task='classify')
        print("Cargando MobileNetV2 ONNX...")
        sess = ort.InferenceSession(path, providers=['CPUExecutionProvider'])
        forth._ai['_onnx_cls_sess'] = sess
    return sess


def _preprocess_mobilenet(img):
    """224x224, normalización ImageNet."""
    import numpy as np
    rgb = img.convert('RGB').resize((224, 224))
    arr = np.array(rgb, dtype=np.float32) / 255.0
    arr = (arr - IMGNET_MEAN) / IMGNET_STD
    return arr.transpose(2, 0, 1)[np.newaxis].astype(np.float32)  # [1,3,224,224]


def _color_classify(img):
    """
    Fallback sin onnxruntime: clasifica por colores dominantes y brillo.
    Solo usa PIL (siempre disponible). No descarga nada.
    """
    import numpy as np

    arr = np.array(img.convert('RGB'), dtype=np.float32) / 255.0
    mean_r = float(arr[:, :, 0].mean())
    mean_g = float(arr[:, :, 1].mean())
    mean_b = float(arr[:, :, 2].mean())
    brightness  = (mean_r + mean_g + mean_b) / 3.0
    saturation  = max(mean_r, mean_g, mean_b) - min(mean_r, mean_g, mean_b)

    if brightness > 0.75:
        if saturation < 0.08:
            label, conf = 'white / very bright', 0.70
        elif mean_b > mean_r and mean_b > mean_g:
            label, conf = 'blue / sky', round(0.5 + mean_b * 0.4, 2)
        elif mean_g >= mean_r:
            label, conf = 'green / nature', round(0.5 + mean_g * 0.4, 2)
        else:
            label, conf = 'warm / bright', round(0.5 + mean_r * 0.3, 2)
    elif brightness < 0.25:
        label, conf = 'dark / night', round(0.6 + (0.25 - brightness) * 1.2, 2)
    else:
        if saturation < 0.06:
            label, conf = 'grayscale / neutral', 0.65
        elif mean_r > mean_g and mean_r > mean_b:
            label, conf = 'red / warm tones', round(0.5 + saturation * 0.5, 2)
        elif mean_g > mean_r and mean_g > mean_b:
            label, conf = 'green / nature', round(0.5 + saturation * 0.5, 2)
        elif mean_b > mean_r:
            label, conf = 'blue / cool tones', round(0.5 + saturation * 0.5, 2)
        else:
            label, conf = 'mixed / colorful', round(0.4 + saturation * 0.4, 2)

    conf = round(min(conf, 0.95), 2)
    print(f"✓ Clasificación por color (sin onnxruntime):")
    print(f"  Brillo={brightness:.2f}  Saturación={saturation:.2f}  R={mean_r:.2f} G={mean_g:.2f} B={mean_b:.2f}")
    print(f"  Categoría: {label}  (conf {conf})")
    print(f"  Para clasificación ImageNet instala: pip install onnxruntime")
    return label, conf


def execute(forth):
    _ensure_ai(forth)
    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        forth.stack.append('?')
        forth.stack.append(0.0)
        return

    _onnx_ok = False
    try:
        import onnxruntime  # noqa
        import numpy as np
        _onnx_ok = True
    except ImportError:
        pass

    if not _onnx_ok:
        label, conf = _color_classify(img)
        forth.stack.append(label)
        forth.stack.append(conf)
        return

    try:
        h      = _helper()
        sess   = _load_session(forth)
        labels = _load_labels(forth)

        tensor   = _preprocess_mobilenet(img)
        inp_name = sess.get_inputs()[0].name
        logits   = sess.run(None, {inp_name: tensor})[0][0]  # [1000]

        # softmax
        e     = np.exp(logits - logits.max())
        probs = e / e.sum()

        top5_idx  = probs.argsort()[::-1][:5]
        top5_conf = probs[top5_idx].tolist()
        top5_lbl  = [labels[i] if i < len(labels) else str(i) for i in top5_idx]

        best_label = top5_lbl[0]
        best_conf  = round(top5_conf[0], 4)

        print(f"✓ Clasificación top-3  (MobileNetV2 ONNX):")
        print(f"  {'Categoría':<30} {'Confianza':>10}")
        print(f"  {'─'*30} {'─'*10}")
        for lbl, conf in zip(top5_lbl[:3], top5_conf[:3]):
            print(f"  {lbl:<30} {conf:>9.4f}")

        forth._ai['last_op'] = {
            'type':    'img-classify',
            'data':    {'top': list(zip(top5_lbl, [round(c,4) for c in top5_conf]))},
            'metrics': {'best_label': best_label, 'best_conf': best_conf},
        }
        forth.stack.append(best_label)
        forth.stack.append(best_conf)

    except Exception as e:
        print(f"Error img-classify: {e}")
        # Fallback a ultralytics si disponible
        try:
            from ultralytics import YOLO
            model = forth._ai.get('yolo_classify_model')
            if model is None:
                print("Intentando con YOLOv8n-cls (ultralytics)...")
                model = YOLO('yolov8n-cls.pt')
                forth._ai['yolo_classify_model'] = model
            results = model(img, verbose=False)
            r = results[0]
            top5_idx  = r.probs.top5
            top5_conf = r.probs.top5conf.tolist()
            top5_lbl  = [model.names[i] for i in top5_idx]
            best_label, best_conf = top5_lbl[0], round(top5_conf[0], 3)
            print(f"✓ Clasificación top-3  (YOLOv8n-cls ultralytics):")
            for lbl, conf in zip(top5_lbl[:3], top5_conf[:3]):
                print(f"  {lbl:<30} {conf:>9.3f}")
            forth.stack.append(best_label)
            forth.stack.append(best_conf)
        except Exception as e2:
            print(f"Error fallback img-classify: {e2}")
            forth.stack.append('?')
            forth.stack.append(0.0)
