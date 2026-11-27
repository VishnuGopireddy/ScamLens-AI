#!/usr/bin/env python3
"""Launch the ScamLens-AI interactive Web GUI (zero extra dependencies)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from GUI.server import run_gui_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the ScamLens-AI Web GUI.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    args = parser.parse_args()
    run_gui_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
