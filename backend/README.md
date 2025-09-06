# WebDev Backend

FastAPI Authentication Backend for WebDev application.

## Quick Start

This is a simple Python application that Railway will auto-detect and deploy.

## Files

- `main.py` - FastAPI application
- `requirements.txt` - Python dependencies  
- `Procfile` - Start command for Railway
- `runtime.txt` - Python version

## Environment Variables

Set these in Railway:

- `MONGODB_URL` - MongoDB connection string
- `SECRET_KEY` - JWT secret key
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `BASE_URL` - Your Railway app URL

## Health Check

The application has a health check endpoint at `/health`.

That's it! Railway will handle the rest.
