# ---- Stage 1: Builder ----
# We install dependencies in a separate stage so the final image is smaller
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy only requirements first (Docker layer caching — if requirements don't change,
# this layer is reused on subsequent builds, making builds faster)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: Final image ----
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY main.py .

# Non-root user for security (running as root in a container is a bad practice)
RUN useradd -m appuser
USER appuser

# Document the port (doesn't actually publish it — that's done at runtime)
EXPOSE 8000

# Start the API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]