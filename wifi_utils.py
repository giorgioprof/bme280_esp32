from machine import reset
import network
import time
import utime


AP_SSID = "WeatherStation"  # Access Point name when in setup mode
AP_PASSWORD = "setupmode"  # Password for setup mode (at least 8 characters)
CONFIG_MODE_TIMEOUT = 300

class WiFiCls:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF)


    def connect(self):
        """Connect to WiFi"""
        self.wlan.active(True)
        
        if not self.is_connected:
            print(f"Connecting to WiFi: {self.ssid}")
            self.wlan.connect(self.ssid, self.password)
            
            timeout = 20  # 20 second timeout
            while not self.is_connected and timeout > 0:
                time.sleep(1)
                timeout -= 1
                print(".", end="") 
            
        if self.is_connected:
            print(f"Connected! IP: {self.wlan.ifconfig()[0]}")
            return True, None
        else:
            print("WiFi connection failed!")
            return False, self.wlan.status() in (network.STAT_WRONG_PASSWORD, network.STAT_NO_AP_FOUND)
    
    def disconnect(self):        
        self.wlan.active(False)
            
    @property
    def is_connected(self):
        return self.wlan.isconnected()


class WiFiSetup:
    def __init__(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(False)
        
    def setup_web_server(self):
        """Setup a web server for configuration"""
        import socket
        
        # Create a socket and bind to address
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('0.0.0.0', 80))
            s.listen(5)
            s.settimeout(2)  # 2 second timeout for accepting connections
        except OSError as ex:
            print(f"Error starting AP: {ex}")
            reset()
        
        print("Web server started")
        
        # HTML template for the configuration page
        # HTML template for the configuration page
        html = """<!DOCTYPE html>
        <html>
        <head>
            <title>Weather Station Setup</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial; margin: 0; padding: 20px; }
                h1 { color: #0066cc; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                input[type="text"], input[type="password"] { width: 100%; padding: 8px; box-sizing: border-box; }
                button { background-color: #0066cc; color: white; border: none; padding: 10px 15px; cursor: pointer; }
                .message { margin-top: 20px; padding: 10px; background-color: #e6f7ff; border-left: 4px solid #0066cc; }
            </style>
        </head>
        <body>
            <h1>Weather Station Wi-Fi Setup</h1>
            <form method="POST" action="/save">
                <div class="form-group">
                    <label for="ssid">Wi-Fi Name (SSID):</label>
                    <input type="text" id="ssid" name="ssid" required>
                </div>
                <div class="form-group">
                    <label for="password">Wi-Fi Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <div class="form-group">
                    <label for="device">Device name:</label>
                    <input type="text" id="device" name="device" required value="Herm-Meteo-1">
                </div>
                <div class="form-group">
                    <label for="broker">Mqtt broker:</label>
                    <input type="text" id="broker" name="broker" required value="192.168.68.134">
                </div>
                <div class="form-group">
                    <label for="port">Mqtt port:</label>
                    <input type="number" id="port" name="port" required value=1883>
                </div>
                <div class="form-group">
                    <label for="mqqtuser">Mqtt username:</label>
                    <input type="text" id="mqqtuser" name="mqqtuser" required value="giorgioprof">
                </div>
                <div class="form-group">
                    <label for="mqqtpass">Mqtt password:</label>
                    <input type="password" id="mqqtpass" name="mqqtpass" required>
                </div>
                <div class="form-group">
                    <label for="mqqttopic">Mqtt topic:</label>
                    <input type="text" id="mqqttopic" name="mqqttopic" required value="sensors/readings">
                </div>
                <div class="form-group">
                    <label for="readingsnum">Number of readings before publishing:</label>
                    <input type="number" id="readingsnum" name="readingsnum" required value=5>
                </div>
                <div class="form-group">
                    <label for="readingssleep">Number of minutes between readings:</label>
                    <input type="number" id="readingssleep" name="readingssleep" required value=5>
                </div>
                <button type="submit">Save Configuration</button>
            </form>
            <div class="message">
                <p>After saving, the weather station will restart and connect to your Wi-Fi network.</p>
                <p>If connection fails, it will return to setup mode automatically.</p>
            </div>
        </body>
        </html>
        """
        
        # HTML response for a successful save
        success_html = """<!DOCTYPE html>
        <html>
        <head>
            <title>Configuration Saved</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial; margin: 0; padding: 20px; text-align: center; }
                h1 { color: #00cc66; }
                .message { margin-top: 20px; padding: 20px; background-color: #e6fff2; border-left: 4px solid #00cc66; text-align: left; }
            </style>
            <meta http-equiv="refresh" content="10;url=/" />
        </head>
        <body>
            <h1>Configuration Saved Successfully!</h1>
            <div class="message">
                <p>Your Wi-Fi credentials have been saved.</p>
                <p>The weather station will now restart and connect to your network.</p>
                <p>Please wait while the device restarts...</p>
            </div>
        </body>
        </html>
        """
        
        # Record the start time
        start_time = time.time()
        
        while True:           
            # Check for timeout
            if time.time() - start_time > CONFIG_MODE_TIMEOUT:
                return False
            
            try:
                # Wait for a connection
                conn, addr = s.accept()
                print(f"Connection from ** {addr}")
                
                # Get the request
                request = conn.recv(1024).decode('utf-8')
                print('Request', request) 
                
                # Parse the request
                if request.startswith('POST /save'):
                    # Find the form data in the request
                    print("Received a save request")
                    
                    content_length = 0
                    for line in request.split('\r\n'):
                        if line.startswith('Content-Length:'):
                            content_length = int(line.split(':')[1].strip())
                            print(f"Content length: {content_length}")
                    
                    # If we found a content length, look for form data
                    if content_length > 0:
                        # Find the form data after the headers
                        headers_end = request.find('\r\n\r\n')
                        
                        if headers_end > -1:
                            body_start = headers_end + 4  # Skip the \r\n\r\n
                            
                            # If body is incomplete, receive more data
                            body = request[body_start:]
                            
                            # If we don't have enough data yet, read more
                            while len(body) < content_length:
                                more_data = conn.recv(1024).decode('utf-8')
                                if not more_data:
                                    break
                                body += more_data
                            
                            print(f"Form data: {body}")
                        
                    # Parse the form data
                    fields = {}
                    for field in body.split('&'):
                        key, value = field.split('=')
                        fields[key] = value.replace('+', ' ')
                    # Extract the Wi-Fi credentials
                    ssid = fields.get('ssid', '')
                    password = fields.get('password', '')
                    device_name = fields.get('device', '')
                    mqtt_broker = fields.get('broker', '')
                    mqtt_port = fields.get('port', '')
                    mqtt_user = fields.get('mqqtuser', '')
                    mqtt_pass = fields.get('mqqtpass', '')
                    mqtt_topic = fields.get('mqqttopic', '')
                    readings_sleep = int(fields.get('readingssleep', 60))
                    readings_number = int(fields.get('readingsnum', 10))
                    
                    # Save the credentials
                    if ssid:
                        print("Saving WIFI credentials to file")
                        # Send success response
                        conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
                        conn.send(success_html)
                        conn.close()
                        
                        # Wait a moment for the user to see the message
                        utime.sleep(3)
                        return {
                            'wifi': {
                                'ssid': ssid,
                                'password': password
                            },
                            'device': {
                                'name': device_name
                            },
                            'mqtt': {
                                'broker': mqtt_broker,
                                'port': mqtt_port,
                                'username': mqtt_user,
                                'password': mqtt_pass,
                                'topic': mqtt_topic
                            },
                            'readings': {
                                'number': readings_number,
                                'sleep': readings_sleep * 60 * 1000
                            }
                        }
                else:
                    # Send the configuration page
                    conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
                    conn.send(html)
                
                conn.close()
            
            except Exception as e:
                # Socket timeout or other error
                pass
            
            # Small delay to prevent CPU overload
            utime.sleep(0.1)
    
    def start_access_point(self):
        """Start access point for configuration"""
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=AP_SSID, password=AP_PASSWORD)
        
        while not ap.active():
            pass
        
        print("Access point started")
        print(f"SSID: {AP_SSID}")
        print(f"Password: {AP_PASSWORD}")
        print(f"IP address: {ap.ifconfig()[0]}")
        return ap
