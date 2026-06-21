#!/bin/bash
set -euo pipefail

# Start backend in the background
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Start frontend development server
cd frontend
npm run dev

# Wait for background processes to finish
wait