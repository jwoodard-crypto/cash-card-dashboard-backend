#!/bin/bash
# Quick setup script for Cash Card Dashboard Backend

set -e

echo "🚀 Cash Card Dashboard Backend Setup"
echo "===================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"
echo ""

# Setup .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your Snowflake credentials!"
    echo ""
    echo "Required configuration:"
    echo "  - SNOWFLAKE_ACCOUNT"
    echo "  - SNOWFLAKE_USER"
    echo "  - SNOWFLAKE_PASSWORD"
    echo "  - SNOWFLAKE_WAREHOUSE"
    echo "  - SNOWFLAKE_ROLE"
    echo ""
    read -p "Press Enter to open .env file in editor..."
    ${EDITOR:-nano} .env
else
    echo "✓ .env file already exists"
fi
echo ""

# Test connection
echo "Testing Snowflake connection..."
python3 << EOF
import os
from dotenv import load_dotenv
import snowflake.connector

load_dotenv()

try:
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        role=os.getenv('SNOWFLAKE_ROLE')
    )
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    cursor.fetchone()
    conn.close()
    print("✓ Snowflake connection successful!")
except Exception as e:
    print(f"✗ Snowflake connection failed: {e}")
    print("\nPlease check your .env configuration and try again.")
    exit(1)
EOF
echo ""

# All done
echo "===================================="
echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  python app.py"
echo ""
echo "Or with auto-reload:"
echo "  uvicorn app:app --reload"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""
