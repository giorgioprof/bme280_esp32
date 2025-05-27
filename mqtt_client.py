import time
from umqtt.simple import MQTTClient

class MqttClient:
    def __init__(self, device, mqtt_host, mqtt_port=1883, mqtt_user=None, mqtt_password=None):
        self.device = device
        self.broker = mqtt_host
        self.port = mqtt_port
        self.username = mqtt_user
        self.password = mqtt_password
        self.client = MQTTClient(
            self.device,
            self.broker,
            port=self.port,
            user=self.username,
            password=self.password
        )
        
    def publish(self, topic, message):
        self.client.connect()
        time.sleep_ms(100)
        self.client.publish(topic, message)
        time.sleep_ms(100)            
        self.client.disconnect()
