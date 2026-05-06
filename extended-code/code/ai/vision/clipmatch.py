# FORTH CODE WORD: code/ai/vision/clipmatch
# Clasifica imagen activa comparando con etiquetas de texto

WORD_NAME = 'clip-match'
#
# === STACK EFFECT ===
# ( label1 label2 ... n -- label confidence )
#   Elige la etiqueta que mejor describe la imagen activa.
#   n = número de etiquetas.
#
# Estrategia (en orden de preferencia):
#   1. CLIP ONNX   — si está disponible (~150 MB al descargar)
#   2. CLIP (torch) — si torch+clip instalados
#   3. YOLOv8n-cls ONNX + similitud de texto (fallback universal)
#
# Ejemplo:
#   s" un perro" s" un gato" s" un pájaro" 3 clip-match
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
        'image': None, 'last_op': None,
        'clip_model': None,                  # cache torch CLIP
        '_clip_onnx': None,                  # cache ONNX CLIP sessions
        '_onnx_cls_sess': None,              # reutiliza YOLOv8n-cls
        '_imagenet_labels': None,
    }.items():
        forth._ai.setdefault(k, v)


# ─────────────────────────────────────────────
#  Opción 1: CLIP ONNX (onnxruntime sin torch)
# ─────────────────────────────────────────────
CLIP_VISUAL_URL = (
    'https://huggingface.co/Xenova/clip-vit-base-patch32'
    '/resolve/main/onnx/vision_model_quantized.onnx'
)
CLIP_TEXT_URL = (
    'https://huggingface.co/Xenova/clip-vit-base-patch32'
    '/resolve/main/onnx/text_model_quantized.onnx'
)


def _load_clip_onnx(forth):
    """Devuelve (visual_sess, text_sess) o None si no disponible."""
    cached = forth._ai.get('_clip_onnx')
    if cached is not None:
        return cached

    try:
        import onnxruntime as ort
    except ImportError:
        return None

    h = _helper()
    v_path = h.model_path('clip_visual_q.onnx')
    t_path = h.model_path('clip_text_q.onnx')

    try:
        if not os.path.exists(v_path):
            print("Descargando CLIP visual ONNX (~87 MB, solo primera vez)...")
            h.download_file(CLIP_VISUAL_URL, v_path, 'clip_visual_q.onnx')
        if not os.path.exists(t_path):
            print("Descargando CLIP texto ONNX (~64 MB, solo primera vez)...")
            h.download_file(CLIP_TEXT_URL, t_path, 'clip_text_q.onnx')
    except Exception as e:
        print(f"Aviso: no se pudo descargar CLIP ONNX ({e}) — usando fallback")
        for p in [v_path, t_path]:
            if os.path.exists(p) and os.path.getsize(p) < 1000:
                os.remove(p)
        return None

    try:
        print("Cargando modelos CLIP ONNX...")
        v_sess = ort.InferenceSession(v_path, providers=['CPUExecutionProvider'])
        t_sess = ort.InferenceSession(t_path, providers=['CPUExecutionProvider'])
        forth._ai['_clip_onnx'] = (v_sess, t_sess)
        return (v_sess, t_sess)
    except Exception as e:
        print(f"Aviso cargando CLIP ONNX: {e}")
        return None


def _clip_tokenize(texts, max_len=77):
    """
    Tokeniza textos para CLIP.
    Intenta transformers.CLIPTokenizer primero (no requiere torch),
    luego tokenización simple de respaldo.
    """
    try:
        from transformers import CLIPTokenizer
        tok = CLIPTokenizer.from_pretrained('openai/clip-vit-base-patch32')
        enc = tok(texts, padding='max_length', truncation=True,
                  max_length=max_len, return_tensors='np')
        return enc['input_ids'].astype('int64'), enc['attention_mask'].astype('int64')
    except Exception:
        pass

    # Fallback: tokenización básica por palabras (muy simplificada)
    import numpy as np
    ids  = np.zeros((len(texts), max_len), dtype='int64')
    mask = np.zeros((len(texts), max_len), dtype='int64')
    for i, t in enumerate(texts):
        words = t.lower().split()[:max_len - 2]
        ids[i, 0] = 49406                  # <|startoftext|>
        for j, w in enumerate(words, 1):
            ids[i, j] = hash(w) % 49406 + 1
        end = len(words) + 1
        ids[i, end] = 49407               # <|endoftext|>
        mask[i, :end + 1] = 1
    return ids, mask


def _clip_onnx_match(img, labels, forth):
    """Clasificación zero-shot con CLIP ONNX (Xenova)."""
    import numpy as np

    sessions = _load_clip_onnx(forth)
    if sessions is None:
        return None

    v_sess, t_sess = sessions
    h = _helper()

    # Imagen → image_embeds [1, 512]
    pv       = h.clip_image_preprocess(img)         # [1,3,224,224]
    img_feat = v_sess.run(None, {'pixel_values': pv})[0][0]   # [512]
    img_feat = img_feat / (np.linalg.norm(img_feat) + 1e-8)

    # Texto: tokenizar y pasar al encoder de texto
    input_ids, _ = _clip_tokenize(labels)
    scores = []
    for i in range(len(labels)):
        ids_i    = input_ids[i:i+1]                  # [1, seq_len]
        txt_feat = t_sess.run(None, {'input_ids': ids_i})[0][0]  # [512]
        txt_feat = txt_feat / (np.linalg.norm(txt_feat) + 1e-8)
        scores.append(float(np.dot(img_feat, txt_feat)))

    # softmax escalada (×100 como CLIP original)
    s = np.array(scores) * 100
    e = np.exp(s - s.max())
    probs = (e / e.sum()).tolist()
    return probs


# ─────────────────────────────────────────────
#  Opción 2: CLIP con torch (original)
# ─────────────────────────────────────────────
def _clip_torch_match(img, labels, forth):
    try:
        import torch
        import clip
    except ImportError:
        return None

    model_data = forth._ai.get('clip_model')
    if model_data is None:
        print("Cargando CLIP (primera vez ~350 MB)...")
        device = 'cpu'
        model, preprocess = clip.load('ViT-B/32', device=device)
        forth._ai['clip_model'] = (model, preprocess, device)
        model_data = forth._ai['clip_model']

    model, preprocess, device = model_data
    import torch
    image_t = preprocess(img).unsqueeze(0).to(device)
    text_t  = clip.tokenize(labels).to(device)
    with torch.no_grad():
        imf  = model.encode_image(image_t)
        txf  = model.encode_text(text_t)
        imf  = imf / imf.norm(dim=-1, keepdim=True)
        txf  = txf / txf.norm(dim=-1, keepdim=True)
        probs = (100.0 * imf @ txf.T).softmax(dim=-1)[0].tolist()
    return probs


# ─────────────────────────────────────────────
#  Opción 3: YOLOv8n-cls + similitud de texto
# ─────────────────────────────────────────────
def _word_sim(a, b):
    """Similitud palabra-a-palabra entre dos frases (Jaccard)."""
    wa = set(a.lower().replace('-', ' ').replace('_', ' ').split())
    wb = set(b.lower().replace('-', ' ').replace('_', ' ').split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _yolo_cls_match(img, labels, forth):
    """Proxy: clasifica con YOLOv8n-cls y mapea resultados a etiquetas del usuario."""
    import numpy as np

    h = _helper()

    # Cargar / reutilizar sesión MobileNetV2
    sess = forth._ai.get('_onnx_cls_sess')
    if sess is None:
        try:
            import onnxruntime as ort
            path = h.ensure_onnx_model('mobilenetv2.onnx', task='classify')
            sess = ort.InferenceSession(path, providers=['CPUExecutionProvider'])
            forth._ai['_onnx_cls_sess'] = sess
        except Exception as e:
            print(f"Aviso fallback cls: {e}")
            return None

    # Cargar etiquetas ImageNet
    inet_labels = forth._ai.get('_imagenet_labels')
    if not inet_labels:
        lbl_path = h.model_path('imagenet_labels.json')
        if not os.path.exists(lbl_path):
            IMAGENET_URL = (
                'https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels'
                '/master/imagenet-simple-labels.json'
            )
            h.download_file(IMAGENET_URL, lbl_path, 'imagenet_labels.json')
        import json
        with open(lbl_path) as f:
            inet_labels = json.load(f)
        forth._ai['_imagenet_labels'] = inet_labels

    # Normalización ImageNet (igual que imgclassify.py)
    MEAN = [0.485, 0.456, 0.406]
    STD  = [0.229, 0.224, 0.225]
    rgb    = img.convert('RGB').resize((224, 224))
    arr    = np.array(rgb, dtype=np.float32) / 255.0
    arr    = (arr - MEAN) / STD
    tensor = arr.transpose(2, 0, 1)[np.newaxis].astype(np.float32)
    logits = sess.run(None, {sess.get_inputs()[0].name: tensor})[0][0]
    e = np.exp(logits - logits.max()); probs_cls = e / e.sum()
    top20_idx = probs_cls.argsort()[::-1][:20]

    # Para cada etiqueta de usuario, calcular similitud con top-20 ImageNet
    user_scores = []
    for user_lbl in labels:
        score = 0.0
        for idx in top20_idx:
            inet_lbl = inet_labels[idx] if idx < len(inet_labels) else ''
            sim = _word_sim(user_lbl, inet_lbl)
            score += sim * float(probs_cls[idx])
        user_scores.append(score)

    total = sum(user_scores) or 1.0
    probs = [s / total for s in user_scores]
    return probs


# ─────────────────────────────────────────────
#  Opción 4: histograma RGB + palabras clave (sin onnxruntime ni torch)
# ─────────────────────────────────────────────
def _histogram_match(img, labels):
    """
    Fallback universal: compara colores dominantes de la imagen
    con palabras clave de color en las etiquetas (ES/EN).
    Siempre disponible, solo usa PIL/numpy.
    """
    import numpy as np

    arr = np.array(img.convert('RGB'), dtype=np.float32) / 255.0
    mean_r = float(arr[:, :, 0].mean())
    mean_g = float(arr[:, :, 1].mean())
    mean_b = float(arr[:, :, 2].mean())
    brightness = (mean_r + mean_g + mean_b) / 3.0
    sat = max(mean_r, mean_g, mean_b) - min(mean_r, mean_g, mean_b)

    # Concepto → valor 0..1 derivado de la imagen
    COLOR_MAP = {
        # rojos / cálidos
        'rojo': mean_r, 'red': mean_r, 'warm': mean_r, 'calido': mean_r,
        'fuego': mean_r, 'fire': mean_r, 'sangre': mean_r,
        # verdes / naturaleza
        'verde': mean_g, 'green': mean_g, 'grass': mean_g, 'hierba': mean_g,
        'natural': mean_g, 'naturaleza': mean_g, 'planta': mean_g, 'plant': mean_g,
        'bosque': mean_g, 'forest': mean_g,
        # azules / agua / cielo
        'azul': mean_b, 'blue': mean_b, 'sky': mean_b, 'cielo': mean_b,
        'agua': mean_b, 'water': mean_b, 'mar': mean_b, 'ocean': mean_b,
        'rio': mean_b, 'lake': mean_b, 'lago': mean_b, 'cool': mean_b,
        # brillo
        'claro': brightness, 'bright': brightness, 'light': brightness,
        'blanco': brightness, 'white': brightness, 'dia': brightness, 'day': brightness,
        # oscuro
        'oscuro': 1 - brightness, 'dark': 1 - brightness,
        'noche': 1 - brightness, 'night': 1 - brightness,
        'negro': 1 - brightness, 'black': 1 - brightness,
        # saturación / colorido
        'colorido': sat, 'colorful': sat, 'vivid': sat, 'vivo': sat,
        # neutros / grises
        'gris': 1 - sat, 'gray': 1 - sat, 'grey': 1 - sat,
        'neutro': 1 - sat, 'neutral': 1 - sat,
    }

    def label_score(label):
        words = label.lower().replace('-', ' ').replace('_', ' ').split()
        best = 0.0
        matched = False
        for w in words:
            if w in COLOR_MAP:
                best = max(best, COLOR_MAP[w])
                matched = True
        return best if matched else 0.30  # base si no hay palabras reconocidas

    scores = [label_score(l) for l in labels]
    total  = sum(scores) or 1.0
    probs  = [round(s / total, 4) for s in scores]

    if not getattr(_histogram_match, '_warned', False):
        print("clip-match: usando histograma RGB + palabras clave (sin onnxruntime)")
        print("  Para zero-shot real instala: pip install onnxruntime")
        _histogram_match._warned = True

    return probs


# ─────────────────────────────────────────────
#  execute
# ─────────────────────────────────────────────
def execute(forth):
    _ensure_ai(forth)

    if not forth.stack:
        print("Error: clip-match requiere ( label1 ... n ) en la pila")
        forth.stack.extend(['?', 0.0])
        return

    n = int(forth.stack.pop())
    if n < 1 or len(forth.stack) < n:
        print(f"Error: se esperaban {n} etiquetas en la pila")
        forth.stack.extend(['?', 0.0])
        return

    labels = []
    for _ in range(n):
        labels.insert(0, str(forth.stack.pop()))

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        forth.stack.extend(['?', 0.0])
        return

    probs  = None
    method = ''

    # Intentar en orden de calidad
    try:
        probs = _clip_onnx_match(img, labels, forth)
        if probs is not None:
            method = 'CLIP ONNX'
    except Exception as e:
        print(f"Aviso CLIP ONNX: {e}")

    if probs is None:
        try:
            probs = _clip_torch_match(img, labels, forth)
            if probs is not None:
                method = 'CLIP (torch)'
        except Exception:
            pass

    if probs is None:
        try:
            probs = _yolo_cls_match(img, labels, forth)
            if probs is not None:
                method = 'YOLOv8n-cls + similitud'
        except Exception as e:
            print(f"Error clip-match (fallback): {e}")

    if probs is None:
        probs = _histogram_match(img, labels)
        if probs is not None:
            method = 'histograma RGB + palabras'

    if probs is None:
        print("Error: ningún motor disponible para clip-match")
        forth.stack.extend(['?', 0.0])
        return

    ranked     = sorted(zip(labels, probs), key=lambda x: -x[1])
    best_label = ranked[0][0]
    best_conf  = round(ranked[0][1], 4)

    print(f"✓ Mejor coincidencia: \"{best_label}\"  ({best_conf:.3f})  [{method}]")
    if len(ranked) > 1:
        print(f"  {'Etiqueta':<30} {'Prob':>8}")
        print(f"  {'─'*30} {'─'*8}")
        for lbl, prob in ranked:
            marker = " ◄" if lbl == best_label else ""
            print(f"  {lbl:<30} {prob:>8.4f}{marker}")

    forth._ai['last_op'] = {
        'type':    'clip-match',
        'data':    {'labels': labels, 'method': method},
        'metrics': {'best_label': best_label, 'best_conf': best_conf,
                    'ranking': [(l, round(p, 4)) for l, p in ranked]},
    }
    forth.stack.append(best_label)
    forth.stack.append(best_conf)
