FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/app/api

COPY app/api/auth.py /app/app/api/auth.py
COPY app/main.py /app/app/main.py
COPY app/config.py /app/app/config.py
COPY app/db/ /app/app/db/
COPY app/services/ /app/app/services/
COPY app/models/ /app/app/models/

RUN echo "=== Checking deployed files ===" && \
    ls -la /app/app/api/ && \
    echo "=== First 5 lines of auth.py ===" && \
    head -5 /app/app/api/auth.py && \
    echo "=== Line count of auth.py ===" && \
    wc -l /app/app/api/auth.py && \
    echo "=== Checking for /auth/session endpoint ===" && \
    grep -n "auth/session" /app/app/api/auth.py

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8001

EXPOSE 8001

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}
