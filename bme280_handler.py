from machine import Pin, I2C
import bme280
import time

class Bme280Sensor:
    def __init__(self, sda, scl, address=0x77):
        self.sda = sda
        self.scl = scl
        self.address = address
        self.i2c = I2C(0, scl=Pin(self.scl), sda=Pin(self.sda))
        
        # Initialize BME280
        self.bme = bme280.BME280(i2c=self.i2c, address=self.address)
        # Stabilize sensor
        time.sleep_ms(100)
        for _ in range(3):
            _ = self.bme.values
            time.sleep_ms(10)
   
    @property   
    def readings(self):
        return self.bme.values
