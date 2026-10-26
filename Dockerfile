FROM python:3.10-slim

WORKDIR /app

# Menjalankan container dengan non-root user demi keamanan runtime
RUN useradd -m appuser

COPY requirements.txt .

# Update pip dan setuptools untuk menambal kerentanan bawaan (vendor)
RUN pip install --no-cache-dir --upgrade pip setuptools

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["python", "app.py"]