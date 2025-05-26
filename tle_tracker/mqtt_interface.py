import datetime
import threading

import paho.mqtt.client as mc
from skyfield.api import EarthSatellite, load

from tle_tracker.data import Position
from tle_tracker.tle_file_handler import TLEFileWatcher


# for tests:
# mosquitto_pub -h localhost -t cubesat/tle -m "1 25544U 98067A   20029.54791435  .00001264  00000-0  29621-4 0  9993\n2 25544  51.6434  21.3435 0007417 318.0083  42.0574 15.49176870211460"
class MQTT_Interface:
    def __init__(self, broker="localhost", port=1883):
        self.client = mc.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(broker, port, 60)
        self.ts = load.timescale()
        self.satellite = None
        self.last_update = None

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("cubesat/tle")
        client.subscribe("cubesat/req_position")
        client.subscribe("cubesat/req_last_update")

    def on_message(self, client, userdata, msg):
        print(f"{msg.topic}: {msg.payload.decode()}")
        if msg.topic == "cubesat/tle":
            tle_string = msg.payload.decode().strip().replace("\\n", "\n")
            tle_data = tle_string.split("\n")
            if len(tle_data) >= 2:
                self.update_tle(tle_data[0], tle_data[1])
        elif msg.topic == "cubesat/req_position":
            self.publish_position()
        elif msg.topic == "cubesat/req_last_update":
            self.publish_last_update()

    def update_tle(self, line1, line2):
        print("Updating TLE...")
        self.last_update = datetime.datetime.now(datetime.UTC)
        self.satellite = EarthSatellite(line1, line2, "CubeSat", self.ts)
        print(self.last_update.isoformat())

    def get_position(self) -> None | Position:
        if not self.satellite:
            return None
        t = self.ts.now()
        geocentric = self.satellite.at(t)
        subpoint = geocentric.subpoint()
        result = Position(
            timestamp=t.utc_datetime(),
            latitude=subpoint.latitude.degrees,
            longitude=subpoint.longitude.degrees,
            altitude_km=subpoint.elevation.km,
        )
        return result

    def publish_position(self):
        pos: Position | None = self.get_position()
        if pos:
            msg = f"{pos.model_dump_json()}"
            self.client.publish("cubesat/position", msg)
            print(f"Published position: {msg}")
        else:
            print("No TLE data available")

    def publish_last_update(self):
        if self.last_update:
            msg = self.last_update.isoformat()
            self.client.publish("cubesat/last_update", msg)
            print(f"Published last_update: {msg}")
        else:
            print("Havent got any tle yet")

    def loop(self):
        self.client.loop_forever()


if __name__ == "__main__":
    mqtt_iface = MQTT_Interface()

    watcher = TLEFileWatcher(mqtt_iface)
    threading.Thread(target=watcher.start, daemon=True).start()

    mqtt_iface.loop()
