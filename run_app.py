import subprocess
import sys
import os
from threading import Thread
import time
import signal

# Function to run the backend (FastAPI/Uvicorn)
def run_backend():
    print("Starting backend...")
    try:
        # Run the backend using Uvicorn in a separate process
        backend_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.backend:app", "--reload", "--port", "8000"])
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
        # Run the frontend using npm in a separate process
        frontend_process = subprocess.Popen(["npm", "start"])
        frontend_process.wait()
    except FileNotFoundError:
        print("Error: 'npm' not found. Make sure Node.js and npm are installed and in your PATH.")
    finally:
        print("Frontend process ended.")
        os.chdir('..')  # Return to root folder after running frontend

# Main entry point
if __name__ == "__main__":
    # Store the root directory
    root_dir = os.getcwd()
    
    # Create threads for backend and frontend processes
    backend_thread = Thread(target=run_backend)
    frontend_thread = Thread(target=run_frontend)

    # Start the backend thread
    backend_thread.start()
    time.sleep(2)  # Give backend some time to start

    # Start the frontend thread
    frontend_thread.start()

    # Handle clean exit on keyboard interrupt
    try:
        backend_thread.join()
        frontend_thread.join()
    except KeyboardInterrupt:
        print("Stopping all processes...")
        os.kill(backend_thread.ident, signal.SIGTERM)
        os.kill(frontend_thread.ident, signal.SIGTERM)
    finally:
        print("All processes have been stopped.")
