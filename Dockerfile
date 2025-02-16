FROM python:3.9-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
EXPOSE 8080

CMD ["python", "backend/app.py", "--host", "0.0.0.0", "--port", "5000"]
