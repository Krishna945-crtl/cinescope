"""
Recommender honest ga panichestunda? 🧪
Test: franchise titles (Bāhubali 1 & 2, same series lo parts...). Oka part isthe, inkoka part top 10 lo vastunda?
Title words ni features lo vaadamu - so idi cheating kaadu, story + genre batti matrame kanukkovali.

Compare: random, popular-in-same-genre, story words only, story + genre (different weights)
"""
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog import load, plain  # noqa: E402
from app.recommender import similar_idx  # noqa: E402

COMMON = {"the", "a", "an", "of", "and", "my", "love", "life", "last", "black", "dark", "little", "world",
          "girl", "boys", "girls", "house", "night", "christmas", "king", "true", "story", "great", "big"}


def franchise_key(title):
    # "Bāhubali 2: The Conclusion" -> "bahubali" ; "Toy Story 3" -> "toy story"
    base = re.split(r"[:\-\u2013(]", plain(title))[0]
    base = re.sub(r"\b(\d+|ii|iii|iv|part|chapter|season|vol|volume)\b", " ", base)
    return " ".join(re.findall(r"[a-z]+", base))


def franchise_groups(df):
    groups = defaultdict(list)
    for i, r in df.iterrows():
        key = franchise_key(r["title"])
        if len(key) >= 4 and key not in COMMON:
            groups[(key, r["kind"])].append(i)
    out = {}
    for k, v in groups.items():
        titles = {plain(t) for t in df.loc[v, "title"]}
        # 2-5 titles, and names really differ (sequel / spin-off), same-name remakes kaadu
        if 2 <= len(v) <= 5 and len(titles) == len(v):
            out[k] = v
    return out


def hit_rate(df, groups, rank_fn, k=10):
    hits = total = 0
    for members in groups.values():
        for i in members:
            top = set(rank_fn(i, k))
            hits += bool(top & (set(members) - {i}))
            total += 1
    return round(hits / total * 100, 1), total


def main():
    df = load()
    groups = franchise_groups(df)
    rng = random.Random(7)
    kinds = df["kind"].to_numpy()

    def rand(i, k):
        pool = [j for j in range(len(df)) if kinds[j] == kinds[i] and j != i]
        return rng.sample(pool, k)

    by_genre = {}
    for i, g in enumerate(df["genres"]):
        by_genre.setdefault((g[0], kinds[i]), []).append(i)
    pop = df["tmdb_popularity"].to_numpy()

    def popular(i, k):
        pool = sorted(by_genre[(df.at[i, "genres"][0], kinds[i])], key=lambda j: -pop[j])
        return [j for j in pool if j != i][:k]

    results = {}
    results["Random"] = hit_rate(df, groups, rand)
    results["Popular in same genre"] = hit_rate(df, groups, popular)
    for w in [0.0, 0.3, 0.6, 0.8]:
        name = "Story words only" if w == 0 else f"Story + genre (genre weight {w})"
        results[name] = hit_rate(df, groups, lambda i, k, w=w: similar_idx(i, k, kind=kinds[i], genre_weight=w))

    n = next(iter(results.values()))[1]
    print(f"franchise test: {len(groups)} groups, {n} seed titles, metric = other part in top 10")
    for name, (pct, _) in results.items():
        print(f"  {name:36s} {pct:5.1f}%")
    out = {"groups": len(groups), "seeds": n, "hit_at_10_pct": {k: v[0] for k, v in results.items()},
           "example_groups": [sorted(df.loc[m, "title"].tolist()) for m in list(groups.values())[:12]]}
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "recommender_eval.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
