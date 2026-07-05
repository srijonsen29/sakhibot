"""
Quick start script for SakhiBot server
Run from backend folder: python scripts/start_server.py
Or from scripts folder: python start_server.py
"""
import sys
import os

# Get the backend directory (parent of scripts folder)
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir) if os.path.basename(script_dir) == 'scripts' else script_dir

# Change to backend directory
os.chdir(backend_dir)

# Add backend to path
sys.path.insert(0, backend_dir)

print("=" * 60)
print("  🚀 Starting SakhiBot Server v2.0.0")
print("  Emergency Response Features: ENABLED")
print("=" * 60)
print(f"\n📂 Working directory: {os.getcwd()}")
print("📍 API will be available at: http://localhost:8000")
print("📚 API docs: http://localhost:8000/docs")
print("🧪 Test emergency features: python test_emergency.py\n")

# Start uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
