\ ════════════════════════════════════════════════════════
\  Módulo VISION — Análisis de imágenes con pfforth
\  Uso: s" vision" load
\
\  Requisito: pip install onnxruntime pillow opencv-python
\  Los modelos se descargan automáticamente en ~/.pfforth/models/
\
\  ── Imagen ──────────────────────────────────────────────
\    img-load   ( filename -- )      Carga imagen activa
\    img-info   ( -- )               Info completa de la imagen
\    img-size   ( -- w h )           Ancho y alto en pila
\    img-resize ( w h -- )           Redimensiona
\    img-save   ( filename -- )      Guarda en disco
\    img-gray   ( -- )               Convierte a escala de grises
\    img-crop   ( x y w h -- )       Recorta región
\
\  ── Detección de objetos (YOLOv5n ONNX, ~4 MB) ─────────
\    img-detect    ( -- n )           Detecta objetos COCO (80 clases)
\    detect-show   ( -- )             Muestra tabla de detecciones
\    detect-count  ( label -- n )     Cuenta objetos de ese tipo
\    detect-boxes  ( -- list )        Lista de cajas detectadas
\
\  ── Clasificación (MobileNetV2 ONNX, ~14 MB) ────────────
\    img-classify  ( -- label conf )  Top-3 ImageNet (1000 clases)
\    clip-match    ( l1 l2 .. n -- label conf )
\                                     Zero-shot con CLIP ONNX (~150 MB)
\                                     o fallback MobileNetV2 + similitud
\
\  ── Caras (OpenCV Haar, sin descarga) ────────────────────
\    face-detect     ( -- n )         Detecta caras (con detalle)
\    face-count      ( -- n )         Cuenta caras (silencioso)
\    face-neighbors! ( n -- )         Sensibilidad Haar (5=más, 15=menos)
\
\  ── Similitud y anomalías (solo PIL) ─────────────────────
\    img-ref!    ( -- )               Fija imagen como referencia
\    img-sim     ( -- score )         Similitud vs referencia (0-1)
\    img-anomaly ( threshold -- flag) -1=anomalía  0=normal
\
\  ── Embedding ─────────────────────────────────────────────
\    img-embed       ( -- vec )         CLIP ONNX (512d) o histograma (768d)
\
\  ── Visualización ──────────────────────────────────────────
\    img-draw-boxes  ( filename -- )    Guarda imagen con rectángulos marcados
\ ════════════════════════════════════════════════════════

import code/ai/vision

." Módulo VISION cargado — 21 palabras"cr
