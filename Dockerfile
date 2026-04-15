FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app_file_based.py .
COPY .env* ./
COPY data/ ./data/

# Create data directory if it doesn't exist
RUN mkdir -p data && \
    echo "[]" > data/queue_volumes.json && \
    echo "[]" > data/network_rejects.json && \
    echo "{}" > data/current_backlog.json

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app_file_based:app", "--host", "0.0.0.0", "--port", "8000"]
