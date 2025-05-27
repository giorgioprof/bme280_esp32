"""
ESP32 BME280 Sensor with Deep Sleep and MQTT Batch Sending
Collects 5 readings (one per minute), then sends via MQTT
"""
from machine import Pin, I2C, deepsleep, RTC, reset
import machine
import bme280
import time
import json
import gc
from wifi_utils import WiFiCls
from mqtt_client import MqttClient
from bme280_handler import Bme280Sensor

# Hardware configuration
LED_PIN = 2  # Built-in LED
SDA_PIN = 21
SCL_PIN = 22
BME_ADDRESS = 0x77

# RTC memory to store readings between deep sleeps
rtc = RTC()

class SensorNode:
    def __init__(self, led, settings):
        self.settings_cls = settings
        self.settings = settings.config
        self.wifi = WiFiCls(
            self.settings.wifi.ssid,
            self.settings.wifi.password
        )
        self.mqtt = MqttClient(
            self.settings.device.name,
            self.settings.mqtt.broker,
            mqtt_port=self.settings.mqtt.port,
            mqtt_user=self.settings.mqtt.username,
            mqtt_password=self.settings.mqtt.password
        )
        self.led = led
        try:
            self.sensor = Bme280Sensor(SDA_PIN, SCL_PIN)
        except Exception as e:
            print(f"BME280 init error: {e}")
            self.led.flash_led(10, 100)  # Fast flashing indicates error
            deepsleep(self.settings.readings.sleep)
    
    def get_reading(self):
        """Get sensor reading"""
        temp, pressure, humidity = self.sensor.readings
        
        # Parse values
        temp_c = float(temp.replace('C', ''))
        pressure_hpa = float(pressure.replace('hPa', ''))
        humidity_pct = float(humidity.replace('%', ''))
        
        return {
            'timestamp': time.time(),
            'temp': temp_c,
            'pressure': pressure_hpa,
            'humidity': humidity_pct
        }
    
    def load_readings(self):
        """Load readings from RTC memory"""
        try:
            data = rtc.memory()
            if data and len(data) > 4:
                return json.loads(data.decode())
            return []
        except:
            return []
    
    def save_readings(self, readings):
        """Save readings to RTC memory"""
        try:
            data = json.dumps(readings).encode()
            if len(data) <= 2048:  # RTC memory limit
                rtc.memory(data)
                return True
            else:
                print("Data too large for RTC memory!")
                return False
        except Exception as e:
            print(f"Save error: {e}")
            return False
    
    def send_mqtt(self, readings):
        """Send readings via MQTT"""
        try:
            # Connect to WiFi
            connected, must_reset = self.wifi.connect()
            if not connected:
                if must_reset:
                    self.settings_cls.reset()
                return False
             
            # Publish data
            message = json.dumps(readings)
            self.mqtt.publish(self.settings.mqtt.topic, message)
            print(f"Published {len(readings)} readings to {self.settings.mqtt.topic}")
            self.wifi.disconnect()
            return True            
        except Exception as e:
            print(f"MQTT error: {e}")
            return False
    
    def run(self):
        """Main execution logic"""
        print(f"\n=== {self.settings.device.name} Starting ===")
        
        # Flash LED 2 times to indicate wake up
        self.led.flash_led(2)
        
        # Get current reading
        print("Taking measurement...")
        reading = self.get_reading()
        print(f"Temp: {reading['temp']:.1f}°C, "
              f"Pressure: {reading['pressure']:.1f}hPa, "
              f"Humidity: {reading['humidity']:.1f}%")
        
        # Load existing readings
        readings = self.load_readings()
        print(f"Loaded {len(readings)} previous readings")
        
        # Add new reading
        readings.append(reading)
        
        # Check if it's time to send
        if len(readings) >= self.settings.readings.number:
            print(f"\nTime to send {len(readings)} readings via MQTT")
            
            if self.send_mqtt(readings):
                # Clear readings after successful send
                readings = []
                self.led.flash_led(3, 100)  # 3 fast flashes for successful send
            else:
                # Keep readings if send failed
                print("MQTT send failed, keeping readings")
                self.led.flash_led(5, 100)  # 5 fast flashes for error
                
                # Limit stored readings to prevent memory overflow
                if len(readings) > self.settings.readings.number * 2:
                    readings = readings[-self.settings.readings.number:]
                    print(f"Trimmed readings to {len(readings)}")
        
        # Save readings
        self.save_readings(readings)
        print(f"Saved {len(readings)} readings to RTC memory")
        
        # Clean up
        gc.collect()
        
        # Enter deep sleep
        print(f"\nGoing to deep sleep for {self.settings.readings.sleep/1000} seconds...")
        print("=" * 40)
        deepsleep(self.settings.readings.sleep)

# Alternative: Store readings count in RTC memory (more reliable)
class CompactSensorNode(SensorNode):
    """
    Compact version that stores only count and latest readings
    More reliable for limited RTC memory
    """
    
    def load_data(self):
        """Load count and readings from RTC memory"""
        try:
            data = rtc.memory()
            if data and len(data) > 0:
                # First byte is count, rest is JSON data
                count = data[0]
                if len(data) > 1:
                    readings = json.loads(data[1:].decode())
                else:
                    readings = []
                return count, readings
            return 0, []
        except:
            return 0, []
    
    def save_data(self, count, readings):
        """Save count and readings to RTC memory"""
        try:
            # Store count as first byte
            data = bytes([count]) + json.dumps(readings).encode()
            rtc.memory(data)
            return True
        except:
            return False
    
    def run(self):
        """Simplified run method with count-based logic"""
        print(f"\n=== {self.settings.device.name} Compact Mode ===")
        
        # Flash LED
        self.led.flash_led(2)
        
        # Get reading
        reading = self.get_reading()
        print(f"Reading: T:{reading['temp']:.1f}°C, "
              f"P:{reading['pressure']:.1f}hPa, "
              f"H:{reading['humidity']:.1f}%")
        
        # Load data
        count, readings = self.load_data()
        print(f"Count: {count}, Stored readings: {len(readings)}")
        
        # Add new reading
        readings.append(reading)
        count += 1
        
        # Keep only last N readings to save memory
        if len(readings) > self.settings.readings.number:
            readings = readings[-self.settings.readings.number:]
        
        # Check if time to send
        if count >= self.settings.readings.number:
            print(f"\nSending {len(readings)} readings...")
            
            if self.send_mqtt(readings):
                count = 0
                readings = []
                self.led.flash_led(3, 100)
            else:
                self.led.flash_led(5, 100)
        
        # Save data
        self.save_data(count % 255, readings)  # Wrap count at 255
        
        # Deep sleep
        print(f"\nSleeping for {self.settings.readings.sleep/1000}s (count: {count})...")
        deepsleep(self.settings.readings.sleep)
