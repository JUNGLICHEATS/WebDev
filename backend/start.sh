#!/bin/bash

# Get port from environment variable or default to 8000
PORT=${PORT:-8000}

# Start the application
echo "Starting FastAPI application on port $PORT"
# Bind to both IPv4 and IPv6 for Railway v2 compatibility
uvicorn main:app --host :: --port $PORT
