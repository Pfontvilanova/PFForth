# FORTH CODE WORD: code/wifi/mqttcallback
# Set callback for received messages

WORD_NAME = 'mqtt-callback'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( client word-name -- client ) Set callback word for messages
# The word receives (topic msg) on stack when message arrives
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: MQTT-CALLBACK requiere (client word-name)")
        return
    
    word_name = str(pop())
    client = pop()
    
    try:
        if client:
            if word_name not in forth.words:
                print(f"Error: palabra '{word_name}' no existe")
                push(client)
                return
            
            def on_message(cl, userdata, msg):
                try:
                    forth.stack.append(msg.topic)
                    forth.stack.append(msg.payload.decode('utf-8', errors='replace'))
                    forth.words[word_name]()
                except Exception as ex:
                    print(f"Error en callback: {ex}")
            
            client.on_message = on_message
            print(f"Callback asignado: {word_name}")
        push(client)
    except Exception as e:
        print(f"Error MQTT callback: {e}")
        push(client)
