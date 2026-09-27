"""
Catalog - titles load chesi, browse rows (Popular, Top rated, From India, sub-genres) tayaru chestundi 🎬
Data: TMDB catalog (data/tmdb_catalog.csv, TMDB_API_KEY unte build time lo download) -
      lekapothe Netflix titles dataset (JustWatch, May 2022) - 5.8K movies + web series.
"""
import ast
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .genres import GENRES, SPECIAL_SUBGENRES, genre_info, subgenre_name

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA = DATA_DIR / "titles.csv"
TMDB_CSV = DATA_DIR / "tmdb_catalog.csv"
POSTER_URL = "https://image.tmdb.org/t/p/w342"
LANGUAGES = {"te": "Telugu", "hi": "Hindi", "ta": "Tamil", "ml": "Malayalam", "kn": "Kannada",
             "en": "English", "ko": "Korean", "ja": "Japanese", "es": "Spanish"}
ROW_SIZE = 20
KINDS = {"movie": "MOVIE", "series": "SHOW"}

# Search lo users type chese maatalu -> mana genre key
GENRE_WORDS = {
    "action": "action", "fight": "action", "thriller": "thriller", "suspense": "thriller",
    "crime": "crime", "gangster": "crime", "horror": "horror", "scary": "horror", "ghost": "horror",
    "romance": "romance", "romantic": "romance", "love": "romance", "comedy": "comedy", "funny": "comedy",
    "family": "family", "kids": "family", "animation": "animation", "animated": "animation", "cartoon": "animation",
    "drama": "drama", "scifi": "scifi", "sci-fi": "scifi", "sci fi": "scifi", "science fiction": "scifi",
    "fantasy": "fantasy", "documentary": "documentation", "documentaries": "documentation",
    "history": "history", "historical": "history", "music": "music", "musical": "music",
    "sport": "sport", "sports": "sport", "reality": "reality", "war": "war", "western": "western",
    "adventure": "adventure", "mystery": "mystery", "detective": "mystery",
}


def plain(text):
    # "Bāhubali" -> "bahubali" - accents lekunda search cheyyadaniki
    return unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower()


def _card_emoji(genres):
    # Rendu genres ki special combo unte adi (ex: crime+action = 🔪), lekapothe first genre emoji
    for i, a in enumerate(genres[:3]):
        for b in genres[i + 1:4]:
            special = SPECIAL_SUBGENRES.get(frozenset({a, b}))
            if special:
                return special[1]
    return GENRES.get(genres[0], {}).get("emoji", "🎬") if genres else "🎬"


def source():
    """TMDB catalog download ayithe adi, lekapothe Netflix dataset"""
    try:
        if TMDB_CSV.exists() and TMDB_CSV.stat().st_size > 1000:
            return "tmdb"
    except OSError:
        pass
    return "netflix"


@lru_cache(maxsize=1)
def load():
    src = source()
    df = pd.read_csv(TMDB_CSV if src == "tmdb" else DATA)
    for col, default in [("poster_path", None), ("language", None), ("rating_source", "IMDb")]:
        if col not in df:
            df[col] = default
    df["genres"] = df["genres"].apply(ast.literal_eval)
    df["countries"] = df["production_countries"].apply(ast.literal_eval)
    df = df[df["genres"].str.len() > 0].copy()                  # genre lekapothe browse lo pettalem
    df = df.dropna(subset=["title"]).drop_duplicates("id")
    df["kind"] = df["type"].map({"MOVIE": "movie", "SHOW": "series"})
    df["tmdb_popularity"] = df["tmdb_popularity"].fillna(0)
    df["imdb_votes"] = df["imdb_votes"].fillna(0)
    df["description"] = df["description"].fillna("")
    df["emoji"] = df["genres"].apply(_card_emoji)
    df["title_plain"] = df["title"].apply(plain)
    return df.reset_index(drop=True)


def card(r):
    return {
        "id": r["id"], "title": r["title"], "kind": r["kind"], "year": int(r["release_year"]),
        "genres": r["genres"], "emoji": r["emoji"],
        "genre_labels": [GENRES.get(g, {"label": g.title()})["label"] for g in r["genres"]],
        "rating": None if pd.isna(r["imdb_score"]) or not r["imdb_score"] else round(float(r["imdb_score"]), 1),
        "rating_src": r["rating_source"],
        "poster": None if pd.isna(r["poster_path"]) or not r["poster_path"] else POSTER_URL + r["poster_path"],
        "language": None if pd.isna(r["language"]) else LANGUAGES.get(r["language"], r["language"]),
        "age": None if pd.isna(r["age_certification"]) else r["age_certification"],
        "runtime": None if pd.isna(r["runtime"]) else int(r["runtime"]),
        "seasons": None if pd.isna(r["seasons"]) else int(r["seasons"]),
        "india": "IN" in r["countries"],
        "description": r["description"],
    }


def _row(title, emoji, frame, key=None):
    return {"key": key or re.sub(r"\W+", "-", title.lower()).strip("-"), "title": title, "emoji": emoji,
            "items": [card(r) for _, r in frame.head(ROW_SIZE).iterrows()]}


def _popular(frame):
    return frame.sort_values("tmdb_popularity", ascending=False)


def _top_rated(frame, kind):
    # Konchem votes unna vaatike rating nammagalam (TMDB lo votes takkuva untayi)
    if source() == "tmdb":
        min_votes = 300 if kind == "movie" else 100
    else:
        min_votes = 5000 if kind == "movie" else 2000
    rated = frame[frame["imdb_votes"] >= min_votes]
    return rated.sort_values(["imdb_score", "imdb_votes"], ascending=False)


def genre_list():
    df = load()
    out = []
    for key in GENRES:
        n = int(df["genres"].apply(lambda g: key in g).sum())
        if n:
            out.append({**genre_info(key), "count": n})
    return sorted(out, key=lambda g: -g["count"])


def languages():
    """TMDB mode lo matrame language info untundi"""
    df = load()
    counts = df["language"].dropna().value_counts()
    return [{"code": c, "label": LANGUAGES[c], "count": int(counts[c])} for c in LANGUAGES if c in counts]


def meta():
    src = source()
    return {"source": src, "languages": languages(),
            "attribution": ("This product uses the TMDB API but is not endorsed or certified by TMDB."
                            if src == "tmdb" else "Data: Netflix titles dataset (JustWatch, May 2022)")}


def browse(kind="movie", genre=None, lang=None):
    df = load()
    frame = df[df["kind"] == kind]
    if genre:
        frame = frame[frame["genres"].apply(lambda g: genre in g)]
    if lang:
        frame = frame[frame["language"] == lang]
    src = "TMDB" if source() == "tmdb" else "IMDb"
    rows = [
        _row("Popular now", "🔥", _popular(frame)),
        _row(f"Top rated on {src}", "⭐", _top_rated(frame, kind)),
        _row("From India", "🇮🇳", _popular(frame[frame["countries"].apply(lambda c: "IN" in c)])),
        _row("Recently released", "🆕", frame.sort_values(["release_year", "tmdb_popularity"], ascending=False)),
    ]
    subgenres = []
    if genre:
        # Sub-genres = ee genre tho kalisi vache vere genres (ex: action + crime = Crime Action)
        others = pd.Series([o for g in frame["genres"] for o in g if o != genre]).value_counts()
        for other, n in others.items():
            if n < 6:
                continue
            name, emoji = subgenre_name(genre, other)
            part = frame[frame["genres"].apply(lambda g, o=other: o in g)]
            subgenres.append({**_row(name, emoji, _popular(part), key=f"{genre}-{other}"), "count": int(n)})
    else:
        for g in genre_list()[:8]:
            part = frame[frame["genres"].apply(lambda x, k=g["key"]: k in x)]
            subgenres.append({**_row(g["label"], g["emoji"], _popular(part), key=g["key"]), "count": len(part)})
    return {
        "kind": kind,
        "genre": genre_info(genre) if genre else None,
        "language": LANGUAGES.get(lang) if lang else None,
        "total": int(len(frame)),
        "rows": [r for r in rows if r["items"]],
        "subgenres": subgenres,
    }


def match_genre(q):
    q = q.strip().lower()
    if q in GENRE_WORDS:
        return GENRE_WORDS[q]
    words = re.findall(r"[a-z\-]+", q)
    for w in words:
        if w in GENRE_WORDS:
            return GENRE_WORDS[w]
    return None


def search(q, limit=40):
    df = load()
    q = (q or "").strip()
    if not q:
        return {"genre": None, "results": []}
    genre = match_genre(q)
    hits = df[df["title_plain"].str.contains(re.escape(plain(q)), na=False)]
    hits = _popular(hits)
    return {"genre": genre_info(genre) if genre else None,
            "results": [card(r) for _, r in hits.head(limit).iterrows()]}


def get(title_id):
    df = load()
    hit = df[df["id"] == title_id]
    return card(hit.iloc[0]) if len(hit) else None
