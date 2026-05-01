#!/bin/bash

# Talash Backend Startup Script for Linux/macOS

echo ""
echo "===================================="
echo "  Talash CV Processing Backend"
echo "===================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Activating virtual environment..."
    source myvenv/bin/activate
fi

echo ""
echo "Starting FastAPI server..."
echo "Server will be available at: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""

cd talash
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
