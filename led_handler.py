"""
ESP32 BME280 Sensor with Deep Sleep and MQTT Batch Sending
Collects 5 readings (one per minute), then sends via MQTT
"""
from machine import Pin, I2C, deepsleep, RTC, reset
import machine
import time


class Led:
    def __init__(self, pin):
        self.led = Pin(pin, Pin.OUT)
    
    def turn_led_on(self):
        self.led.on()

    def turn_led_off(self):
        self.led.off()
    
    def invert(self):
        self.led.value(not self.led.value())
    
    def flash_led(self, times=2, delay_ms=300):
        """Flash LED specified number of times"""
        for _ in range(times):
            self.turn_led_on()
            time.sleep_ms(delay_ms)
            self.turn_led_off()
            time.sleep_ms(delay_ms)
