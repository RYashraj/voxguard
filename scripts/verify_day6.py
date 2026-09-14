"""
Root wrapper for backend/scripts/verify_day6_sprint.py
Allows running `python scripts/verify_day6.py` from repository root.
"""
import sys
import os
import asyncio
from pathlib import Path

backend_dir = Path(__file__).parent.parent / "backend"
backend_scripts = backend_dir / "scripts"

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_scripts))

from verify_day6_sprint import run_day6_sprint_verification

if __name__ == "__main__":
    asyncio.run(run_day6_sprint_verification())
