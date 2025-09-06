# Simple Railway Deployment

This is a simplified Python deployment for Railway.

## Files Required:
- `main.py` - FastAPI application
- `requirements.txt` - Python dependencies
- `Procfile` - Railway start command
- `railway.json` - Railway configuration
- `runtime.txt` - Python version

## How it works:
1. Railway detects this as a Python project
2. Installs dependencies from `requirements.txt`
3. Runs the command from `Procfile`: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Health check runs on `/health` endpoint

## Environment Variables to set in Railway:
- `MONGODB_URL`
- `SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `BASE_URL` (your Railway app URL)

That's it! No Docker, no complex scripts, just pure Python.
