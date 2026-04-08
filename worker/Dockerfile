# ---- Stage 1: Builder ----
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: Final image ----
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY main.py .

RUN useradd -m appuser
USER appuser

# Worker has no exposed port — it doesn't serve HTTP traffic
CMD ["python", "main.py"]