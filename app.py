import socket
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_mqtt import Mqtt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from sqlalchemy import text
import logging
from datetime import datetime

# ตั้งค่า logging
logging.basicConfig(filename='sensor_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder="www/")
app.config['SECRET_KEY'] = 'secret_key'
# socketio = SocketIO(app)
# mqtt = Mqtt(app)

app.config['MQTT_BROKER_URL'] = '192.168.43.212'  
app.config['MQTT_BROKER_PORT'] = 1883  
app.config['MQTT_USERNAME'] = ''  
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 300 
app.config['MQTT_TLS_ENABLED'] = False 
topic = "+"

socketio = SocketIO(app)
mqtt = Mqtt(app)
mqtt_sensor_topic = "sensor_data"
mqtt_relay_topic = "relay_controller"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://miso:1234@10.161.112.160:5432/iot_smart_classroom_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def test_db_connection():
    try:
        # ใช้ text() เพื่อประกาศเป็น raw SQL ที่ถูกต้อง
        result = db.session.execute(text("SELECT * FROM relay_data;"))
        print("✅ Database connected successfully: ", result.fetchone())
    except Exception as e:
        print("❌ Error connecting to database:", e)

def parse_sensor_data(data):
    sensor_data = json.loads(data)
    temperature = sensor_data.get('temperature', 0)
    humidity = sensor_data.get('humidity', 0)
    esp32_temperature = sensor_data.get('esp32Temperature', 0)

    # Send to Database
    with app.app_context():
        send_db(temperature, humidity, esp32_temperature)

    return {
        'temperature': temperature,
        'humidity': humidity,
        'esp32Temperature': esp32_temperature
    }


def send_db(temperature, humidity, esp32_temperature):
    try:
        logging.info("send_db function called")
        logging.info(f"Received values -> Temperature: {temperature}, Humidity: {humidity}, ESP32 Temperature: {esp32_temperature}")

        logging.info("Connecting to database...")

        current_time = datetime.now()
        date_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        logging.info("Executing SQL command...")

        db.session.execute(
            "INSERT INTO sensor_data (temperature, humidity, esp32_temperature, update_time) VALUES (:temperature, :humidity, :esp32_temperature, :update_time)",
            {
                'temperature': temperature,
                'humidity': humidity,
                'esp32_temperature': esp32_temperature,
                'update_time': date_time
            }
        )
        db.session.commit()
        logging.info("Insert data successful")
    except Exception as e:
        logging.error(f"Error while inserting data: {e}")
        db.session.rollback()
        return "error"

# MQTT
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe(mqtt_sensor_topic)  # ใช้หัวข้อที่กำหนดไว้
    mqtt.subscribe(mqtt_relay_topic)   # ถ้าต้องการรับคำสั่งรีเลย์ด้วย
    print("Connected to MQTT Broker")




@mqtt.on_message()
def handle_message(client, userdata, message):
    data = message.payload.decode()
    print(f"Received MQTT message: {data}")
    if message.topic == "sensor_data":
        try:
            parsed_data = parse_sensor_data(data)
            print(f"Parsed data: {parsed_data}")
        except Exception as e:
            print(f"Error parsing data: {e}")
            return
        
        # ตรวจสอบว่าค่ามีอยู่หรือไม่
        if not parsed_data.get('temperature') or not parsed_data.get('humidity'):
            print("Missing sensor data")
        
        motion_detected = parsed_data.get('motionDetected', False)
        socketio.emit('sensorData', parsed_data, namespace='/')
        socketio.emit('motionStatus', motion_detected, namespace='/')

@socketio.on('relay')
def handle_relay(data):
    print("Received relay message:", data)
    # Send to Broker
    mqtt.publish(mqtt_relay_topic, json.dumps(data))

    # Send to Database
    with app.app_context():
        relay_number = data.get('relayNumber', 0)
        relay_state = data.get('state', 0)
        try:
            current_time = datetime.now()
            date_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            
            db.session.execute(
                "INSERT INTO relay_data (relay_number, relay_state, update_time) VALUES (:relay_number, :relay_state, :update_time)",
                {
                    'relay_number': relay_number,
                    'relay_state': relay_state,
                    'update_time': date_time
                }
            )
            db.session.commit()

            resp = jsonify(message="Data added successfully!!")
            resp.status_code = 200
            return resp
        except Exception as e:
            print(e)
            db.session.rollback()
            return jsonify(message="adding data error"), 500

@socketio.on('connect')
def on_connect():
    print('Client connected')
    socketio.emit('message', 'Connected to server')

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')
    socketio.emit('message', 'state: disconnected')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # สร้างตารางหากยังไม่มี
        test_db_connection()
        print("Database connected successfully")
    print("Server is running on http://127.0.0.1:5000/")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)


