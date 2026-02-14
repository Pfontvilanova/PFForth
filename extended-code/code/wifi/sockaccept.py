# FORTH CODE WORD: code/wifi/sockaccept
# Accept incoming connection on socket

WORD_NAME = 'sock-accept'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( sock -- client-sock addr ) Accept connection, return client socket and address
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: ACCEPT requiere socket")
        return
    
    sock = pop()
    
    try:
        client, addr = sock.accept()
        push(sock)
        push(client)
        push(f"{addr[0]}:{addr[1]}")
    except Exception as e:
        print(f"Error accept: {e}")
        push(sock)
        push(0)
        push("")
