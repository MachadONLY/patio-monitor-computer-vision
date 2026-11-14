"""Serve the production frontend and API from the same origin."""

import os
from pathlib import Path

from fastapi.staticfiles import StaticFiles

# Render supplies this URL before application startup, including on new deployments.
if not os.getenv("PATIO_PUBLIC_ORIGIN") and os.getenv("RENDER_EXTERNAL_URL"):
    os.environ["PATIO_PUBLIC_ORIGIN"] = os.environ["RENDER_EXTERNAL_URL"]

from .main import app

app.mount("/", StaticFiles(directory=Path(os.environ["PATIO_WEB_DIST"]), html=True), name="web")
