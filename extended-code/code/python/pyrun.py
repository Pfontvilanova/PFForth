# FORTH CODE WORD: code/python/pyrun
# Execute a Python file

WORD_NAME = 'py-run'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( filename -- ) Execute Python file with access to Forth interpreter
# === FIN CÓDIGO FORTH ===

def execute(forth):
    import os
    
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: PY-RUN requiere nombre de fichero")
        return
    
    filename = str(pop())
    
    if not filename.endswith('.py'):
        filename += '.py'
    
    search_paths = [
        filename,
        os.path.join('extended-code', filename),
        os.path.join('extended-code', 'python', filename),
    ]
    
    filepath = None
    for path in search_paths:
        if os.path.exists(path):
            filepath = path
            break
    
    if not filepath:
        print(f"Error: No se encuentra '{filename}'")
        return
    
    try:
        if not hasattr(forth, 'shared'):
            forth.shared = {}
        
        env = {
            'forth': forth,
            'stack': forth.stack,
            'push': lambda v: forth.stack.append(v),
            'pop': lambda: forth.stack.pop() if forth.stack else None,
            'shared': forth.shared,
            'execute': lambda code: forth.execute(code),
        }
        
        with open(filepath, 'r') as f:
            code = f.read()
        
        exec(code, env)
        
    except Exception as e:
        print(f"Error ejecutando '{filepath}': {e}")
