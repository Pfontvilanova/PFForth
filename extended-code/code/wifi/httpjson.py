# FORTH CODE WORD: code/wifi/httpjson
# Parse HTTP response as JSON

WORD_NAME = 'http-json'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( response -- dict ) Parse response body as JSON
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: HTTP-JSON requiere response")
        return
    
    resp = pop()
    
    try:
        if resp is None:
            push({})
        else:
            push(resp.json())
    except Exception as e:
        print(f"Error JSON: {e}")
        push({})
