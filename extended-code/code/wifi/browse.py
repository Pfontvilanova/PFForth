# FORTH CODE WORD: code/wifi/browse
# Open URL in web browser

WORD_NAME = 'browse'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( url -- ) Open URL in system web browser
# === FIN CÓDIGO FORTH ===

def execute(forth):
    import webbrowser
    
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 1:
        print("Error: BROWSE requiere URL")
        return
    
    url = str(pop())
    
    try:
        webbrowser.open(url)
        print(f"Abriendo: {url}")
    except Exception as e:
        print(f"Error browse: {e}")
