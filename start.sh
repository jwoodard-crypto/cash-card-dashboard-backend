#!/bin/bash
set -e

echo "Starting Cash Card Dashboard Backend..."
echo "PORT: ${PORT:-8000}"
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "Files in directory:"
ls -la

# Start uvicorn
exec uvicorn app_file_based:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
