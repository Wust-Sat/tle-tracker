import datetime
import json

import pytest
from skyfield.api import load
from unittest.mock import MagicMock, call

from tle_tracker.mqtt_interface import MQTT_Interface

TLE_LINE_1 = "1 25544U 98067A   20029.54791435  .00001264  00000-0  29621-4 0  9993"
TLE_LINE_2 = "2 25544  51.6434  21.3435 0007417 318.0083  42.0574 15.49176870211460"
TLE_PAYLOAD = f"{TLE_LINE_1}\n{TLE_LINE_2}".encode("utf-8")


@pytest.fixture
def mqtt_iface_fixture(monkeypatch):
    """
    A pytest fixture to set up the test environment.
    - Mocks the paho.mqtt.client.Client class.
    - Instantiates our MQTT_Interface.
    - Yields the interface instance and the mock client instance.
    """
    mock_client_class = MagicMock()
    mock_client_instance = mock_client_class.return_value
    monkeypatch.setattr("tle_tracker.mqtt_interface.mc.Client", mock_client_class)
    iface = MQTT_Interface(broker="test-broker", port=9999)

    yield iface, mock_client_class, mock_client_instance


def test_initialization(mqtt_iface_fixture):
    """
    Test if the client is initialized and configured correctly.
    """
    mqtt_iface, mock_client_class, mock_client = mqtt_iface_fixture
    mock_client_class.assert_called_once()
    mock_client.connect.assert_called_once_with("test-broker", 9999, 60)
    assert mock_client.on_connect == mqtt_iface.on_connect
    assert mock_client.on_message == mqtt_iface.on_message


def test_on_connect_subscribes_to_topics(mqtt_iface_fixture):
    """
    Test if the on_connect callback subscribes to the correct topics.
    """
    mqtt_iface, mock_client_class, mock_client = mqtt_iface_fixture

    # Directly call the on_connect method
    mqtt_iface.on_connect(mock_client, None, None, 0)

    # Verify that subscribe was called for each topic
    expected_calls = [
        call("cubesat/tle"),
        call("cubesat/req_position"),
        call("cubesat/req_last_update"),
    ]
    mock_client.subscribe.assert_has_calls(expected_calls, any_order=True)


def test_on_message_updates_tle(mqtt_iface_fixture):
    """
    Test if a TLE message correctly updates the satellite object.
    """
    mqtt_iface, mock_client_class, mock_client = mqtt_iface_fixture

    assert mqtt_iface.satellite is None
    assert mqtt_iface.last_update is None

    # Create a mock message object
    mock_msg = MagicMock()
    mock_msg.topic = "cubesat/tle"
    mock_msg.payload = TLE_PAYLOAD

    # Simulate receiving the message
    mqtt_iface.on_message(mock_client, None, mock_msg)

    # Assert that the satellite and last_update were updated
    assert mqtt_iface.satellite is not None
    assert mqtt_iface.satellite.name == "CubeSat"
    assert mqtt_iface.last_update is not None
    assert isinstance(mqtt_iface.last_update, datetime.datetime)


def test_publish_position_without_tle(mqtt_iface_fixture):
    """
    Test that requesting a position does nothing if no TLE is set.
    """
    mqtt_iface, mock_client_class, mock_client = mqtt_iface_fixture

    # Simulate a position request
    mqtt_iface.publish_position()

    # Assert that publish was NOT called
    mock_client.publish.assert_not_called()


def test_publish_position_with_tle(mqtt_iface_fixture, monkeypatch):
    """
    Test that a position is published when requested after a TLE update.
    We patch ts.now() to get a deterministic position.
    """
    mqtt_iface, mock_client_class, mock_client = mqtt_iface_fixture

    # --- Setup a fixed time for deterministic results ---
    fixed_utc_dt = datetime.datetime(
        2025, 6, 12, 16, 12, 8, tzinfo=datetime.timezone.utc
    )
    ts = load.timescale()
    fixed_skyfield_time = ts.from_datetime(fixed_utc_dt)

    # Patch the 'now' method on the *instance* of the timescale object
    monkeypatch.setattr(mqtt_iface.ts, "now", lambda: fixed_skyfield_time)
    # --- End time setup ---

    # 1. Update TLE
    mqtt_iface.update_tle(TLE_LINE_1, TLE_LINE_2)

    # 2. Request position
    mqtt_iface.publish_position()

    # 3. Assert that publish was called with the correct data
    mock_client.publish.assert_called_once()
    topic_arg, payload_arg = mock_client.publish.call_args[0]

    assert topic_arg == "cubesat/position"

    # The exact position depends on the TLE and the fixed time
    expected_pos = {
        "timestamp": "2025-06-12T16:12:08Z",
        "latitude": 50.094139815985834,
        "longitude": -87.08561990743935,
        "altitude_km": 404.43169426280593,
    }
    # Load the JSON from the payload to compare it as a dictionary
    assert json.loads(payload_arg) == expected_pos


def test_publish_last_update(mqtt_iface_fixture, monkeypatch):
    """
    Test publishing the last TLE update timestamp.
    """
    mqtt_iface, mock_client_class, mock_client = mqtt_iface_fixture

    # Set a fixed time for the update
    fixed_now = datetime.datetime(
        2025, 1, 1, 12, 0, 0, tzinfo=datetime.UTC
    )

    # Mock datetime.datetime.now() to return our fixed time
    mock_dt = MagicMock()
    mock_dt.now.return_value = fixed_now
    mock_dt.UTC = datetime.UTC
    monkeypatch.setattr("datetime.datetime", mock_dt)

    # 1. Update TLE to set the last_update timestamp
    mqtt_iface.update_tle(TLE_LINE_1, TLE_LINE_2)

    # 2. Request the last update time
    mqtt_iface.publish_last_update()

    # 3. Assert that publish was called with the correct ISO formatted time
    mock_client.publish.assert_called_once_with(
        "cubesat/last_update", fixed_now.isoformat()
    )


def test_publish_last_update_without_tle(mqtt_iface_fixture):
    """
    Test that requesting last_update does nothing if no TLE is set.
    """
    mqtt_iface, mock_client_class, mock_client = mqtt_iface_fixture

    mqtt_iface.publish_last_update()
    mock_client.publish.assert_not_called()
