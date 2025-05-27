from machine import Pin, deepsleep, RTC, reset
import machine
import time
from sensor import CompactSensorNode
from led_handler import Led
from config import Config
from custom_exceptions import MissingConfig, InvalidConfig
from wifi_utils import WiFiSetup

# Hardware configuration
LED_PIN = 2  # Built-in LED
CONFIG_FILE = 'config.json'

# Timing configuration
MINUTE_MS = 1000
SLEEP_TIME_MS = 5 * MINUTE_MS  

rtc = RTC()

# Boot detection and initialization
def main():
    try:
        settings = Config(
            CONFIG_FILE
        )
    except (MissingConfig, InvalidConfig) as ex:
        wifi_config = WiFiSetup()
        ap = wifi_config.start_access_point()
        config = wifi_config.setup_web_server()
        # Clean up
        ap.active(False)
        
        if config:
            try:
                settings = Config(
                    CONFIG_FILE,
                    config_dict=config
                )
                time.sleep(1)
            except Exception as ex:
                print('Failed to save config', ex)
        reset()

    """Main entry point"""
    # Check reset cause
    reset_cause = machine.reset_cause()
    
    if reset_cause == machine.DEEPSLEEP_RESET:
        print("Woke from deep sleep")
    else:
        print("Power on or reset")
        # Clear RTC memory on fresh start
        rtc.memory(b'')
    
    # Run sensor node
    try:
        led = Led(LED_PIN)
        node = CompactSensorNode(led, settings)
        node.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        # Flash rapidly to indicate error
        for _ in range(20):
            led.invert()
            time.sleep_ms(100)
        # Sleep and try again
        deepsleep(SLEEP_TIME_MS)

# Run main program
if __name__ == "__main__":
    main()