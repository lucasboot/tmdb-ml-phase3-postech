"""Vercel serverless entrypoint for the Flask application."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from web.app import create_app  # noqa: E402  (import after sys.path tweak)


app = create_app()

