# FORTH CODE WORD: code/wifi/mqttconnect
# Connect to MQTT broker

WORD_NAME = 'mqtt-connect'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( broker port -- client ) Connect to MQTT broker
# === FIN CÓDIGO FORTH ===

import paho.mqtt.client as mqtt

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    if len(forth.stack) < 2:
        print("Error: MQTT-CONNECT requiere (broker port)")
        return
    
    port = int(pop())
    broker = str(pop())
    
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(broker, port, 60)
        client.loop_start()
        push(client)
        print(f"MQTT conectado a {broker}:{port}")
    except Exception as e:
        print(f"Error MQTT connect: {e}")
        push(None)
