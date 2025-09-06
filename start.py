#!/usr/bin/env python3
"""
Local development server for WebDev LLM App
Runs both frontend (React) and backend (FastAPI) simultaneously
"""

import subprocess
import threading
import time
import os
import sys
from pathlib import Path

def run_command(command, cwd=None, shell=True):
    """Run a command in a subprocess"""
    try:
        if cwd:
            os.chdir(cwd)
        print(f"Running: {' '.join(command) if isinstance(command, list) else command} in {cwd or os.getcwd()}")
        subprocess.run(command, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        sys.exit(0)

def run_backend():
    """Start the FastAPI backend server"""
    backend_dir = Path(__file__).parent / "backend"
    print("🚀 Starting FastAPI backend server on http://localhost:8000")
    run_command(["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"], cwd=backend_dir)

def run_frontend():
    """Start the React frontend development server"""
    frontend_dir = Path(__file__).parent / "frontend"
    print("⚛️  Starting React frontend server on http://localhost:3000")
    run_command(["npm", "run", "dev"], cwd=frontend_dir)

def main():
    """Main function to start both servers"""
    print("🌟 Starting WebDev LLM App Development Environment")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("frontend").exists() or not Path("backend").exists():
        print("❌ Error: Please run this script from the WebDev root directory")
        print("Expected structure:")
        print("WebDev/")
        print("├── frontend/")
        print("├── backend/")
        print("└── start.py")
        sys.exit(1)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    print("⏳ Waiting for backend to initialize...")
    time.sleep(3)
    
    # Start frontend (this will block)
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("\n👋 Shutting down development servers...")
        sys.exit(0)

if __name__ == "__main__":
    main()
