from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from stream import VideoStream
from location import LocationStore
from fastapi.responses import Response


import os
import cv2
import numpy as np
import asyncio
from datetime import datetime

# Initialize
app = FastAPI()
video_stream = VideoStream()
location_store = LocationStore()

# Directory for saving frames
SAVE_DIR = "saved_frames"
os.makedirs(SAVE_DIR, exist_ok=True)

# === Middlewares ===
class SimpleLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"?? Request: {request.method} {request.url}")
        return await call_next(request)

app.add_middleware(SimpleLoggerMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Upload Endpoint ===
@app.post("/upload-frame/")
async def upload_frame(file: UploadFile = File(...)):
    content = await file.read()
    video_stream.set_frame(content)

    # Save image to disk
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
    filename = f"{SAVE_DIR}/frame_{timestamp}.jpg"
    with open(filename, "wb") as f:
        f.write(content)

    print(f"? Frame saved: {filename}")
    return {"status": "frame_received", "saved_as": filename}

# === MJPEG Streaming ===
@app.get("/video-stream/")
async def video_stream_route():
    async def stream_generator():
        while True:
            frame = video_stream.get_frame()
            if frame:
                img = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    h, w = img.shape[:2]
                    center = (w // 2, h // 2)
                    color = (0, 0, 255)
                    thickness = 2
                    length = min(w, h) // 10
                    cv2.line(img, (center[0] - length, center[1]), (center[0] + length, center[1]), color, thickness)
                    cv2.line(img, (center[0], center[1] - length), (center[0], center[1] + length), color, thickness)

                    success, jpeg = cv2.imencode('.jpg', img)
                    if success:
                        yield (
                            b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' +
                            jpeg.tobytes() +
                            b'\r\n'
                        )
            await asyncio.sleep(0.03)  # 30 FPS
    return StreamingResponse(stream_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

# === WebSocket Live Frame ===
@app.websocket("/ws/video")
async def websocket_video(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            frame = video_stream.get_frame()
            if frame:
                await websocket.send_bytes(frame)
            await asyncio.sleep(0.03)
    except WebSocketDisconnect:
        print("? WebSocket disconnected")

@app.get("/latest-image/")
async def latest_image():
    frame = video_stream.get_frame()
    if frame:
        return Response(content=frame, media_type="image/jpeg")
    return {"error": "No image available"}

# === Location API ===
@app.post("/location")
async def post_location(lat: float, long: float):
    location_store.set_location(lat, long)
    return {"status": "location_saved", "lat": lat, "long": long}

@app.get("/location")
async def get_location():
    return location_store.get_location()
