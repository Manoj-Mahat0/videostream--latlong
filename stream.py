import threading

class VideoStream:
    def __init__(self):
        self.frame = None
        self.lock = threading.Lock()

    def set_frame(self, frame_data: bytes):
        with self.lock:
            self.frame = frame_data

    def get_frame(self):
        with self.lock:
            return self.frame
