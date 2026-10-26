FROM python:3.10-slim

WORKDIR /app

# Menjalankan container dengan non-root user demi keamanan runtime
RUN useradd -m appuser

COPY requirements.txt .

# PAKSA upgrade paket-paket sistem bawaan image yang rentan (Bypass Cache)
RUN pip install --no-cache-dir --upgrade pip setuptools==78.1.1 wheel==0.46.2 jaraco.context==6.1.0 msgpack==1.2.1 urllib3==2.8.0

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["python", "app.py"]