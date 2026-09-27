"""API tests 🧪  Run: pytest -q"""
from fastapi.testclient import TestClient

from app.catalog import load
from app.main import app

client = TestClient(app)


def _id(title):
    df = load()
    return df.loc[df["title"] == title, "id"].iloc[0]


def test_genres_have_emoji_and_theme():
    g = client.get("/api/genres").json()
    action = next(x for x in g if x["key"] == "action")
    assert action["emoji"] and action["theme"]["accent"].startswith("#")
    assert action["count"] > 100


def test_browse_action_movies_has_rows_and_subgenres():
    r = client.get("/api/browse", params={"kind": "movie", "genre": "action"}).json()
    titles = [row["title"] for row in r["rows"]]
    assert "Popular now" in titles
    assert all("action" in c["genres"] for row in r["rows"] for c in row["items"])
    assert all(c["kind"] == "movie" for row in r["rows"] for c in row["items"])
    names = [s["title"] for s in r["subgenres"]]
    assert "Crime Action" in names and "Action Thriller" in names


def test_series_are_separate_from_movies():
    r = client.get("/api/browse", params={"kind": "series", "genre": "romance"}).json()
    assert all(c["kind"] == "series" for s in r["subgenres"] for c in s["items"])


def test_unknown_genre_is_404():
    assert client.get("/api/browse", params={"genre": "cooking"}).status_code == 404


def test_search_detects_genre_and_ignores_accents():
    r = client.get("/api/search", params={"q": "romantic"}).json()
    assert r["genre"]["key"] == "romance"
    r = client.get("/api/search", params={"q": "bahubali"}).json()
    assert any("Bāhubali" in c["title"] for c in r["results"])


def test_similar_finds_the_sequel():
    r = client.get(f"/api/title/{_id('Bāhubali: The Beginning')}").json()
    assert "Bāhubali 2: The Conclusion" in [c["title"] for c in r["similar"]]


def test_recommend_excludes_watchlist_items():
    ids = [_id("Sooryavanshi"), _id("Dhamaka")]
    recs = client.post("/api/recommend", json={"ids": ids}).json()
    assert recs and not set(ids) & {c["id"] for c in recs}


def test_recommend_validates_input():
    assert client.post("/api/recommend", json={"ids": []}).status_code == 422


def test_recommend_can_stay_inside_a_genre():
    ids = [_id("Sooryavanshi"), _id("Dhamaka")]
    recs = client.post("/api/recommend", json={"ids": ids, "genre": "romance", "kind": "movie"}).json()
    assert recs and all("romance" in c["genres"] and c["kind"] == "movie" for c in recs)
