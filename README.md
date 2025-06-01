# TLE (position) tracker

TLE service for WUST-Sat OBC.

### Tests and linter

This project enforces code quality using listed tools:

`black` - code formatter that ensures consistent style across the project  
`isort` - organizes import statements into sections and alphabetically  
`ruff` - linter for code quality checks and automatic fixes  

You can test quality of code using `poe` command:

`poe format` will automatically correct formatting, import order, and check if
ruff returns errors.  
`poe format_check` will run checkers and linters, but without editing the code.  

## TLE Tracker on Raspberry Pi

To deploy and run the `TLE_tracker` service on a Raspberry Pi, use the dedicated Ansible playbook:

**Playbook:** [`tle-tracker.yml`](https://github.com/Wust-Sat/obc-system/tree/master/playbooks)

**Repository:** [`Wust-Sat/obc-system`](https://github.com/Wust-Sat/obc-system)


## Dependecies

Please install `mosquitto` or provide different MQTT server.


## Features
This repository enable starting service using **mqtt** library to calculate position of satellite:
- time of the request
- latitide
- longitude
- altitude (in km)
  
To calculate posittion of a satellite client needs **TLE** (2 lines) and broker (**mosquitto**). You can always send TLE via terminal like this:
 ```bash
mosquitto_pub -h localhost -t cubesat/tle -m "1 25544U 98067A   20029.54791435  .00001264  00000-0  29621-4 0  9993\n2 25544  51.6434  21.3435 0007417 318.0083  42.0574 15.49176870211460"
```
but remember to have running both **mosquitto_interface** and **mosquitto** broker.

If you wish to use this in your code you need to import:
```python
import paho.mqtt.client as mc
```

## Operating the Library via Shell Commands

`TLE_tracker` primarily uses files located in the **/var/lib/tle** folder. It monitors the most recent file in this directory and extracts TLE lines from it when available. 

If the folder does not exist, a warning message will be displayed during `tle_tracker` runtime. In that case, updating TLE lines is only possible through MQTT topics.

```bash
mosquitto_pub -h localhost -t cubesat/tle -m "1 25544U 98067A   20029.54791435  .00001264  00000-0  29621-4 0  9993\n2 25544  51.6434  21.3435 0007417 318.0083  42.0574 15.49176870211460"
mosquitto_sub -h localhost -t cubesat/req_position -m ""
mosquitto_sub -h localhost -t cubesat/req_last_update -m ""
```


## Listening inside your program
In order to get position or time of last update you need:
```python
def __init__(self, broker="localhost", port=1883):
    self.client = mc.Client()
    self.client.on_connect = self.on_connect
    self.client.on_message = self.on_message
```
where:
```python
def on_connect(self, client,userdata,flags,rc):
        client.subscribe("cubesat/position")
        client.subscribe("cubesat/last_update")
```
and:
```python
def on_message(self, client, userdata, msg):
        print(f"{msg.topic}: {msg.payload.decode()}")
        if msg.topic == "cubesat/position":
            func_for_what_to_do()
        elif msg.topic == "cubesat/last_update":
            func_for_what_to_do2()
```
## Requesting info inside program
In order to make request for position info:
```python
    def get_pos_info():
        self.client.publish("cubesat/req_position","")
```
In order to make request for last_update time:
```python
    def get_update_time_info():
        self.client.publish("cubesat/req_last_update","")
```
