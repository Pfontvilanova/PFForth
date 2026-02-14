# FORTH CODE WORD: code/wifi/bind
# Bind socket to local port

WORD_NAME = 'bind'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( sock port -- flag ) Bind socket to local port
# Returns -1 on success, 0 on failure
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: BIND requiere (sock port)")
        return
    
    port = int(pop())
    sock = pop()
    
    try:
        sock.setsockopt(1, 2, 1)  # SOL_SOCKET, SO_REUSEADDR
        sock.bind(('0.0.0.0', port))
        push(sock)
        push(-1)
    except Exception as e:
        print(f"Error bind: {e}")
        push(sock)
        push(0)
