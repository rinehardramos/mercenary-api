FROM python:3.12-alpine

ARG BUILD_VERSION=2026-03-28-v3
RUN echo "=== BUILD VERSION: ${BUILD_VERSION} ==="

WORKDIR /app

RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8001

EXPOSE 8001

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}
