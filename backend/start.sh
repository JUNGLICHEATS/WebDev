#!/bin/bash

# Get port from environment variable or default to 8000
PORT=${PORT:-8000}

# Start the application
echo "Starting FastAPI application on port $PORT"
uvicorn main:app --host 0.0.0.0 --port $PORT
