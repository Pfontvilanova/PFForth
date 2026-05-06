# FORTH CODE WORD: code/ai/vision/imgdrawboxes
# Guarda la imagen activa con los rectángulos de detección dibujados

WORD_NAME = 'img-draw-boxes'
#
# === STACK EFFECT ===
# ( filename -- )  Guarda copia de la imagen con cajas y etiquetas
#                  Requiere img-detect o face-detect previo
#
# Ejemplo:
#   s" foto.jpg"  img-load
#   img-detect drop
#   s" foto_marcada.jpg"  img-draw-boxes
#
# También funciona con face-detect:
#   s" foto.jpg"  img-load
#   face-detect drop
#   s" foto_caras.jpg"  img-draw-boxes
# === FIN ===

# Paleta de colores por clase (cicla automáticamente)
_PALETTE = [
    '#FF3333', '#33BB33', '#3399FF', '#FF9900', '#CC33FF',
    '#FF66CC', '#00CCCC', '#FFFF00', '#FF6600', '#99FF33',
]


def _color_for(label, alpha=False):
    idx = hash(label) % len(_PALETTE)
    hex_c = _PALETTE[idx]
    r = int(hex_c[1:3], 16)
    g = int(hex_c[3:5], 16)
    b = int(hex_c[5:7], 16)
    return (r, g, b, 128) if alpha else (r, g, b)


def execute(forth):
    if not forth.stack:
        print("Error: img-draw-boxes requiere nombre de archivo  ( filename -- )")
        return

    filename = str(forth.stack.pop()).strip()
    if not filename:
        print("Error: nombre de archivo vacío")
        return

    if not hasattr(forth, '_ai'):
        forth._ai = {}

    img = forth._ai.get('image')
    if img is None:
        print("Error: no hay imagen activa — usa img-load primero")
        return

    detections = forth._ai.get('detections')
    if not detections:
        print("Error: no hay detecciones — usa img-detect o face-detect primero")
        return

    try:
        from PIL import Image, ImageDraw, ImageFont

        # Trabajar sobre una copia para no alterar la imagen activa
        out = img.convert('RGB').copy()
        draw = ImageDraw.Draw(out, 'RGBA')

        w, h = out.size
        # Grosor del borde proporcional al tamaño de la imagen
        lw = max(2, min(w, h) // 200)
        # Tamaño de fuente proporcional
        fsize = max(12, min(w, h) // 40)

        # Intentar fuente del sistema; si no, la por defecto de PIL
        font = None
        try:
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', fsize)
        except Exception:
            try:
                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', fsize)
            except Exception:
                font = ImageFont.load_default()

        for d in detections:
            label = d.get('label', '?')
            conf  = d.get('conf', 0.0)
            box   = d.get('box', [])

            if len(box) != 4:
                continue

            x1, y1, x2, y2 = [int(v) for v in box]
            color      = _color_for(label)
            color_fill = _color_for(label, alpha=True)

            # Rectángulo con relleno semitransparente
            draw.rectangle([x1, y1, x2, y2], outline=color, width=lw, fill=color_fill)

            # Etiqueta: fondo sólido + texto
            text = f"{label} {conf:.2f}"
            try:
                bbox = font.getbbox(text)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except Exception:
                tw, th = fsize * len(text) // 2, fsize

            pad   = 3
            ty    = max(0, y1 - th - pad * 2)
            draw.rectangle(
                [x1, ty, x1 + tw + pad * 2, ty + th + pad * 2],
                fill=color,
            )
            draw.text(
                (x1 + pad, ty + pad),
                text,
                fill='white',
                font=font,
            )

        out.save(filename)
        print(f"✓ Guardado: {filename}  ({len(detections)} objetos marcados)")

    except Exception as e:
        print(f"Error img-draw-boxes: {e}")
