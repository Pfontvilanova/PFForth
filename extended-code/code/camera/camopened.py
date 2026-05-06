# FORTH CODE WORD: code/camera/camopened
# Comprueba si hay una camara abierta actualmente

WORD_NAME = 'cam-open?'
# === STACK EFFECT ===
# ( -- flag )  -1 si la camara esta abierta, 0 si no
# === FIN ===

import os
import sys


def execute(forth):
    cam = getattr(forth, '_cam', {})
    is_open = cam.get('cap') is not None
    forth.stack.append(-1 if is_open else 0)
