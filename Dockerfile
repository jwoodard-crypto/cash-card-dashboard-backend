FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app_file_based.py .
COPY start.sh .
RUN chmod +x start.sh

# Copy data directory with initial JSON files
COPY data/ ./data/

# Ensure data files exist (Railway will use these as fallback)
RUN mkdir -p data && \
    test -f data/queue_volumes.json || echo "[]" > data/queue_volumes.json && \
    test -f data/network_rejects.json || echo "[]" > data/network_rejects.json && \
    test -f data/current_backlog.json || echo "{}" > data/current_backlog.json

# Expose port (Railway will set PORT env var)
EXPOSE ${PORT:-8000}

# Run application
CMD ["./start.sh"]
