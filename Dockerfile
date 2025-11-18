# Multi-stage Dockerfile for Luno Trading Bot
# Builds a production image that can run both the Flask dashboard and background worker via Procfile

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Procfile runner (for multi-process support)
RUN pip install --no-cache-dir honcho

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/healthz || exit 1

# Default: run via Procfile (both web and worker)
# Railway will use the explicit start command from railway.json or Procfile
CMD ["honcho", "-f", "Procfile", "start"]
