# FORTH CODE WORD: code/wifi/listen
# Set socket to listen mode

WORD_NAME = 'listen'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( sock -- ) Set socket to listen for connections (backlog=5)
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: LISTEN requiere socket")
        return
    
    sock = pop()
    
    try:
        sock.listen(5)
        push(sock)
        push(-1)
    except Exception as e:
        print(f"Error listen: {e}")
        push(sock)
        push(0)
