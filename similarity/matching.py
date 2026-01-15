"""
Similarity matching engine for finding comparable titles.
"""

# Genre mapping from dropdown options to TMDb genre names
GENRE_MAP = {
    "Action/Adventure": ["Action", "Adventure"],
    "Drama": ["Drama"],
    "Comedy": ["Comedy"],
    "Horror/Thriller": ["Horror", "Thriller"],
    "Sci-Fi/Fantasy": ["Science Fiction", "Fantasy"],
}

# Scale tiers in order (for adjacency matching)
SCALE_TIERS = [
    "Blockbuster",
    "Major Studio",
    "Mid-Budget",
    "Indie",
    "Micro",
]

# Attribute adjacency for partial matching
ADJACENCY = {
    "vfx": ["Heavy", "Moderate", "Light", "Practical Only"],
    "action": ["High", "Moderate", "Light", "Dialogue-Driven"],
    "period": ["Futuristic", "Contemporary", "Recent Past (1980-2010)", "Period (1900-1980)", "Historical (pre-1900)"],
    "star_power": ["A-List", "B-List", "Rising Stars", "Ensemble/Unknown"],
}


def matches_genre(user_genre: str, title_genres: list) -> bool:
    """Check if user's selected genre matches any of the title's genres."""
    if not title_genres:
        return False

    target_genres = GENRE_MAP.get(user_genre, [])
    return any(g in target_genres for g in title_genres)


def match_scale(user_scale: str, title_scale: str) -> float:
    """
    Match production scale with adjacency scoring.
    Returns 100 for exact match, 50 for adjacent tier, 0 otherwise.
    """
    if not title_scale:
        return 0

    # Extract tier name from title_scale (e.g., "Blockbuster ($100M+)" -> "Blockbuster")
    title_tier = title_scale.split(" (")[0] if title_scale else ""
    user_tier = user_scale.split(" (")[0] if user_scale else ""

    if title_tier == user_tier:
        return 100

    # Check adjacency
    try:
        user_idx = SCALE_TIERS.index(user_tier)
        title_idx = SCALE_TIERS.index(title_tier)
        if abs(user_idx - title_idx) == 1:
            return 50
    except ValueError:
        pass

    return 0


def is_adjacent(attr: str, val1: str, val2: str) -> bool:
    """Check if two attribute values are adjacent in their scale."""
    if attr not in ADJACENCY:
        return False

    order = ADJACENCY[attr]
    try:
        idx1 = order.index(val1)
        idx2 = order.index(val2)
        return abs(idx1 - idx2) == 1
    except ValueError:
        return False


def compute_similarity(user_attrs: dict, title: dict) -> tuple[float, list]:
    """
    Compute similarity score between user-selected attributes and a database title.
    Returns (score 0-100, list of matching reasons).
    """
    score = 0
    reasons = []

    # Attribute weights (total = 100)
    weights = {
        "genre": 25,      # Primary genre match
        "scale": 20,      # Budget scale match
        "vfx": 15,        # VFX intensity match
        "action": 15,     # Action complexity match
        "period": 15,     # Period/era match
        "star_power": 10, # Star power match
    }

    # Genre matching
    if matches_genre(user_attrs.get("genre", ""), title.get("genres", [])):
        score += weights["genre"]
        if title.get("genres"):
            reasons.append(f"Genre: {title['genres'][0]}")

    # Scale matching (exact or adjacent tier)
    scale_score = match_scale(user_attrs.get("scale", ""), title.get("computed_scale", ""))
    score += scale_score * weights["scale"] / 100
    if scale_score >= 50:
        scale_display = title.get("computed_scale", "N/A").split(" (")[0]
        reasons.append(f"Scale: {scale_display}")

    # Other attributes (exact match = full points, partial = half)
    attr_map = {
        "vfx": "computed_vfx",
        "action": "computed_action",
        "period": "computed_period",
        "star_power": "computed_star_power",
    }

    for attr, title_key in attr_map.items():
        user_val = user_attrs.get(attr, "")
        title_val = title.get(title_key, "")

        if user_val and title_val:
            if user_val == title_val:
                score += weights[attr]
                reasons.append(f"{attr.replace('_', ' ').title()}: {title_val}")
            elif is_adjacent(attr, user_val, title_val):
                score += weights[attr] * 0.5

    return score, reasons


def filter_by_scale(user_scale: str, title_scale: str) -> bool:
    """
    Check if title matches the selected scale.
    Scale is a HARD FILTER - only exact matches are included.
    """
    if not title_scale:
        return False

    # Extract tier names (e.g., "Blockbuster ($100M+)" -> "Blockbuster")
    user_tier = user_scale.split(" (")[0] if user_scale else ""
    title_tier = title_scale.split(" (")[0] if title_scale else ""

    # Exact match only
    return user_tier == title_tier


def find_comparable_titles(user_attrs: dict, titles: list, limit: int = 5) -> list:
    """
    Find top N most similar titles from database.

    Args:
        user_attrs: Dict with keys: genre, scale, vfx, action, period, star_power
        titles: List of title dicts from database
        limit: Max number of results to return

    Returns:
        List of dicts with keys: title, score, reasons
    """
    user_scale = user_attrs.get("scale", "")

    scored = []
    for title in titles:
        # HARD FILTER: Scale must be within ±1 tier
        title_scale = title.get("computed_scale", "")
        if not filter_by_scale(user_scale, title_scale):
            continue

        score, reasons = compute_similarity(user_attrs, title)
        if score > 0:  # Only include titles with some match
            scored.append({
                "title": title,
                "score": score,
                "reasons": reasons
            })

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]
