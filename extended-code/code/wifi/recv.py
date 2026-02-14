# FORTH CODE WORD: code/wifi/recv
# Receive data from socket

WORD_NAME = 'recv'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( sock n -- str ) Receive up to n bytes, return as string
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: RECV requiere (sock n)")
        return
    
    n = int(pop())
    sock = pop()
    
    try:
        data = sock.recv(n)
        push(sock)
        push(data.decode('utf-8', errors='replace'))
    except Exception as e:
        print(f"Error recv: {e}")
        push(sock)
        push("")
