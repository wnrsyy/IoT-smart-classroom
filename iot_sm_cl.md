### postgresql
- install postgresql

<br>Option 1: Using Default APT Repository
```bash
apt install postgresql
```
<br> Option 2: Manually configure the Apt repository
```bash
sudo apt install curl ca-certificates
sudo install -d /usr/share/postgresql-common/pgdg
sudo curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc
sudo sh -c 'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
sudo apt update
sudo apt -y install postgresql
```
- cmd access to database
```bash
psql #connect general
sudo -u postgres psql #connect with pg user 
psql -U miso -d iot_smart_classroom_db -W #Connects to the iot_smart_classroom_db database as user miso on a Linux machine (it's running locally).
psql -U miso -d iot_smart_classroom_db -h 10.161.112.160 -W #Connects to the iot_smart_classroom_db database as user miso from a PC (or another machine).
```
- postgresql
```bash
create database iot_smart_classroom; #create db
create user miso with encrypted password '1234'; #create user role
grant all privileges on database iot_smart_classroom to miso; #grant all privileges to user
```
- grant privileges
```bash
```
- Define and create a table named smartclass_db in a database.
```bash 
CREATE TABLE smartclass_db (
    id INT SERIAL PRIMARY KEY,
    temp_in_c FLOAT NOT NULL,
    temp_in_f FLOAT NOT NULL,
    humi_in FLOAT NOT NULL,
    temp_out_c FLOAT NOT NULL,
    temp_out_f FLOAT NOT NULL,
    humi_out FLOAT NOT NULL,
    motion_front BOOLEAN NOT NULL,
    motion_back BOOLEAN NOT NULL,
    people_count INT NOT NULL DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
