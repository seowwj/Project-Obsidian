import multiprocessing
import uvicorn
import os
import sys

# Add the current directory to sys.path to ensure 'app' can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.server import app

if __name__ == "__main__":
    multiprocessing.freeze_support()

    uvicorn.run(app, host="127.0.0.1", port=8000, workers=1)
