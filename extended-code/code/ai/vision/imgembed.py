# FORTH CODE WORD: code/ai/vision/imgembed
# Genera embedding de la imagen activa

WORD_NAME = 'img-embed'
#
# === STACK EFFECT ===
# ( -- vec )  Deja vector de embedding en la pila
#
# Estrategia (en orden de preferencia):
#   1. CLIP ONNX          — 512 dims  (~150 MB al descargar primera vez)
#   2. CLIP (torch)       — 512 dims  (si torch+clip instalados)
#   3. Histograma RGB     — 768 dims  (siempre disponible, sin descarga)
# === FIN ===

import os
import sys
import importlib.util


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
        'image': None, 'embedding': None,
        'clip_model': None, '_clip_onnx': None, 'last_op': None,
    }.items():
        forth._ai.setdefault(k, v)


def _histogram_embedding(img):
    """Embedding siempre disponible: histograma RGB normalizado (768 dims)."""
    hist  = img.convert('RGB').histogram()
    total = sum(hist) or 1
    return [v / total for v in hist]


CLIP_VISUAL_URL = (
    'https://huggingface.co/Xenova/clip-vit-base-patch32'
    '/resolve/main/onnx/vision_model_quantized.onnx'
)


def _clip_onnx_embed(img, forth):
    """Embedding CLIP con ONNX — no requiere PyTorch."""
    import numpy as np
    try:
        import onnxruntime as ort
    except ImportError:
        return None, None

    h      = _helper()
    v_path = h.model_path('clip_visual_q.onnx')

    # Reutilizar sesión ya cargada por clip-match si existe
    cached = forth._ai.get('_clip_onnx')
    v_sess = cached[0] if cached else None

    if v_sess is None:
        if not os.path.exists(v_path):
            print("Descargando CLIP visual ONNX (~87 MB, solo primera vez)...")
            try:
                h.download_file(CLIP_VISUAL_URL, v_path, 'clip_visual_q.onnx')
            except Exception as e:
                print(f"Aviso descarga CLIP: {e}")
                return None, None
        try:
            print("Cargando CLIP visual ONNX...")
            v_sess = ort.InferenceSession(v_path, providers=['CPUExecutionProvider'])
        except Exception as e:
            print(f"Aviso CLIP ONNX: {e}")
            return None, None

    pv  = h.clip_image_preprocess(img)        # [1,3,224,224]
    vec = v_sess.run(None, {'pixel_values': pv})[0][0]  # [512]
    vec = vec / (np.linalg.norm(vec) + 1e-8)
    return vec.tolist(), 'CLIP ONNX'


def _clip_torch_embed(img, forth):
    """Embedding CLIP con torch (original)."""
    try:
        import torch
        import clip
    except ImportError:
        return None, None

    model_data = forth._ai.get('clip_model')
    if model_data is None:
        print("Cargando CLIP (primera vez ~350 MB)...")
        device = 'cpu'
        model, preprocess = clip.load('ViT-B/32', device=device)
        forth._ai['clip_model'] = (model, preprocess, device)
        model_data = forth._ai['clip_model']

    model, preprocess, device = model_data
    import torch
    tensor = preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        vec = model.encode_image(tensor)
        vec = vec / vec.norm(dim=-1, keepdim=True)
    return vec[0].tolist(), 'CLIP (torch)'


def execute(forth):
    _ensure_ai(forth)

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        forth.stack.append(None)
        return

    embedding, method = None, None

    # Intentar CLIP ONNX
    try:
        embedding, method = _clip_onnx_embed(img, forth)
    except Exception as e:
        print(f"Aviso CLIP ONNX embed: {e}")

    # Intentar CLIP torch
    if embedding is None:
        try:
            embedding, method = _clip_torch_embed(img, forth)
        except Exception:
            pass

    # Fallback: histograma
    if embedding is None:
        embedding = _histogram_embedding(img)
        method    = 'histograma RGB'

    dims = len(embedding)
    forth._ai['embedding'] = embedding
    forth._ai['last_op'] = {
        'type':    'img-embed',
        'data':    {'method': method},
        'metrics': {'dims': dims},
    }
    print(f"✓ Embedding ({method}): {dims} dimensiones")
    forth.stack.append(embedding)
