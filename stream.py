from pathlib import Path

class VideoStream:
    def __init__(self):
        self.frame = Path("placeholder.jpg").read_bytes()  # fallback image
        self.lock = threading.Lock()

    def set_frame(self, frame_data: bytes):
        with self.lock:
            self.frame = frame_data

    def get_frame(self):
        with self.lock:
            return self.frame
