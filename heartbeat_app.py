import json
import time
import socket
import sys
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import network_data

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

def main(jSettings_path="conf/jSettings.json"):
    # Load jSettings
    with open(jSettings_path, "r") as f:
        jSettings = json.load(f)

    hostname = socket.gethostname()
    mqtt_conf = jSettings["MQTT-AWS"]
    broker = mqtt_conf["broker"]
    port = mqtt_conf["port"]
    topic = f"{hostname}/{jSettings['heartbeat']['topic']}"
    username = mqtt_conf.get("username")
    password = mqtt_conf.get("password")
    heartbeat_interval = jSettings["heartbeat"]["interval"]

    # Store connection state
    userdata = {"connected": False}

    client = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        userdata=userdata
    )
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    if username and password:
        client.username_pw_set(username=username, password=password)

    client.reconnect_delay_set(min_delay=1, max_delay=30)

    try:
        client.connect(broker, port)
    except Exception as e:
        print(f"Could not connect to MQTT broker: {e}")
        sys.exit(1)

    try:
        client.loop_start()

        while True:
            if not userdata["connected"]:
                print("Waiting for MQTT connection...")
                time.sleep(1)
                continue

            data = {
                "hostname": hostname,
                "timestamp": int(time.time() * 1000),
                "ifconfig": network_data.get_ifconfig_data(),
                "iwconfig": network_data.get_iwconfig_data()
            }
            payload = json.dumps(data)

            try:
                result = client.publish(topic, payload)
                status = result[0]
                if status == mqtt.MQTT_ERR_SUCCESS:
                    print(f"Sent message to topic `{topic}`")
                else:
                    print(f"Failed to send message to topic `{topic}`, error code: {status}")
                    return
            except Exception as e:
                print(f"Exception during publishing: {e}")
                return

            time.sleep(heartbeat_interval)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
