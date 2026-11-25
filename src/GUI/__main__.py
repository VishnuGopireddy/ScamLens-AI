"""Allow running the ScamLens-AI GUI directly with `python -m GUI`."""

from __future__ import annotations

import argparse

from GUI.server import run_gui_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the ScamLens-AI Web GUI.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    args = parser.parse_args()
    run_gui_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
