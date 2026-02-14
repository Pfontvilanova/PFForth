# FORTH CODE WORD: code/wifi/httpbody
# Get HTTP response body as text

WORD_NAME = 'http-body'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( response -- str ) Get response body as string
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: HTTP-BODY requiere response")
        return
    
    resp = pop()
    
    try:
        if resp is None:
            push("")
        else:
            push(resp.text)
    except Exception as e:
        print(f"Error: {e}")
        push("")
