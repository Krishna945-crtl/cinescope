"""
TMDB nundi latest movies + web series teesukuni, mana catalog format lo save chestundi 🌐
Key: TMDB_API_KEY environment variable (GitHub lo ennadu pettakoodadhu 🔒)
  - short API key (v3) or long "API Read Access Token" (v4) - rendu pani chestayi

This product uses the TMDB API but is not endorsed or certified by TMDB.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

API = "https://api.themoviedb.org/3"
OUT = Path(__file__).resolve().parents[1] / "data" / "tmdb_catalog.csv"
PAGES_PER_GENRE = 4          # 4 x 20 = 80 titles per genre
PAGES_PER_LANGUAGE = 5
INDIAN_LANGS = ["te", "hi", "ta", "ml", "kn"]

# TMDB genre id -> mana genre keys
MOVIE_GENRES = {
    28: ["action"], 12: ["adventure"], 16: ["animation"], 35: ["comedy"], 80: ["crime"],
    99: ["documentation"], 18: ["drama"], 10751: ["family"], 14: ["fantasy"], 36: ["history"],
    27: ["horror"], 10402: ["music"], 9648: ["mystery"], 10749: ["romance"], 878: ["scifi"],
    53: ["thriller"], 10752: ["war"], 37: ["western"],
}
TV_GENRES = {
    10759: ["action", "adventure"], 16: ["animation"], 35: ["comedy"], 80: ["crime"],
    99: ["documentation"], 18: ["drama"], 10751: ["family"], 10762: ["family"], 9648: ["mystery"],
    10764: ["reality"], 10765: ["scifi", "fantasy"], 10766: ["drama"], 10768: ["war"], 37: ["western"],
}


def _get(path, key, **params):
    params = {"language": "en-US", "include_adult": "false", **params}
    headers = {"accept": "application/json"}
    if key.startswith("eyJ"):                 # v4 read access token
        headers["Authorization"] = f"Bearer {key}"
    else:                                     # v3 api key
        params["api_key"] = key
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:                 # too many requests - konchem aagi malli 🔁
                time.sleep(1 + attempt)
                continue
            raise
    raise RuntimeError(f"TMDB kept rate-limiting {path}")


def to_row(item, kind):
    """Oka TMDB result ni mana catalog row ga marchedi (Netflix dataset columns laane)"""
    gmap = MOVIE_GENRES if kind == "movie" else TV_GENRES
    genres = []
    for gid in item.get("genre_ids", []):
        for g in gmap.get(gid, []):
            if g not in genres:
                genres.append(g)
    date = item.get("release_date") if kind == "movie" else item.get("first_air_date")
    if not genres or not date or len(date) < 4:
        return None
    lang = item.get("original_language")
    countries = list(item.get("origin_country") or [])
    if lang in INDIAN_LANGS and "IN" not in countries:
        countries.append("IN")
    return {
        "id": f"tmdb-{'m' if kind == 'movie' else 't'}{item['id']}",
        "title": item.get("title") or item.get("name"),
        "type": "MOVIE" if kind == "movie" else "SHOW",
        "description": item.get("overview") or "",
        "release_year": int(date[:4]),
        "age_certification": None, "runtime": None, "seasons": None, "imdb_id": None,
        "genres": str(genres),
        "production_countries": str(countries),
        "imdb_score": item.get("vote_average"),
        "imdb_votes": item.get("vote_count"),
        "tmdb_popularity": item.get("popularity"),
        "tmdb_score": item.get("vote_average"),
        "poster_path": item.get("poster_path"),
        "language": lang,
        "rating_source": "TMDB",
    }


def build_catalog(key, out=OUT, log=print):
    rows = {}
    jobs = []
    for kind, gmap in [("movie", MOVIE_GENRES), ("tv", TV_GENRES)]:
        for gid in gmap:
            for page in range(1, PAGES_PER_GENRE + 1):
                jobs.append((kind, {"with_genres": gid, "page": page, "vote_count.gte": 30 if kind == "movie" else 10}))
        for lang in INDIAN_LANGS:
            for page in range(1, PAGES_PER_LANGUAGE + 1):
                jobs.append((kind, {"with_original_language": lang, "page": page, "vote_count.gte": 5}))
    for n, (kind, params) in enumerate(jobs, 1):
        data = _get(f"/discover/{kind}", key, sort_by="popularity.desc", **params)
        for item in data.get("results", []):
            row = to_row(item, "movie" if kind == "movie" else "tv")
            if row:
                rows[row["id"]] = row
        if n % 25 == 0:
            log(f"  {n}/{len(jobs)} requests, {len(rows)} titles")
        time.sleep(0.03)
    df = pd.DataFrame(rows.values())
    out.parent.mkdir(exist_ok=True)
    df.to_csv(out, index=False)
    log(f"saved {len(df)} titles ({(df['type'] == 'MOVIE').sum()} movies, {(df['type'] == 'SHOW').sum()} series) -> {out}")
    return df


if __name__ == "__main__":
    key = os.environ.get("TMDB_API_KEY", "").strip()
    if not key:
        raise SystemExit("Set TMDB_API_KEY first")
    build_catalog(key)
