FROM python:3.9-slim
WORKDIR /app

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ /app/
COPY frontend/ /app/
EXPOSE 8080

CMD ["python", "backend/app.py", "--host", "0.0.0.0", "--port", "5000"]
