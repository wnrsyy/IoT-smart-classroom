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
    id SERIAL PRIMARY KEY,
    temp_in_c DOUBLE PRECISION NOT NULL,
    temp_out_c DOUBLE PRECISION NOT NULL,
    humi_in DOUBLE PRECISION NOT NULL,
    humi_out DOUBLE PRECISION NOT NULL,
    people_count INTEGER NOT NULL DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    temp_in_f DOUBLE PRECISION NOT NULL,
    temp_out_f DOUBLE PRECISION NOT NULL,
```
