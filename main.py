#!/usr/bin/env python3
"""
PFForth - Python Forth Interpreter/Compiler

Modos de uso:
1. REPL interactivo de Forth: python main.py repl
2. Modo DSL de Python: python main.py (o python -i main.py)
3. Ejecutar archivo Forth: python main.py archivo.fth

Compatible con:
- Cualquier Python 3.x estandar
- Jupyter Notebook (iPad, etc.)
- Sin dependencias externas
"""

import sys

try:
    from pfforth import InteractiveForth
except ImportError:
    from pfforth.repl import InteractiveForth

def create_forth():
    """Create a new Forth interpreter instance"""
    return InteractiveForth()

def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == 'repl':
            print("Iniciando Forth REPL...")
            print("Escribe 'help' para ver comandos, 'bye' para salir")
            print()
            f = InteractiveForth()
            f.repl()
        elif arg.endswith('.fth') or arg.endswith('.forth'):
            f = create_forth()
            with open(arg, 'r') as file:
                code = file.read()
                f.execute(code)
        else:
            print(f"Argumento no reconocido: {arg}")
            print(__doc__)
    else:
        print("=" * 60)
        print("PFForth v2.0 - Modular Edition")
        print("Pere Font 2025")
        print("=" * 60)
        print()
        print("Instancia de Forth creada como 'f'")
        print()
        print("Ejemplos DSL:")
        print("  f.push(10, 20).add().dot()       # 30")
        print("  f.execute('10 20 + .')           # 30")
        print()
        print("Para REPL de Forth:")
        print("  f.repl()                         # REPL interactivo")
        print()
        print("Documentacion:")
        print("  f.execute('help')                # Ver palabras")
        print("  f.execute('words')               # Listar palabras")
        print("=" * 60)
        print()
        
        f = create_forth()
        
        import code
        code.interact(local=locals(), banner="")

if __name__ == "__main__":
    main()
