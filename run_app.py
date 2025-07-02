import subprocess
import sys
import os
from threading import Thread
import time
import signal
import requests

# Function to run the backend (FastAPI/Uvicorn)
def run_backend():
    print("Starting backend...")
    try:
        # Run the backend using Uvicorn in a separate process, accessible on all interfaces
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "backend.backend:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
        ])
        backend_process.wait()
    except FileNotFoundError:
        print("Error: 'uvicorn' not found. Make sure it's installed and in your PATH.")
    finally:
        print("Backend process ended.")

# Function to run the frontend (React)
def run_frontend():
    print("Starting frontend...")
    os.chdir('frontend')  # Navigate to the React app folder
    try:
        # Run the frontend using npm in a separate process, accessible on all interfaces
        # If your React app supports HOST env var, this will work:
        frontend_process = subprocess.Popen(["npm", "start"], env={**os.environ, "HOST": "0.0.0.0"})
        frontend_process.wait()
    except FileNotFoundError:
        print("Error: 'npm' not found. Make sure Node.js and npm are installed and in your PATH.")
    finally:
        print("Frontend process ended.")
        os.chdir('..')  # Return to root folder after running frontend

# Wait for backend to be ready
def wait_for_backend(url, timeout=30):
    print("Waiting for backend to be ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Backend is ready!")
                return True
        except Exception:
            pass
        time.sleep(0.5)
    print(f"Backend was not ready after {timeout} seconds.")
    return False

# Main entry point
if __name__ == "__main__":
    # Store the root directory
    root_dir = os.getcwd()
    
    # Create threads for backend and frontend processes
    backend_thread = Thread(target=run_backend)
    frontend_thread = Thread(target=run_frontend)

    # Start the backend thread
    backend_thread.start()

    # Wait for backend to be ready before starting frontend
    if wait_for_backend("http://localhost:8000/bots", timeout=30):
        # Start the frontend thread
        frontend_thread.start()
    else:
        print("Frontend will not start because backend is not ready.")

    # Handle clean exit on keyboard interrupt
    try:
        backend_thread.join()
        if frontend_thread.is_alive():
            frontend_thread.join()
    except KeyboardInterrupt:
        print("Stopping all processes...")
        # Note: Proper process termination should be handled here if needed
    finally:
        print("All processes have been stopped.")
