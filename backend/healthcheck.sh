#!/bin/bash

# Get port from environment variable or default to 8000
PORT=${PORT:-8000}

# Check if the application is responding
curl -f http://localhost:$PORT/health || exit 1
