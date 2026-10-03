#!/usr/bin/env python3
"""Run server script for Test-Honesty Gate.

Launches the FastAPI backend server on port 8000 and automatically opens the
browser to the Apple-inspired Web Landing Page & Inspector Dashboard.
"""

import sys
import webbrowser
from pathlib import Path
import uvicorn

# Ensure backend directory is importable
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

def main():
    port = 8000
    url = f"http://127.0.0.1:{port}"
    print(f"🚀 Starting Test-Honesty Gate Server at {url}...")
    print("✨ Opening browser...")
    
    # Auto open browser after brief delay
    webbrowser.open(url)
    
    # Run uvicorn server
    uvicorn.run("backend.api.app:app", host="127.0.0.1", port=port, reload=True)

if __name__ == "__main__":
    main()
