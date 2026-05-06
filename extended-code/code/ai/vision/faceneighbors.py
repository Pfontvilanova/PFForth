# FORTH CODE WORD: code/ai/vision/faceneighbors
# Configura la sensibilidad del detector de caras

WORD_NAME = 'face-neighbors!'

#
# === STACK EFFECT ===
# ( n -- )  Ajusta minNeighbors del detector Haar. Rango típico: 5-15
#           Más alto → menos falsos positivos, puede perder caras pequeñas
#           Más bajo → detecta más caras, pero más falsos positivos
#           Por defecto: 10
# Uso: 8 face-neighbors!    ( más sensible )
#      12 face-neighbors!   ( más estricto )
# === FIN ===

def execute(forth):
    if not forth.stack:
        print("Error: face-neighbors! requiere un número en la pila")
        print("Uso: 8 face-neighbors!   ( rango típico: 5-15 )")
        return

    n = int(forth.stack.pop())
    if n < 1:
        print("Error: face-neighbors! debe ser >= 1")
        return

    if not hasattr(forth, '_ai'):
        forth._ai = {}
    forth._ai['face_min_neighbors'] = n
    print(f"face-detect: minNeighbors={n}  (más alto=menos falsos positivos)")
