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


def get_distance_score(attr: str, val1: str, val2: str) -> float:
    """
    Get a distance-based score for attribute matching.
    Returns: 1.0 for exact match, 0.6 for 1 step away, 0.3 for 2 steps, 0 otherwise.
    """
    if val1 == val2:
        return 1.0

    if attr not in ADJACENCY:
        return 0.0

    order = ADJACENCY[attr]
    try:
        idx1 = order.index(val1)
        idx2 = order.index(val2)
        distance = abs(idx1 - idx2)
        if distance == 1:
            return 0.6  # Adjacent
        elif distance == 2:
            return 0.3  # Two steps away
        else:
            return 0.0  # Too far
    except ValueError:
        return 0.0


def is_adjacent(attr: str, val1: str, val2: str) -> bool:
    """Check if two attribute values are adjacent in their scale."""
    return get_distance_score(attr, val1, val2) >= 0.6


def compute_similarity(user_attrs: dict, title: dict) -> tuple[float, list]:
    """
    Compute similarity score between user-selected attributes and a database title.
    Returns (score 0-100, list of matching reasons).

    Improved algorithm with:
    - Distance-based partial scoring (not just 0/50/100)
    - Recency bonus for newer titles within the window
    - Genre partial matching for related genres
    """
    score = 0
    reasons = []

    # Attribute weights (total base = 100, with up to 10 bonus points)
    weights = {
        "genre": 25,      # Primary genre match
        "scale": 20,      # Budget scale match
        "vfx": 15,        # VFX intensity match
        "action": 15,     # Action complexity match
        "period": 15,     # Period/era match
        "star_power": 10, # Star power match
    }

    # Genre matching (with partial credit for related genres)
    user_genre = user_attrs.get("genre", "")
    title_genres = title.get("genres", [])
    if matches_genre(user_genre, title_genres):
        score += weights["genre"]
        if title_genres:
            reasons.append(f"Genre: {title_genres[0]}")
    elif title_genres:
        # Partial credit for related genres
        related_bonus = 0
        if user_genre == "Action/Adventure" and any(g in ["Thriller", "Science Fiction"] for g in title_genres):
            related_bonus = weights["genre"] * 0.4
        elif user_genre == "Drama" and any(g in ["Romance", "Crime"] for g in title_genres):
            related_bonus = weights["genre"] * 0.4
        elif user_genre == "Horror/Thriller" and any(g in ["Mystery", "Crime"] for g in title_genres):
            related_bonus = weights["genre"] * 0.4
        elif user_genre == "Sci-Fi/Fantasy" and any(g in ["Adventure", "Action"] for g in title_genres):
            related_bonus = weights["genre"] * 0.4
        score += related_bonus

    # Scale matching (exact or adjacent tier)
    scale_score = match_scale(user_attrs.get("scale", ""), title.get("computed_scale", ""))
    score += scale_score * weights["scale"] / 100
    if scale_score >= 50:
        scale_display = title.get("computed_scale", "N/A").split(" (")[0]
        reasons.append(f"Scale: {scale_display}")

    # Other attributes with distance-based scoring
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
            distance_multiplier = get_distance_score(attr, user_val, title_val)
            score += weights[attr] * distance_multiplier
            if distance_multiplier == 1.0:
                reasons.append(f"{attr.replace('_', ' ').title()}: {title_val}")
            elif distance_multiplier >= 0.6:
                reasons.append(f"{attr.replace('_', ' ').title()}: ~{title_val}")

    # Recency bonus (up to 5 extra points for very recent titles)
    release_date = title.get("release_date", "")
    if release_date and len(release_date) >= 4:
        try:
            from datetime import datetime
            year = int(release_date[:4])
            current_year = datetime.now().year
            years_old = current_year - year
            if years_old <= 1:
                score += 5  # Released this year or last year
            elif years_old <= 2:
                score += 3  # 2 years old
            elif years_old <= 3:
                score += 1  # 3 years old
        except ValueError:
            pass

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


def get_title_year(title: dict) -> int:
    """Extract release year from title."""
    release_date = title.get("release_date", "")
    if release_date and len(release_date) >= 4:
        try:
            return int(release_date[:4])
        except ValueError:
            pass
    return 0


def find_comparable_titles(user_attrs: dict, titles: list, limit: int = 5, max_years: int = 6) -> list:
    """
    Find top N most similar titles from database.

    Args:
        user_attrs: Dict with keys: genre, scale, vfx, action, period, star_power
        titles: List of title dicts from database
        limit: Max number of results to return
        max_years: Only include titles from the last N years (default 6, per industry standard)

    Returns:
        List of dicts with keys: title, score, reasons
    """
    from datetime import datetime
    current_year = datetime.now().year
    min_year = current_year - max_years  # e.g., 2024 - 6 = 2018, so 2019+ included

    user_scale = user_attrs.get("scale", "")

    scored = []
    for title in titles:
        # HARD FILTER 1: Only titles from last 6 years
        title_year = get_title_year(title)
        if title_year < min_year:
            continue

        # HARD FILTER 2: Scale must match exact tier
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
