from sanic import Sanic, HTTPResponse
from sanic.response import empty, html, file
import cv2
import os
import asyncio
from ultralytics import YOLO

app = Sanic("VideoStreamingApp")

app.static("/", "frontend")

frame_buffer = None
buffer_lock = asyncio.Lock()

model = YOLO(os.path.join(os.path.dirname(__file__), "files", "best.pt"))

FPS = 10


def predict(
    file_,
    show_=False,
    imgsz_=1280,
    show_labels_=False,
    save_=False,
    name_="predicted",
    conf_=0.2,
):
    pre = model.predict(
        device=0,
        source=file_,
        show=show_,
        imgsz=imgsz_,
        show_labels=show_labels_,
        show_boxes=True,
        save=save_,
        name=name_,
        conf=conf_,
        verbose=False,
    )
    return pre


async def read_frames():
    global frame_buffer
    cap = cv2.VideoCapture(2)
    if not cap.isOpened():
        raise RuntimeError("Не удалось открыть камеру!")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Ошибка: Не удалось захватить кадр.")
                break

            pred = predict(frame, show_=False, imgsz_=736, show_labels_=True)
            annotated_frame = pred[0].plot()
            _, buffer = cv2.imencode(".jpg", annotated_frame)

            async with buffer_lock:
                frame_buffer = buffer.tobytes()

            await asyncio.sleep(1 / FPS)
    finally:
        cap.release()


async def generate_frames():
    global frame_buffer
    while True:
        await asyncio.sleep(1 / FPS)
        async with buffer_lock:
            if frame_buffer:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_buffer + b"\r\n"
                )


@app.get("/")
async def home(request):
    return await file("frontend/index.html")


@app.get("/video_feed")
async def video_feed(request):
    response = await request.respond(
        headers={"Content-Type": "multipart/x-mixed-replace; boundary=frame"}
    )
    async for frame in generate_frames():
        await response.send(frame)
    return empty()


@app.before_server_start
async def setup_background_task(app, loop):
    app.add_task(read_frames())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
