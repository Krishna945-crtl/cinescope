"""
CineScope API 🎬 (FastAPI)
Run: uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import catalog, recommender

STATIC = Path(__file__).resolve().parents[1] / "static"
Kind = Literal["movie", "series"]


@asynccontextmanager
async def lifespan(_app):
    # Data + vectors mundu load chesthe first request slow avvadu ⚡
    catalog.load()
    recommender.vectors()
    yield


app = FastAPI(title="CineScope", description="Genre-first movie & web series explorer with recommendations",
              lifespan=lifespan)


@app.get("/api/meta")
def meta():
    return catalog.meta()


@app.get("/api/genres")
def genres():
    return catalog.genre_list()


@app.get("/api/browse")
def browse(kind: Kind = "movie", genre: str | None = None, lang: str | None = None):
    if genre and genre not in {g["key"] for g in catalog.genre_list()}:
        raise HTTPException(404, f"Unknown genre '{genre}'")
    if lang and lang not in catalog.LANGUAGES:
        raise HTTPException(404, f"Unknown language '{lang}'")
    return catalog.browse(kind, genre, lang)


@app.get("/api/search")
def search(q: str = Query(..., min_length=1, max_length=80)):
    return catalog.search(q)


@app.get("/api/title/{title_id}")
def title(title_id: str):
    t = catalog.get(title_id)
    if not t:
        raise HTTPException(404, "Title not found")
    return {**t, "similar": recommender.similar(title_id, k=12)}


class RecommendIn(BaseModel):
    ids: list[str] = Field(..., min_length=1, max_length=100)
    kind: Kind | None = None
    genre: str | None = None      # genre page lo unte aa genre lone suggestions


@app.post("/api/recommend")
def recommend(body: RecommendIn):
    return recommender.recommend(body.ids, k=16, kind=body.kind, genre=body.genre)


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
