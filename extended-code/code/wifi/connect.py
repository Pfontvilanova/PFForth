# FORTH CODE WORD: code/wifi/connect
# Connect socket to remote host

WORD_NAME = 'connect'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( sock addr port -- flag ) Connect to remote host
# Returns -1 on success, 0 on failure
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 3:
        print("Error: CONNECT requiere (sock addr port)")
        return
    
    port = int(pop())
    addr = str(pop())
    sock = pop()
    
    try:
        sock.connect((addr, port))
        push(sock)
        push(-1)
    except Exception as e:
        print(f"Error connect: {e}")
        push(sock)
        push(0)
