"""TMDB mode tests - real API call cheyyakunda fake TMDB responses tho 🧪"""
import random

import pytest
from fastapi.testclient import TestClient

from app import catalog, recommender, tmdb
from app.main import app

STORIES = [
    "A police officer hunts a ruthless gang across the city after a bank robbery.",
    "Two strangers fall in love during a rainy summer in a small hill town.",
    "A family haunted by a ghost in their old village house tries to escape.",
    "A young farmer fights a corrupt landlord to save his village.",
    "An astronaut stranded on a distant planet must find a way home.",
]


def fake_page(kind, params):
    rng = random.Random(str(params))
    gmap = tmdb.MOVIE_GENRES if kind == "movie" else tmdb.TV_GENRES
    lang = params.get("with_original_language", "en")
    gid = params.get("with_genres") or rng.choice(list(gmap))
    results = []
    for i in range(20):
        tid = rng.randint(1, 10**6)
        item = {"id": tid, "overview": rng.choice(STORIES), "genre_ids": [gid, rng.choice(list(gmap))],
                "original_language": lang, "vote_average": round(rng.uniform(5, 9), 1),
                "vote_count": rng.randint(50, 5000), "popularity": rng.uniform(1, 300),
                "poster_path": f"/p{tid}.jpg"}
        if kind == "movie":
            item.update(title=f"Movie {tid}", release_date=f"{rng.randint(2015, 2026)}-01-01")
        else:
            item.update(name=f"Show {tid}", first_air_date=f"{rng.randint(2015, 2026)}-01-01", origin_country=[])
        results.append(item)
    return {"results": results}


def test_to_row_maps_genres_language_and_india():
    row = tmdb.to_row({"id": 7, "title": "Test", "release_date": "2024-03-01", "genre_ids": [28, 53],
                       "original_language": "te", "overview": "x", "poster_path": "/a.jpg"}, "movie")
    assert eval(row["genres"]) == ["action", "thriller"]
    assert "IN" in eval(row["production_countries"]) and row["language"] == "te"
    tv = tmdb.to_row({"id": 8, "name": "S", "first_air_date": "2023-01-01", "genre_ids": [10759],
                      "original_language": "en"}, "tv")
    assert eval(tv["genres"]) == ["action", "adventure"] and tv["type"] == "SHOW"
    assert tmdb.to_row({"id": 9, "title": "No date", "genre_ids": [28]}, "movie") is None


@pytest.fixture()
def tmdb_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(tmdb, "_get", lambda path, key, **p: fake_page(path.rsplit("/", 1)[-1], p))
    monkeypatch.setattr(tmdb.time, "sleep", lambda s: None)
    out = tmp_path / "tmdb_catalog.csv"
    tmdb.build_catalog("fake-key", out=out, log=lambda *a: None)
    monkeypatch.setattr(catalog, "TMDB_CSV", out)
    for f in (catalog.load, recommender.vectors, recommender._no_story):
        f.cache_clear()
    yield TestClient(app)
    for f in (catalog.load, recommender.vectors, recommender._no_story):
        f.cache_clear()


def test_tmdb_catalog_is_used_with_posters_and_languages(tmdb_mode):
    meta = tmdb_mode.get("/api/meta").json()
    assert meta["source"] == "tmdb" and "TMDB" in meta["attribution"]
    assert "te" in {l["code"] for l in meta["languages"]}
    r = tmdb_mode.get("/api/browse", params={"kind": "movie", "genre": "action", "lang": "te"}).json()
    items = [c for row in r["rows"] for c in row["items"]]
    assert items and all(c["language"] == "Telugu" and c["india"] for c in items)
    assert all(c["poster"].startswith("https://image.tmdb.org/") for c in items)
    assert any(row["title"] == "Top rated on TMDB" for row in r["rows"])


def test_unknown_language_is_404(tmdb_mode):
    assert tmdb_mode.get("/api/browse", params={"lang": "xx"}).status_code == 404
