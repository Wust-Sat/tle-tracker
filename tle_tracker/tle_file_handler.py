import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import os

TLE_FILE_PATH = "/home/ubuntu/tle.txt"

class TLEFileHandler(FileSystemEventHandler):
    def __init__(self, mqtt_iface):
        self.mqtt_iface = mqtt_iface

    def on_modified(self, event):
        if event.src_path == TLE_FILE_PATH:
            with open(TLE_FILE_PATH, "r") as f:
                lines = f.read().strip().split("\n")
                if len(lines) >= 2:
                    print("Detected TLE file change, updating...")
                    self.mqtt_iface.update_tle(lines[0], lines[1])

class TLEFileWatcher:
    def __init__(self, mqtt_iface):
        self.event_handler = TLEFileHandler(mqtt_iface)
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            path=os.path.dirname(TLE_FILE_PATH),
            recursive=False
        )

    def start(self):
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
