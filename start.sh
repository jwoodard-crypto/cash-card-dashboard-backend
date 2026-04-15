#!/bin/bash
# Railway startup script

echo "🚀 Starting Cash Card Dashboard API..."
echo "Working directory: $(pwd)"
echo "Files present:"
ls -la

# Create data directory if it doesn't exist
mkdir -p data

# Check if data files exist, if not create empty ones
if [ ! -f "data/queue_volumes.json" ]; then
    echo "[]" > data/queue_volumes.json
fi

if [ ! -f "data/network_rejects.json" ]; then
    echo "[]" > data/network_rejects.json
fi

if [ ! -f "data/current_backlog.json" ]; then
    echo "{}" > data/current_backlog.json
fi

echo "✅ Data files ready"
echo "🌐 Starting Uvicorn server on port ${PORT:-8000}..."

# Start the server
uvicorn app_file_based:app --host 0.0.0.0 --port ${PORT:-8000}
