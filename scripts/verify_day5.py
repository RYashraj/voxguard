"""
Root wrapper for backend/scripts/verify_day5.py
Allows running `python scripts/verify_day5.py` from repository root.
"""
import sys
import os
import asyncio
from pathlib import Path

# Add backend and backend/scripts to sys.path
backend_dir = Path(__file__).parent.parent / "backend"
backend_scripts = backend_dir / "scripts"

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_scripts))

from verify_day5 import run_day5_verification

if __name__ == "__main__":
    asyncio.run(run_day5_verification())
