#!/bin/bash

# BLE Backend Startup Script

echo "========================================"
echo "  BLE Device Control Backend"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Starting BLE Backend on port 5000..."
echo "   API: http://localhost:5000"
echo "   Frontend: http://localhost:5000"
echo ""
echo "🔍 Searching for BLE devices with 'wear' in name..."
echo ""

python backend.py


