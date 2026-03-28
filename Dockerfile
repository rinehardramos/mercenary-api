FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ARG CACHE_BUST=default
RUN echo "Build timestamp: $(date)" > /tmp/build_info
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN ls -la /app/app/api/ && head -20 /app/app/api/auth.py

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8001

EXPOSE 8001

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}
