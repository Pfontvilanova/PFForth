# FORTH CODE WORD: code/wifi/sockclose
# Close a socket

WORD_NAME = 'sock-close'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( sock -- ) Close the socket
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: SOCK-CLOSE requiere socket")
        return
    
    sock = pop()
    
    try:
        sock.close()
    except Exception as e:
        print(f"Error close: {e}")
