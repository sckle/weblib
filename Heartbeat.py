import threading
import json
import time

from app.weblib import network_data

class Heartbeat:
    def __init__(self, mqttClient, hostname, timer):
        self.thread = threading.Thread(target=self.run)
        self.mqttClient = mqttClient

        self.running = True
        self.hostname = hostname
        self.timer = timer

        self.thread.start()
        print("Thread Heartbeat started.")

    def run(self):
        while self.running:
            data = {
                "hostname": self.hostname,
                "timestamp": int(time.time() * 1000),
                "ifconfig": network_data.get_ifconfig_data(),
                "iwconfig": network_data.get_iwconfig_data()
            }

            self.mqttClient.publish(self.hostname + "/heartbeat", json.dumps(data))
            time.sleep(self.timer)
