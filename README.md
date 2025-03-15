# IoT-smart-classroom
Overview
A data collection program that gathers various data values from multiple data sources, such as retrieving room status, indoor temperature, and various IoT devices, and analyzes data from databases, creates new databases, and can control room access as needed through the IoT system.

Member
643040185-8	นางสาวกิตติยาภรณ์ จันทร์หล้า 
643040207-4	นางสาวภัทรนันท์ ปาปะขัง
643040762-6	นางสาวเพชรศิริ ขันติโชติ
643040765-0	นางสาววีรยา ชลศฤงคาร
643040766-8	นางสาวศรศิริ โคตะคาม

Services
- The system collects and stores sensor data, including temperature, humidity, motion detection in a PostgreSQL database.
- A web-based dashboard provides real-time monitoring of classroom status.
- The backend utilizes Flask API for handling requests and WebSockets for real-time communication between the ESP32 and the web application.

Hardware Requirements
- ESP32 1 unit (for sensor data collection and communication)
- AM2301 Sensor 2 units (for temperature and humidity measurements)
- Motion Sensor 2 units (for detecting occupancy)
- USB cable

Software Requirements
- Thonny IDE (for Python development and ESP32 programming)
- Docker (for containerized deployment)
- WebSockets (for real-time data updates)
- Flask API (for backend server)
- MQTT Broker (for message communication between devices)
- PostgreSQL(for storing sensor data)

Installation & Setup
