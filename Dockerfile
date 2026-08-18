# --- Stage 1: Build ---
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for Cython compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy all source code first (pip needs the package source to build the wheel)
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir .

# Build Cython extensions
RUN python setup_cython.py build_ext --inplace

# --- Stage 2: Production ---
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (with compiled Cython extensions)
COPY --from=builder /app .

# Expose port for API and Dashboard (8000)
EXPOSE 8000

# Default command (overridden by docker-compose)
CMD ["python", "-m", "oure.cli.main", "--help"]
