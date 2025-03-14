### postgresql

- cmd access to database
```bash
psql #connect general
sudo -u postgres psql #connect with pg user
psql -U miso -d iot_smart_classroom_db -W #connect with specific user
```

- postgresql

```bash
create database iot_smart_classroom; #create db
create user miso with encrypted password '1234'; #create user role
grant all privileges on database iot_smart_classroom to miso; #grant all privileges to user
```

- grant privileges
bash
bash

