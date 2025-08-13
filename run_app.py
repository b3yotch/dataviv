import subprocess
import threading
import time
import webbrowser
import sys
import os

def run_fastapi():
    """Run FastAPI server"""
    # Force use of current Python interpreter
    subprocess.run([
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--port", "8000"
    ], env=os.environ.copy())  # Use current environment

def run_streamlit():
    """Run Streamlit app"""
    time.sleep(3)
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_app.py",
        "--server.port", "8501"
    ], env=os.environ.copy())  # Use current environment

if __name__ == "__main__":
    print("Starting Caltech 101 Dataset Explorer...")
    print(f"Using Python: {sys.executable}")
    
    # Verify we're in venv
    if "venv" not in sys.executable and ".venv" not in sys.executable:
        print("WARNING: Not running in virtual environment!")
        print("Please activate your virtual environment first:")
        print("  venv\\Scripts\\activate")
        sys.exit(1)
    
    # Start FastAPI in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.daemon = True
    fastapi_thread.start()
    
    print("Starting FastAPI server...")
    time.sleep(3)
    
    print("Opening browser...")
    webbrowser.open("http://localhost:8501")
    
    print("Starting Streamlit UI...")
    run_streamlit()