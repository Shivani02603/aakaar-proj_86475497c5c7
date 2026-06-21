#!/bin/bash
set -euo pipefail

# Start the backend in the background
echo "Starting backend..."
(cd backend && uvicorn main:app --host 0.0.0.0 --port 8000) &

# Wait for backend to start
sleep 5

# Start the frontend development server
echo "Starting frontend..."
(cd frontend && npm run dev)

# Wait for both processes to finish
wait