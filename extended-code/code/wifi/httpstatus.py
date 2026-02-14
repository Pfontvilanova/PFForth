# FORTH CODE WORD: code/wifi/httpstatus
# Get HTTP response status code

WORD_NAME = 'http-status'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( response -- code ) Get HTTP status code
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: HTTP-STATUS requiere response")
        return
    
    resp = pop()
    
    try:
        if resp is None:
            push(0)
        else:
            push(resp.status_code)
    except Exception as e:
        print(f"Error: {e}")
        push(0)
