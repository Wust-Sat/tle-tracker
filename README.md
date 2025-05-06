# TLE (position) tracker
This repository enable starting service using **mqtt** library to calculate position:
- latitide
- longitude
- altitude (in km)
  
To calculate posittion of a satellite client needs **TLE** (2 lines) and broker (**mosquitto**). You can always sen TLE via terminal like this:
 ```bash
mosquitto_pub -h localhost -t cubesat/tle -m "1 25544U 98067A   20029.54791435  .00001264  00000-0  29621-4 0  9993\n2 25544  51.6434  21.3435 0007417 318.0083  42.0574 15.49176870211460"
```
but remember to have running both **mosquitto_interface** and **mosquitto** broker.

If you wish to use this in your code you need to import:
```python
import paho.mqtt.client as mc
```


## Listening
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
## Getting info
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