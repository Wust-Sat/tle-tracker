from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

TLE_FOLDER_PATH = "/var/lib/tle"


class TLEFileHandler(FileSystemEventHandler):
    def __init__(self, mqtt_iface, folder_path):
        self.mqtt_iface = mqtt_iface
        self.folder_path = Path(folder_path)

    def on_any_event(self, event):
        if event.is_directory:
            return
        if event.event_type in ("created", "modified"):
            latest_file = self.get_latest_file()
            if latest_file:
                with open(latest_file, "r") as f:
                    lines = f.read().strip().split("\n")
                    if len(lines) >= 2:
                        print(
                            f"Detected change in {latest_file}, updating"
                            " TLE..."
                        )
                        self.mqtt_iface.update_tle(lines[0], lines[1])

    def get_latest_file(self):
        files = list(self.folder_path.glob("*"))
        if not files:
            return None
        latest = max(files, key=lambda f: f.stat().st_mtime)
        return latest


class TLEFileWatcher:
    def __init__(self, mqtt_iface, folder_path=TLE_FOLDER_PATH):
        self.folder_path = Path(folder_path)
        self.folder_exists = self.folder_path.exists()
        self.event_handler = TLEFileHandler(mqtt_iface, folder_path)
        self.observer = Observer()

        if self.folder_exists:
            self.observer.schedule(
                self.event_handler, path=folder_path, recursive=False
            )
        else:
            print(
                f"[WARNING] Folder '{folder_path}' does not exist. "
                "TLE watcher will not start."
            )

    def start(self):
        if not self.folder_exists:
            return

        latest = self.event_handler.get_latest_file()
        if latest:
            with open(latest, "r") as f:
                lines = f.read().strip().split("\n")
                if len(lines) >= 2:
                    print(f"Startup update from {latest}")
                    self.event_handler.mqtt_iface.update_tle(
                        lines[0], lines[1]
                    )
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
