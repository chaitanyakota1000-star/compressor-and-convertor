import uvicorn
import os
import sys

# Ensure we can import modules from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting Universal File & Image Compressor API...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
