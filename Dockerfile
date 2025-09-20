# Multi-stage build for optimized image size and build speed

# Build stage
FROM python:3.9-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements/base.txt .

# Install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir -r base.txt

# Runtime stage
FROM python:3.9-slim AS runtime

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    gosu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create user with commonly available UID/GID (1000 is often the first non-root user)
RUN groupadd -g 1000 appgroup && \
    useradd --create-home --shell /bin/bash --uid 1000 --gid 1000 app \
    && mkdir -p /app/data /app/logs \
    && chown -R app:appgroup /app

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy installed packages from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=app:appgroup src/ src/

# Don't switch to non-root user here - let entrypoint handle it
# USER app

# Expose port
EXPOSE 5000

# Environment variables
ENV FLASK_APP=src/main.py

# Use entrypoint script for user handling
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Default command
CMD ["python", "src/main.py"]