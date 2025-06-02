import time
import json
import pytest
import datetime
import paho.mqtt.client as mqtt
from tle_tracker.data import Position 

TLE_LINE_1 = "1 25544U 98067A   20029.54791435  .00001264  00000-0  29621-4 0  9993"
TLE_LINE_2 = "2 25544  51.6434  21.3435 0007417 318.0083  42.0574 15.49176870211460"

POSITION_TOPIC = "cubesat/req_position"
PUBLISH_TOPIC = "cubesat/tle"

received_positions = []

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        obj = json.loads(payload)
        position = Position(**obj)
        received_positions.append(position)
    except Exception as e:
        pytest.fail(f"Invalid message or JSON: {e}")

@pytest.mark.timeout(10)
def test_position_updates_change_over_time():
    client = mqtt.Client()
    client.on_message = on_message

    client.connect("localhost", 1883)
    client.loop_start()

    client.subscribe(POSITION_TOPIC)

    # Publikuj TLE
    tle_data = f"{TLE_LINE_1}\n{TLE_LINE_2}"
    client.publish(PUBLISH_TOPIC, tle_data)
    time.sleep(1)

    # Zapytaj pierwszy raz o pozycję
    client.publish(POSITION_TOPIC, "")
    time.sleep(1)

    # Zapytaj drugi raz po chwili
    client.publish(POSITION_TOPIC, "")
    time.sleep(1)

    client.loop_stop()
    client.disconnect()

    assert len(received_positions) >= 2, "Expected at least 2 position messages"

    first, second = received_positions[:2]
    assert first.timestamp != second.timestamp or first.latitude != second.latitude, \
        "Expected different positions/timestamps in responses"
