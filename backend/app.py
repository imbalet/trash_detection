from sanic import Sanic
from sanic.response import empty, file, json as s_json
import cv2
import os
import asyncio
import torch.version
from ultralytics import YOLO
import sqlite3
from sanic.worker.manager import WorkerManager
from sanic_cors import CORS
from datetime import datetime, timedelta
from sanic.log import logger
import torch

WorkerManager.THRESHOLD = 600
FPS = 10
TIMEOUT = 0.5  # in minutes
CAMERA_ID = int(os.environ.get("CAMERA_ID", 0))
DEVICE = "0" if torch.cuda.is_available() else "cpu"


app = Sanic("VideoStreamingApp")

logger.info(
    f"device = {DEVICE}, cuda = {torch.version.cuda}, torch = {torch.__version__}, cuda_aval = {torch.cuda.is_available()}"
)

app.static("/", "frontend")

CORS(
    app,
    resources={r"/trash_data/*": {"origins": "*"}},
    automatic_options=True,
    supports_credentials=False,
    allow_headers=["Content-Type", "Authorization"],
)

frame_buffer = None
buffer_lock = asyncio.Lock()
trash_amount = 0

model = YOLO(os.path.join(os.path.dirname(__file__), "files", "best.pt"))


conn = sqlite3.connect(
    os.path.join(os.path.dirname(__file__), "database", "trash_data.db"),
    check_same_thread=False,
)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS trash_records (
        stamp TIMESTAMP,
        trash_amount INTEGER
    )
    """
)
conn.commit()


def insert_data(trash_amount):
    cursor.execute(
        """
        INSERT INTO trash_records (stamp, trash_amount)
        VALUES (?, ?)
        """,
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), trash_amount),
    )
    conn.commit()


def predict(
    file_,
    device_="cpu",
    show_=False,
    imgsz_=1280,
    show_labels_=False,
    save_=False,
    name_="predicted",
    conf_=0.2,
    show_boxes_=True,
    verbose_=False,
):
    pre = model.predict(
        device=device_,
        source=file_,
        show=show_,
        imgsz=imgsz_,
        show_labels=show_labels_,
        show_boxes=show_boxes_,
        save=save_,
        name=name_,
        conf=conf_,
        verbose=verbose_,
    )
    return pre


async def read_frames():
    global frame_buffer, trash_amount
    print(CAMERA_ID)
    cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_V4L2)
    if not cap.isOpened():
        raise RuntimeError("Не удалось открыть камеру!")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Ошибка: Не удалось захватить кадр.")
                break

            pred = predict(
                frame, show_=False, imgsz_=736, show_labels_=False, device_=DEVICE
            )
            trash_amount = len(pred[0].boxes)
            annotated_frame = pred[0].plot()

            _, buffer = cv2.imencode(".jpg", annotated_frame)

            async with buffer_lock:
                frame_buffer = buffer.tobytes()

            await asyncio.sleep(1 / FPS)
    finally:
        cap.release()


async def record_to_db():
    global trash_amount
    while True:
        insert_data(trash_amount)
        print(f"[INFO] Записано в базу: trash_amount={trash_amount}")
        await asyncio.sleep(TIMEOUT * 60)


async def generate_frames():
    global frame_buffer
    while True:
        await asyncio.sleep(1 / FPS)
        async with buffer_lock:
            if frame_buffer:
                yield (
                    b"--frame\r\n"
                    b"Contoent-Type: image/jpeg\r\n\r\n" + frame_buffer + b"\r\n"
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


@app.get("/trash_data")
async def get_trash_data(request):
    timeframe = request.args.get("timeframe", "15m")

    if timeframe == "5m":
        timeframe_minutes = 5
    elif timeframe == "15m":
        timeframe_minutes = 15
    elif timeframe == "30m":
        timeframe_minutes = 30
    elif timeframe == "1h":
        timeframe_minutes = 60
    else:
        timeframe_minutes = 1440

    # match timeframe:
    #     case "5m":
    #         timeframe_minutes = 5
    #     case "15m":
    #         timeframe_minutes = 15
    #     case "30m":
    #         timeframe_minutes = 30
    #     case "1h":
    #         timeframe_minutes = 60
    #     case "1d":
    #         timeframe_minutes = 1440

    start_time = datetime.now() - timedelta(minutes=timeframe_minutes)
    end_time = datetime.now()
    rows = []

    for i in range(15):
        q = """
            SELECT MIN(stamp), AVG(trash_amount)
            FROM trash_records
            WHERE stamp BETWEEN ? AND ?;
            """
        cursor.execute(q, (start_time, end_time))
        results = cursor.fetchall()
        # print(results)
        if results[0][0] is None or results[0][1] is None:
            break
        rows.append(results)
        start_time -= timedelta(minutes=timeframe_minutes)
        end_time -= timedelta(minutes=timeframe_minutes)

    result = [{"time": row[0][0], "trash": round(row[0][1])} for row in rows][::-1]

    print(result)
    return s_json(result)


@app.before_server_start
async def setup_background_task(app, loop):
    app.add_task(read_frames())
    app.add_task(record_to_db())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
