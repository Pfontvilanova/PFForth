# FORTH CODE WORD: code/wifi/send
# Send data through socket

WORD_NAME = 'send'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( sock str -- n ) Send string through socket, return bytes sent
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: SEND requiere (sock str)")
        return
    
    data = str(pop())
    sock = pop()
    
    try:
        n = sock.send(data.encode('utf-8'))
        push(sock)
        push(n)
    except Exception as e:
        print(f"Error send: {e}")
        push(sock)
        push(0)
