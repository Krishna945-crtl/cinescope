"""
Recommender 🤖 - "More like this" & "Because you added ..."
Idea: prathi title ni oka vector ga marchestham = story words (TF-IDF on description) + genres.
Rendu vectors enta daggara unte (cosine similarity) anta similar.
"""
from functools import lru_cache

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer, normalize

from .catalog import card, load

GENRE_WEIGHT = 0.3      # story words vs genre - franchise test lo best (scripts/eval_recommender.py)


@lru_cache(maxsize=4)
def vectors(genre_weight=GENRE_WEIGHT):
    df = load()
    text = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    X_text = text.fit_transform(df["description"])
    mlb = MultiLabelBinarizer()
    X_genre = csr_matrix(normalize(mlb.fit_transform(df["genres"]).astype(float)))
    X = hstack([X_text * (1 - genre_weight), X_genre * genre_weight]).tocsr()
    return normalize(X)


@lru_cache(maxsize=1)
def _no_story():
    # Description lekapothe vector lo genre matrame untundi -> anni recommendations lo adi vastundi (hub).
    # Alanti titles ni suggest cheyyam
    return set(np.flatnonzero(load()["description"].str.len().to_numpy() < 40))


def _rank(scores, exclude, kind=None, k=12, genre=None):
    df = load()
    order = np.argsort(-scores)
    out = []
    skip = _no_story()
    for i in order:
        if i in exclude or i in skip:
            continue
        if kind and df.at[i, "kind"] != kind:
            continue
        if genre and genre not in df.at[i, "genres"]:
            continue
        out.append(i)
        if len(out) == k:
            break
    return out


def similar_idx(idx, k=12, kind=None, genre_weight=GENRE_WEIGHT):
    X = vectors(genre_weight)
    scores = (X @ X[idx].T).toarray().ravel()
    return _rank(scores, {idx}, kind, k)


def similar(title_id, k=12):
    df = load()
    hit = df.index[df["id"] == title_id]
    if not len(hit):
        return []
    idx = int(hit[0])
    return [card(df.loc[i]) for i in similar_idx(idx, k, kind=df.at[idx, "kind"])]


def recommend(ids, k=12, kind=None, genre=None):
    """Watchlist lo unna titles anni kalipi, vaatiki daggaraga unna kotha titles 🍿"""
    df = load()
    idx = [int(i) for i in df.index[df["id"].isin(ids)]]
    if not idx:
        return []
    X = vectors()
    profile = normalize(np.asarray(X[idx].mean(axis=0)))
    scores = (X @ profile.T).ravel()
    return [card(df.loc[i]) for i in _rank(np.asarray(scores).ravel(), set(idx), kind, k, genre)]
