"""
Build step: TMDB_API_KEY unte latest catalog download chestundi, lekapothe Netflix dataset tho continue 🙂
Render build command lo run avutundi:  python scripts/fetch_tmdb.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tmdb import build_catalog  # noqa: E402

key = os.environ.get("TMDB_API_KEY", "").strip()
if not key:
    print("TMDB_API_KEY not set - using the bundled Netflix dataset")
    sys.exit(0)
try:
    build_catalog(key)
except Exception as e:  # build fail avvakoodadhu - dataset tho site pani chestundi
    print(f"TMDB download failed ({e}) - using the bundled Netflix dataset")
