import json
import time
import socket
import sys
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from DS18B20 import DS18B20

# Store connection state
userdata = {"connected": False}

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to MQTT broker successfully.")
        userdata["connected"] = True
    else:
        print(f"Failed to connect, return code {rc}")
        userdata["connected"] = False

def on_disconnect(client, userdata, rc, properties=None):
    print(f"Disconnected from MQTT broker with code {rc}")
    userdata["connected"] = False
    if rc != 0:
        print("Unexpected disconnection. Will attempt to reconnect.")

def publish_ambient_temperature(mqtt_client, topic, temperatureSensorId, temperature, unit):
    if temperature is None:
        print("Temperature is None !!!")

    if not userdata["connected"]:
        print("Waiting for MQTT connection...")
        time.sleep(1)
        return True

    global hostname
    data = {
        "hostname": hostname,
        "timestamp": int(time.time() * 1000),
        "id": temperatureSensorId,
        "ambientTemperature": {
            "value": temperature,
            "unit": unit
        }
    }
    payload = json.dumps(data)

    print(f"temperature: {payload}")

    try:
        result = mqtt_client.publish(topic, payload)
        status = result[0]
        if status == mqtt.MQTT_ERR_SUCCESS:
            print(f"Sent message to topic `{topic}`")
        else:
            print(f"Failed to send message to topic `{topic}`, error code: {status}")
            return False

    except Exception as e:
        print(f"Exception during publishing: {e}")

    return True

def main(settings_path="conf/settings.json"):
    # Load settings
    with open(settings_path, "r") as f:
        jSettings = json.load(f)

    global hostname
    hostname = socket.gethostname()
    mqtt_conf = jSettings["MQTT-AWS"]
    broker = mqtt_conf["broker"]
    port = mqtt_conf["port"]
    topic = f"{hostname}/{jSettings['DS18B20']['topic']}"
    interval = mqtt_conf["interval"]
    username = mqtt_conf.get("username")
    password = mqtt_conf.get("password")

    mqtt_client = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        userdata=userdata
    )
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect

    if username and password:
        mqtt_client.username_pw_set(username=username, password=password)

    mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)

    try:
        mqtt_client.connect(broker, port)
    except Exception as e:
        print(f"Could not connect to MQTT broker: {e}")
        sys.exit(1)

    try:
        mqtt_client.loop_start()

        ambientTemperatureSensorId = jSettings["DS18B20"]["id"][0]
        ambientTemperatureSensor = DS18B20(ambientTemperatureSensorId)
        ambientTemperatureSensor.start()

        while True:
            temperature, unit = ambientTemperatureSensor.get_temperature()
            if not publish_ambient_temperature(mqtt_client, topic, ambientTemperatureSensorId, temperature, unit):
                return
            time.sleep(10)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
