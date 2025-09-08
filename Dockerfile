FROM python:3.9-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

# Copy the application
COPY src/ src/
COPY config/ config/
COPY data/ data/
COPY logs/ logs/

# Create directories if they don't exist
RUN mkdir -p data logs

# Expose the port
EXPOSE 5000

# Environment variables
ENV FLASK_APP=src/main.py

# Run the application
CMD ["python", "src/main.py"]