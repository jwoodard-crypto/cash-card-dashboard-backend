FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app_file_based.py .

# Copy data directory with initial JSON files
COPY data/ ./data/

# Ensure data files exist (Railway will use these as fallback)
RUN mkdir -p data && \
    test -f data/queue_volumes.json || echo "[]" > data/queue_volumes.json && \
    test -f data/network_rejects.json || echo "[]" > data/network_rejects.json && \
    test -f data/current_backlog.json || echo "{}" > data/current_backlog.json

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run application - Railway sets PORT env var
CMD uvicorn app_file_based:app --host 0.0.0.0 --port ${PORT:-8000}
# Force rebuild Wed Apr 15 14:35:43 CDT 2026
