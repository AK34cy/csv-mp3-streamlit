FROM python:3.11-slim

WORKDIR /app

# Установим ffmpeg (нужен для pydub)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]
