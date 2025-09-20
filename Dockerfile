# Multi-stage build for optimized image size and build speed

# Build stage
FROM python:3.9-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements/base.txt .

# Install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r base.txt

# Download the model during build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Runtime stage
FROM python:3.9-slim AS runtime

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/data /app/logs \
    && chown -R app:app /app

# Copy installed packages from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy model cache from builder stage
COPY --from=builder /root/.cache /home/app/.cache

# Set ownership of cache
RUN chown -R app:app /home/app/.cache

# Set cache directories for the app user
ENV TORCH_HOME=/home/app/.cache/torch
ENV HF_HOME=/home/app/.cache/huggingface

# Copy application code
COPY --chown=app:app src/ src/

# Switch to non-root user
USER app

# Expose port
EXPOSE 5000

# Environment variables
ENV FLASK_APP=src/main.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Run the application
CMD ["python", "src/main.py"]