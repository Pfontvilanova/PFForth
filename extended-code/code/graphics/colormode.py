# FORTH CODE WORD: code/graphics/colormode
# Set color output mode for canvas rendering

WORD_NAME = 'color-mode'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( s -- ) Set color mode: "truecolor" "256" "16" "none" "auto"
# === FIN CÓDIGO FORTH ===

def execute(forth):
    if len(forth.stack) < 1:
        print("Error: color-mode requiere modo (truecolor/256/16/none/auto)")
        return
    mode = str(forth.stack.pop()).strip().lower()
    valid = ('truecolor', '256', '16', 'none', 'auto')
    if mode not in valid:
        print(f"Error: modo no válido. Usa: {', '.join(valid)}")
        return

    import os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    import __braille_canvas as bc
    bc.COLOR_MODE = mode
    print(f"Color mode: {mode}")
