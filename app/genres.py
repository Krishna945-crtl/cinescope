"""
Genre info: display name, emoji, colour theme 🎨
Main genre select chesthe website theme ee colours ki maarutundi.
"""

# theme = (background, card surface, accent, text)
GENRES = {
    "action":        {"label": "Action",        "emoji": "💥", "theme": ("#1a0405", "#2b0a0c", "#c1121f", "#fbe9e9")},  # blood red
    "thriller":      {"label": "Thriller",      "emoji": "🔫", "theme": ("#0f0f14", "#1c1c26", "#e63946", "#ececf1")},
    "crime":         {"label": "Crime",         "emoji": "🔪", "theme": ("#111111", "#1f1f1f", "#b91c1c", "#eeeeee")},
    "horror":        {"label": "Horror",        "emoji": "👻", "theme": ("#0b0710", "#1a1024", "#7b2cbf", "#efe6fb")},
    "war":           {"label": "War",           "emoji": "💣", "theme": ("#14170f", "#23281a", "#6b8e23", "#eef2e4")},
    "romance":       {"label": "Romance",       "emoji": "❤️", "theme": ("#fff0f5", "#ffe0ec", "#e75480", "#4a1a2c")},  # pink
    "comedy":        {"label": "Comedy",        "emoji": "😂", "theme": ("#fffbea", "#fff1c2", "#f59e0b", "#3d2e00")},
    "family":        {"label": "Family",        "emoji": "👨‍👩‍👧", "theme": ("#eef7ff", "#dcefff", "#3b82f6", "#10233d")},  # light blue
    "animation":     {"label": "Animation",     "emoji": "🎨", "theme": ("#eefaff", "#d8f3ff", "#0ea5e9", "#0c2a3a")},
    "drama":         {"label": "Drama",         "emoji": "🎭", "theme": ("#1b1410", "#2a1f18", "#d97706", "#f7ede4")},
    "scifi":         {"label": "Sci-Fi",        "emoji": "🚀", "theme": ("#050b1a", "#0d1a33", "#22d3ee", "#e2f5ff")},
    "fantasy":       {"label": "Fantasy",       "emoji": "🧙", "theme": ("#120a1f", "#211436", "#a78bfa", "#f1ebff")},
    "documentation": {"label": "Documentary",   "emoji": "🎥", "theme": ("#f3f6ef", "#e3ebd9", "#4d7c0f", "#1f2a12")},
    "history":       {"label": "History",       "emoji": "📜", "theme": ("#f7f1e3", "#ecdfc4", "#92400e", "#2d1f0b")},
    "music":         {"label": "Music",         "emoji": "🎵", "theme": ("#140a1a", "#24122e", "#ec4899", "#fbe8f4")},
    "sport":         {"label": "Sport",         "emoji": "⚽", "theme": ("#f0fdf4", "#dcfce7", "#16a34a", "#0f2e1a")},
    "reality":       {"label": "Reality",       "emoji": "📺", "theme": ("#fdf4ff", "#fae8ff", "#c026d3", "#3b0a40")},
    "western":       {"label": "Western",       "emoji": "🤠", "theme": ("#1f150c", "#2e2012", "#d4a373", "#f6ecdf")},
    "european":      {"label": "European",      "emoji": "🇪🇺", "theme": ("#0b1633", "#132449", "#facc15", "#eef2ff")},
    # TMDB lo matrame vache genres
    "adventure":     {"label": "Adventure",     "emoji": "🧭", "theme": ("#10180d", "#1d2a17", "#f97316", "#f3f0e6")},
    "mystery":       {"label": "Mystery",       "emoji": "🕵️", "theme": ("#07151a", "#10262e", "#14b8a6", "#e3f6f4")},
}

DEFAULT_THEME = ("#0e1116", "#1a1f27", "#e50914", "#f2f2f2")

# Konni combos ki natural ga pilichedi peru + prathyeka emoji (lekapothe "<Other> <Main>" ani pedatham)
SPECIAL_SUBGENRES = {
    frozenset({"action", "thriller"}): ("Action Thriller", "🔫"),
    frozenset({"action", "crime"}): ("Crime Action", "🔪"),
    frozenset({"action", "drama"}): ("Drama Action", "🎭"),
    frozenset({"action", "comedy"}): ("Action Comedy", "🤜"),
    frozenset({"action", "scifi"}): ("Sci-Fi Action", "🚀"),
    frozenset({"action", "war"}): ("War Action", "💣"),
    frozenset({"action", "fantasy"}): ("Fantasy Action", "🗡️"),
    frozenset({"action", "animation"}): ("Animated Action", "🦸"),
    frozenset({"romance", "comedy"}): ("Romantic Comedy", "💘"),
    frozenset({"romance", "drama"}): ("Romantic Drama", "💔"),
    frozenset({"romance", "music"}): ("Musical Romance", "🎶"),
    frozenset({"crime", "thriller"}): ("Crime Thriller", "🕵️"),
    frozenset({"crime", "drama"}): ("Crime Drama", "⚖️"),
    frozenset({"horror", "thriller"}): ("Horror Thriller", "🩸"),
    frozenset({"horror", "comedy"}): ("Horror Comedy", "🤡"),
    frozenset({"scifi", "thriller"}): ("Sci-Fi Thriller", "👽"),
    frozenset({"family", "animation"}): ("Family Animation", "🧸"),
    frozenset({"comedy", "drama"}): ("Comedy Drama", "🙂"),
    frozenset({"history", "war"}): ("War History", "🎖️"),
    frozenset({"documentation", "crime"}): ("True Crime", "🔍"),
    frozenset({"documentation", "sport"}): ("Sports Documentary", "🏆"),
    frozenset({"action", "adventure"}): ("Action Adventure", "🗺️"),
    frozenset({"mystery", "thriller"}): ("Mystery Thriller", "🔍"),
    frozenset({"crime", "mystery"}): ("Crime Mystery", "🕵️"),
}


def genre_info(key):
    g = GENRES.get(key, {"label": key.title(), "emoji": "🎬", "theme": DEFAULT_THEME})
    bg, surface, accent, text = g["theme"]
    return {"key": key, "label": g["label"], "emoji": g["emoji"],
            "theme": {"bg": bg, "surface": surface, "accent": accent, "text": text}}


# Sub-genre peru natural ga undali: "Romance Action" kaadu, "Romantic Action" 🙂
ADJECTIVE = {"romance": "Romantic", "animation": "Animated", "history": "Historical", "music": "Musical",
             "documentation": "Documentary-style", "sport": "Sports", "war": "War", "family": "Family"}


def subgenre_name(main, other):
    special = SPECIAL_SUBGENRES.get(frozenset({main, other}))
    if special:
        return special
    adj = ADJECTIVE.get(other, GENRES.get(other, {"label": other.title()})["label"])
    return f"{adj} {GENRES[main]['label']}", GENRES.get(other, {}).get("emoji", "🎬")
