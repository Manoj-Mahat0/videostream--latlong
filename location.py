# location.py

import threading

class LocationStore:
    def __init__(self):
        self.location = {"lat": None, "long": None}
        self.lock = threading.Lock()

    def set_location(self, lat: float, long: float):
        with self.lock:
            self.location = {"lat": lat, "long": long}

    def get_location(self):
        with self.lock:
            return self.location
