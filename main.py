# main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from stream import VideoStream
from location import LocationStore
import cv2
import numpy as np
import time
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

app = FastAPI()
video_stream = VideoStream()
location_store = LocationStore()

class SimpleLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        return response

app.add_middleware(SimpleLoggerMiddleware)

# Optionally, add CORS middleware if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload-frame/")
async def upload_frame(file: UploadFile = File(...)):
    content = await file.read()
    video_stream.set_frame(content)
    return {"status": "frame_received"}


@app.get("/video-stream/")
async def video_stream_route():
    async def stream_generator():
        while True:
            frame = video_stream.get_frame()
            if frame:
                img = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    # Draw a cross at the center of the frame
                    h, w = img.shape[:2]
                    center = (w // 2, h // 2)
                    color = (0, 0, 255)  # Red color in BGR
                    thickness = 2
                    length = min(w, h) // 10  # Length of cross arms

                    # Draw horizontal line
                    cv2.line(img, (center[0] - length, center[1]), (center[0] + length, center[1]), color, thickness)
                    # Draw vertical line
                    cv2.line(img, (center[0], center[1] - length), (center[0], center[1] + length), color, thickness)

                    _, jpeg = cv2.imencode('.jpg', img)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            await asyncio.sleep(0.01)  # Small delay for smoother streaming
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
