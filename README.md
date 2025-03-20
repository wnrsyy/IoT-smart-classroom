# IoT-smart-classroom

## Overview

A data collection program that gathers various data values from multiple data sources, such as retrieving room status, indoor temperature, and various IoT devices, and analyzes data from databases, creates new databases, and can control room access as needed through the IoT system.

## Member

| Member                 | Student ID  |
| ---------------------- | ----------- |
| Kittiyaporn Chanla     | 643040185-8 |
| Patharanan Papakang    | 643040207-4 |
| Phetsiri Khuntichot    | 643040762-6 |
| Weeraya Chonsaringkarn | 643040765-0 |
| Sornsiri Kothakham     | 643040766-8 |

## Services

- The system collects and stores sensor data, including temperature, humidity, motion detection in a PostgreSQL database.
- A web-based dashboard provides real-time monitoring of classroom status.
- The backend utilizes Flask API for handling requests and WebSockets for real-time communication between the ESP32 and the web application.

## Hardware Requirements

- ESP32 1 unit (for sensor data collection and communication)
- AM2301 Sensor 2 units (for temperature and humidity measurements)
- Motion Sensor 2 units (for detecting occupancy)
- USB cable 2 units
- Breadboard 1 unit

## Software Requirements

- Thonny IDE (for Python development and ESP32 programming)
- Arduino IDE 2.x
- Visual Studio Code
- The Visual Studio Code extension PlatformIO.
- The correct partition.csv file for the Arduino Nano ESP32.
- Docker (for containerized deployment)
- WebSockets (for real-time data updates)
- Flask API (for backend server)
- MQTT Broker (for message communication between devices)
- PostgreSQL(for storing sensor data)

## Installation & Setup

### Run with Docker Compose

#### Setup ESP32 board

- Connect all hardware devices in Hardware Requirements completely

- Open Thonny; if you don't have it yet, install it from (https://thonny.org)

- Open the mqtt.py file and check that the GPIO Pin matches the devices on the board

- Open Tools -> Options... -> Interpreter <br> Select the kind of interpreter as MicroPython (ESP32) <br> And select the Port where you connected your board to your computer

- Press the Run button or F5.

#### Run the web application

Verify that Docker Compose is installed correctly by checking the version
(https://github.com/docker/compose/releases)

Clone repository

```bash
git clone https://github.com/wnrsyy/IoT-smart-classroom.git
```

Linux

```bash
docker compose up
```

Windows

```powershell
docker-compose up
```

If your have any problem when docker build

```bash
docker compose up --build
```

Check your task or application

```bash
docker compose ps
```

Tear down your application

```bash
docker compose down
```

### Run each of services on localhost

#### Run Front-end and Back-end

```bash
python app.py
```

#### MQTT to connect MQTT broker

```bash
mosquitto -c “<address of mosquitto/config/mosquitto.conf path>” -v
```
