# main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from stream import VideoStream
from location import LocationStore
import cv2
import numpy as np
import time

app = FastAPI()
video_stream = VideoStream()
location_store = LocationStore()

@app.post("/upload-frame/")
async def upload_frame(file: UploadFile = File(...)):
    content = await file.read()
    video_stream.set_frame(content)
    return {"status": "frame_received"}

@app.get("/video-stream/")
def video_stream_route():
    def stream_generator():
        while True:
            frame = video_stream.get_frame()
            if frame:
                img = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    _, jpeg = cv2.imencode('.jpg', img)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.05)
    return StreamingResponse(stream_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

# ✅ POST latitude and longitude
@app.post("/location")
async def post_location(lat: float, long: float):
    location_store.set_location(lat, long)
    return {"status": "location_saved", "lat": lat, "long": long}

# ✅ GET last location
@app.get("/location")
async def get_location():
    return location_store.get_location()
