from fastapi import FastAPI
import uvicorn
from datetime import datetime, timezone
from tle_tracker.mqtt_interface import MQTT_Interface

app = FastAPI()
app_state  = {
    "status": None
}
mqtt_interface = MQTT_Interface()

@app.get("/")
def read_root():
    now = datetime.now(timezone.utc)
    return {"Hello": "World","now":f"{now}"}

@app.get("/status")
def read_status():
    return app_state

@app.put("/status")
def set_status(status: str):
    app_state["status"] = status
    return app_state

@app.get("/mqtt")
def get_mgqtt(topic: str):
    return mqtt_interface.get_message(topic)

@app.put("/mqtt")
def send_mgqtt_message(topic: str, msg: bytes):
    return mqtt_interface.send_message(topic,msg)

if __name__ == "__main__":
    uvicorn.run(
        "tle_tracker.app:app",
        host="0.0.0.0",
        port=8765,
        log_level="debug",
        reload=True,
    )