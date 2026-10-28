"""Pytest test fixtures and configuration."""

import sys
from pathlib import Path

# Add src to sys.path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

