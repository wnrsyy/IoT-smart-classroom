
from machine import Pin
from umqtt.simple import MQTTClient
import time
import esp32
import dht
import gc
import json
import network

gc.collect()

# Setting GPIO Pin for DHT22 sensor
sensor = dht.DHT22(Pin(16))

# Setting GPIO Pin for PIR sensor
PIR_SENSOR_OUTPUT_PIN = 23  
pir_sensor = Pin(PIR_SENSOR_OUTPUT_PIN, Pin.IN)

# MQTT Configuration
mqtt_broker = "192.168.43.212"
mqtt_client_id = "esp32-sensor"
sensor_topic = "sensor_data"

client = None

# Wi-Fi Connection
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to Wi-Fi...')
        wlan.connect('666wifipassword', '1133335678')  
        timeout = 10  
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        print('Connected to Wi-Fi:', wlan.ifconfig()[0])
    else:
        print("Failed to connect to Wi-Fi. Restarting...")
        machine.reset()

# MQTT Connection
def connect_mqtt():
    global client
    try:
        client = MQTTClient(mqtt_client_id, mqtt_broker, port=1883, user=None, password=None, keepalive=300, ssl=False)
        client.connect(clean_session=False)
        client.set_last_will(sensor_topic, "Disconnected")
        print("Connected to MQTT broker")
    except OSError as e:
        print("Failed to connect to MQTT broker: ", e)
        time.sleep(5)
        connect_mqtt()

def disconnect_mqtt():
    global client
    if client:
        try:
            client.disconnect()
            print("Disconnected from MQTT broker")
        except OSError as e:
            print("Error disconnecting MQTT: ", e)

# Variables for tracking temperature changes
last_temperature = None
last_timestamp = time.time()

# Function to read temperature, detect A/C status
def reading_sensor():
    global last_temperature, last_timestamp
    
    try:
        sensor.measure()
        temperature = sensor.temperature()  # Celsius
        humidity = sensor.humidity()
        temperature_esp32 = esp32.raw_temperature()  # ESP32 internal temp (already Celsius)
        
        # Get current time
        current_timestamp = time.time()

        # Air-conditioning detection (every 5 minutes)
        ac_status = "unknown"
        if last_temperature is not None and (current_timestamp - last_timestamp) >= 300:  # 5 minutes
            temperature_change = temperature - last_temperature  # Check temperature difference
            
            if temperature_change <= -1.0:  # Decreased by 1°C (A/C ON)
                ac_status = "on"
            elif temperature_change >= 1.0:  # Increased by 1°C (A/C OFF)
                ac_status = "off"
            
            # Update last recorded temperature and timestamp
            last_temperature = temperature
            last_timestamp = current_timestamp
        
        # First-time temperature storage
        if last_temperature is None:
            last_temperature = temperature
        
        # Prepare data for MQTT
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "esp32_temperature": temperature_esp32,
            "ac_status": ac_status
        }
        payload = json.dumps(data)

        if client:
            print(f"Publishing to MQTT: {payload}")
            client.publish(sensor_topic, payload)
        else:
            print("MQTT client not connected!")

    except Exception as e:
        print("Error reading sensor:", e)

# PIR Sensor Detection
def check_pir():
    global warm_up
    sensor_output = pir_sensor.value()
    if sensor_output == 0:
        if warm_up == 1:
            warm_up = 0
        print("Nobody here (--!)\n")
    else:
        print("I'm here!\n")
        warm_up = 1

print("Waiting For Power On Warm Up")
