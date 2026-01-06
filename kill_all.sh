#!/bin/bash

# Kill All Death Sentence Processes
# Terminates all backend and frontend servers

echo "╔════════════════════════════════════════╗"
echo "║  Terminating All Processes            ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Function to kill processes on a port
kill_port() {
    PORT=$1
    NAME=$2
    PIDS=$(lsof -ti:$PORT 2>/dev/null)
    
    if [ ! -z "$PIDS" ]; then
        echo "🔪 Killing $NAME (port $PORT)..."
        kill -9 $PIDS 2>/dev/null
        echo "   ✅ Terminated PIDs: $PIDS"
    else
        echo "✓  $NAME (port $PORT) - no process running"
    fi
}

# Kill all services
kill_port 5000 "BLE Backend"
kill_port 8000 "AI Backend"
kill_port 8080 "Frontend Server"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  All processes terminated             ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "You can now restart the servers:"
echo "  ./start_ble_backend.sh"
echo "  ./restart_ai_backend.sh"
echo "  ./start_frontend.sh"


