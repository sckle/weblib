from __future__ import print_function
import builtins
import os
from flask import Flask
from flask_mqtt import Mqtt

class MqttClient:
    def __init__(self, j, on_message_callback=None):
        self.jConfig = j
        self.clientLockFile = j["clientLockFile"]

        if os.path.exists(self.clientLockFile):
            os.remove(self.clientLockFile)

        self.app = Flask(__name__)
        self.app.config['MQTT_BROKER_URL'] = self.jConfig["host"]
        self.app.config['MQTT_BROKER_PORT'] = self.jConfig["port"]
        self.app.config['MQTT_USERNAME'] = self.jConfig["user"]
        self.app.config['MQTT_PASSWORD'] = self.jConfig["password"]
        self.app.config['MQTT_REFRESH_TIME'] = 1.0

        self.mqtt = Mqtt(self.app)

        # Register internal connect/disconnect handlers
        self.mqtt.on_connect()(self.mqtt_on_connect)
        self.mqtt.on_disconnect()(self.mqtt_on_disconnect)

        # Register external on_message handler if provided
        if on_message_callback:
            self.mqtt.on_message()(on_message_callback)
            builtins.print("Custom on_message callback registered.")
        else:
            builtins.print("No on_message callback provided.")

    def mqtt_on_connect(self, client, userdata, flags, rc):
        if not os.path.exists(self.clientLockFile):
            open(self.clientLockFile, 'a').close()

        builtins.print(f"MqttClient.on_connect ... {self.app.config['MQTT_BROKER_URL']}")

        # Subscribe to topics if defined
        topics = self.jConfig.get("topic")
        if topics:
            if isinstance(topics, str):
                topics = [topics]
            for topic in topics:
                builtins.print(f"Subscribing to topic: {topic}")
                self.mqtt.subscribe(topic)

    def mqtt_on_disconnect(self):
        if os.path.exists(self.clientLockFile):
            os.remove(self.clientLockFile)
        builtins.print(f"MqttClient.on_disconnect ... ({self.app.config['MQTT_BROKER_URL']})")

    def publish(self, topic, message):
        try:
            self.mqtt.publish(topic, message)
        except Exception as e:
            builtins.print(f"Error publishing message: {e}")
