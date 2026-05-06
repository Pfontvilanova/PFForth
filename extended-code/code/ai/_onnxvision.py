"""
Utilidades compartidas para las palabras de visión basadas en ONNX.
No es una palabra Forth — se importa internamente desde imgdetect.py,
imgclassify.py, clipmatch.py, imgembed.py.
"""
import os
import sys
import importlib.util
import urllib.request

MODELS_DIR = os.path.expanduser('~/.pfforth/models')


def models_dir():
    os.makedirs(MODELS_DIR, exist_ok=True)
    return MODELS_DIR


def model_path(filename):
    return os.path.join(models_dir(), filename)


def download_file(url, dest, desc=None):
    """Descarga url → dest mostrando progreso."""
    label = desc or os.path.basename(dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    def _progress(count, block, total):
        if total > 0:
            pct = min(count * block * 100 // total, 100)
            print(f"\r  {label}: {pct}%", end='', flush=True)

    print(f"Descargando {label}...")
    urllib.request.urlretrieve(url, dest, reporthook=_progress)
    print()


def ensure_onnx_model(model_name, task='detect'):
    """
    Devuelve la ruta al archivo .onnx listo para usar.
    Orden de intento:
      1. Archivo ya cacheado en ~/.pfforth/models/
      2. Exportar desde ultralytics (si instalado)
      3. Descargar desde URLs públicas
    """
    path = model_path(model_name)
    if os.path.exists(path):
        return path

    # --- intento 1: exportar con ultralytics ---
    try:
        from ultralytics import YOLO
        import shutil
        pt_name = model_name.replace('.onnx', '.pt')
        print(f"Exportando {pt_name} → ONNX (primera vez, requiere ~100 MB)...")
        mdl = YOLO(pt_name)
        exported = mdl.export(format='onnx', dynamic=False, simplify=True)
        shutil.move(str(exported), path)
        print(f"✓ Modelo guardado: {path}")
        return path
    except ImportError:
        pass
    except Exception as e:
        print(f"Aviso export: {e}")

    # --- intento 2: descargar ONNX pre-exportado ---
    DOWNLOAD_URLS = {
        # YOLOv5n (GitHub releases — archivo ONNX verificado, ~4 MB)
        'yolov5n.onnx': [
            'https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5n.onnx',
        ],
        # MobileNetV2 — ONNX Model Zoo (~14 MB, clasificación ImageNet)
        'mobilenetv2.onnx': [
            'https://github.com/onnx/models/raw/main/validated/vision/classification'
            '/mobilenet/model/mobilenetv2-12.onnx',
        ],
    }
    urls = DOWNLOAD_URLS.get(model_name, [])
    for url in urls:
        try:
            download_file(url, path, model_name)
            if os.path.getsize(path) > 100_000:
                print(f"✓ Descargado: {path}")
                return path
            os.remove(path)
        except Exception:
            if os.path.exists(path):
                os.remove(path)

    raise RuntimeError(
        f"No se pudo obtener '{model_name}'.\n"
        f"Copia manualmente el archivo .onnx a: {MODELS_DIR}/"
    )


def letterbox(img, size=640):
    """Redimensiona con padding (para detección YOLO)."""
    import numpy as np
    w, h = img.size
    scale = size / max(w, h)
    nw, nh = int(w * scale), int(h * scale)
    resized = img.resize((nw, nh))
    canvas = np.zeros((size, size, 3), dtype=np.float32)
    pad_y = (size - nh) // 2
    pad_x = (size - nw) // 2
    canvas[pad_y:pad_y + nh, pad_x:pad_x + nw] = (
        np.array(resized.convert('RGB'), dtype=np.float32) / 255.0
    )
    return canvas, scale, pad_x, pad_y


def nms(boxes, scores, iou_thr=0.45):
    """Non-Maximum Suppression básico."""
    import numpy as np
    if len(boxes) == 0:
        return []
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas  = (x2 - x1) * (y2 - y1)
    order  = scores.argsort()[::-1]
    keep   = []
    while order.size:
        i = order[0]
        keep.append(i)
        order = order[1:]
        ix1 = np.maximum(x1[i], x1[order])
        iy1 = np.maximum(y1[i], y1[order])
        ix2 = np.minimum(x2[i], x2[order])
        iy2 = np.minimum(y2[i], y2[order])
        inter = np.maximum(0, ix2 - ix1) * np.maximum(0, iy2 - iy1)
        iou   = inter / (areas[i] + areas[order] - inter + 1e-7)
        order = order[iou <= iou_thr]
    return keep


def clip_image_preprocess(img):
    """Preprocesa imagen para CLIP ONNX."""
    import numpy as np
    MEAN = [0.48145466, 0.4578275,  0.40821073]
    STD  = [0.26862954, 0.26130258, 0.27577711]
    rgb  = img.convert('RGB').resize((224, 224))
    arr  = np.array(rgb, dtype=np.float32) / 255.0
    arr  = (arr - MEAN) / STD
    return arr.transpose(2, 0, 1)[np.newaxis].astype(np.float32)


def load_helper(word_file):
    """Carga este módulo desde un archivo hermano — uso: _h = load_helper(__file__)"""
    key = '_onnxvision_helper'
    if key in sys.modules:
        return sys.modules[key]
    here  = os.path.dirname(os.path.abspath(word_file))
    fpath = os.path.join(here, '..', '_onnxvision.py')
    spec  = importlib.util.spec_from_file_location(key, fpath)
    mod   = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod
