# FORTH CODE WORD: code/wifi/mqttconnecttls
# Connect to MQTT broker over verified TLS with username/password
# (HiveMQ Cloud i similars, port 8883)

WORD_NAME = 'mqtt-connect-tls'
#
# === CÓDIGO FORTH ORIGINAL ===
# ( broker port user pass -- client ) Connect with TLS + auth
# El certificat del broker es verifica amb els CA del sistema
# (a l'iPad/desktop hi son; no cal fitxer CA com als micros).
# === FIN CÓDIGO FORTH ===

import paho.mqtt.client as mqtt


def execute(forth):
    def push(val):
        forth.stack.append(val)

    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()

    if len(forth.stack) < 4:
        print("Error: MQTT-CONNECT-TLS requiere (broker port user pass)")
        return

    password = str(pop())
    user = str(pop())
    port = int(pop())
    broker = str(pop())

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.tls_set()          # CA del sistema + verificacio de hostname
        if user:
            client.username_pw_set(user, password)
        client.connect(broker, port, 60)
        client.loop_start()
        push(client)
        print(f"MQTT TLS conectado a {broker}:{port}")
    except Exception as e:
        print(f"Error MQTT connect TLS: {e}")
        push(None)
