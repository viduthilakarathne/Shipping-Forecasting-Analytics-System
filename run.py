"""
run.py — Entry point for UK Port Shipping Analytics Application
Copies the source Excel file to the uploads directory, then starts Flask.
"""

import os
import sys
import shutil
from pathlib import Path

# Force UTF-8 output (fixes Windows cp1252 emoji issues)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Auto-copy default dataset to uploads folder
DEFAULT_DATASET = r"C:\Users\ASUS\Downloads\weeklyshippingindicatorsdataset250626.xlsx"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

TARGET = UPLOADS_DIR / "dataset.xlsx"

if not TARGET.exists() and os.path.exists(DEFAULT_DATASET):
    print(f"📋 Copying default dataset to uploads/dataset.xlsx...")
    shutil.copy2(DEFAULT_DATASET, str(TARGET))
    print("✅ Dataset ready.")

# Import and start Flask app
from backend.app import app, bootstrap

if __name__ == "__main__":
    print("=" * 60)
    print("  🚢 UK Port Shipping Analytics Dashboard")
    print("=" * 60)
    bootstrap()
    print(f"\n🌐 Dashboard: http://127.0.0.1:5000")
    print(f"📡 API Base:  http://127.0.0.1:5000/api")
    print(f"\n  Press Ctrl+C to stop the server\n")
    app.run(debug=False, host="0.0.0.0", port=5000, use_reloader=False)
