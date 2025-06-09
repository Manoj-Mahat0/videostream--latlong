import threading
import cv2
import numpy as np

class VideoStream:
    def __init__(self):
        # Create a default black image (e.g., 320x240)
        blank = np.zeros((240, 320, 3), dtype=np.uint8)
        _, jpeg = cv2.imencode('.jpg', blank)
        self.frame = jpeg.tobytes()
        self.lock = threading.Lock()

    def set_frame(self, frame_data: bytes):
        with self.lock:
            self.frame = frame_data

    def get_frame(self):
        with self.lock:
            return self.frame
