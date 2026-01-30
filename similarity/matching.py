"""
Similarity matching engine for finding comparable titles.

Scoring uses a baseline + bonus/penalty system:
- Start at 50 (neutral)
- Matches add points, mismatches subtract
- Produces scores ranging ~30-100 for meaningful differentiation
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

# Country mapping from dropdown options to TMDb production country names
COUNTRY_MAP = {
    "USA (Hollywood)": ["United States of America"],
    "UK": ["United Kingdom"],
    "Canada/Australia": ["Canada", "Australia"],
    "Europe (non-UK)": ["France", "Germany", "Spain", "Italy", "Belgium", "Netherlands", "Sweden", "Norway", "Denmark", "Finland", "Ireland", "Austria", "Switzerland", "Poland", "Czech Republic", "Hungary", "Romania", "Portugal", "Greece"],
    "Asia/Other": [],  # Match anything not in above categories
}

# Runtime tier boundaries (minutes)
RUNTIME_TIERS = {
    "Short": (0, 90),
    "Standard": (90, 120),
    "Long": (120, 150),
    "Epic": (150, 999),
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


def match_country(user_country: str, title_countries: list) -> float:
    """
    Match production country.
    Returns 1.0 for match, 0.3 for partial (same region), 0.0 for mismatch.
    """
    if not title_countries:
        return 0.0

    expected = COUNTRY_MAP.get(user_country, [])

    # "Asia/Other" matches anything not in the Western categories
    # Primary country (first listed) must be non-western
    if user_country == "Asia/Other":
        western = set()
        for key, vals in COUNTRY_MAP.items():
            if key != "Asia/Other":
                western.update(vals)
        primary = title_countries[0]
        if primary not in western:
            return 1.0
        return 0.0

    # Exact region match (primary country must be in expected list)
    if title_countries[0] in expected:
        return 1.0

    # Any country in expected list = partial match
    if any(c in expected for c in title_countries):
        return 0.5

    # Partial: English-speaking countries are somewhat similar
    english_speaking = {"United States of America", "United Kingdom", "Canada", "Australia"}
    if expected and set(expected) & english_speaking and set(title_countries) & english_speaking:
        return 0.3

    return 0.0


def match_runtime(user_runtime: str, title_runtime) -> float:
    """
    Match runtime tier.
    Returns 1.0 for same tier, 0.5 for adjacent tier, 0.0 for far apart.
    """
    if not title_runtime or not user_runtime:
        return 0.0

    try:
        runtime_min = int(title_runtime)
    except (ValueError, TypeError):
        return 0.0

    # Determine title's tier
    title_tier = None
    for tier, (low, high) in RUNTIME_TIERS.items():
        if low <= runtime_min < high:
            title_tier = tier
            break

    if not title_tier:
        return 0.0

    if user_runtime == title_tier:
        return 1.0

    # Check adjacency
    tier_order = ["Short", "Standard", "Long", "Epic"]
    try:
        user_idx = tier_order.index(user_runtime)
        title_idx = tier_order.index(title_tier)
        if abs(user_idx - title_idx) == 1:
            return 0.5
    except ValueError:
        pass

    return 0.0


def compute_similarity(user_attrs: dict, title: dict) -> tuple[float, list]:
    """
    Compute similarity score between user-selected attributes and a database title.
    Returns (score 0-100, list of matching reasons).

    Uses baseline + bonus/penalty system for meaningful score differentiation:
    - Start at 50 (neutral baseline)
    - Matches add points (+bonus)
    - Mismatches subtract points (-penalty)
    - 8 scoring dimensions for wide spread
    """
    score = 50  # Neutral baseline
    reasons = []

    # Attribute weights: (bonus for match, penalty for mismatch)
    weights = {
        "genre":      {"bonus": 12, "penalty": -10},
        "scale":      {"bonus": 10, "penalty": -8},
        "vfx":        {"bonus": 6,  "penalty": -5},
        "action":     {"bonus": 6,  "penalty": -5},
        "period":     {"bonus": 6,  "penalty": -5},
        "star_power": {"bonus": 4,  "penalty": -3},
        "country":    {"bonus": 4,  "penalty": -3},
        "runtime":    {"bonus": 4,  "penalty": -3},
    }

    # --- Genre matching ---
    user_genre = user_attrs.get("genre", "")
    title_genres = title.get("genres", [])
    if matches_genre(user_genre, title_genres):
        score += weights["genre"]["bonus"]
        if title_genres:
            reasons.append(f"Genre: {title_genres[0]}")
    elif title_genres:
        related = False
        if user_genre == "Action/Adventure" and any(g in ["Thriller", "Science Fiction"] for g in title_genres):
            related = True
        elif user_genre == "Drama" and any(g in ["Romance", "Crime"] for g in title_genres):
            related = True
        elif user_genre == "Horror/Thriller" and any(g in ["Mystery", "Crime"] for g in title_genres):
            related = True
        elif user_genre == "Sci-Fi/Fantasy" and any(g in ["Adventure", "Action"] for g in title_genres):
            related = True

        if related:
            score += weights["genre"]["bonus"] * 0.3
            reasons.append(f"Genre: ~{title_genres[0]}")
        else:
            score += weights["genre"]["penalty"]
    else:
        score += weights["genre"]["penalty"]

    # --- Scale matching ---
    scale_score = match_scale(user_attrs.get("scale", ""), title.get("computed_scale", ""))
    if scale_score == 100:
        score += weights["scale"]["bonus"]
        scale_display = title.get("computed_scale", "N/A").split(" (")[0]
        reasons.append(f"Scale: {scale_display}")
    elif scale_score == 50:
        score += weights["scale"]["bonus"] * 0.3
        scale_display = title.get("computed_scale", "N/A").split(" (")[0]
        reasons.append(f"Scale: ~{scale_display}")
    else:
        score += weights["scale"]["penalty"]

    # --- Distance-based attributes (vfx, action, period, star_power) ---
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
            dist = get_distance_score(attr, user_val, title_val)
            if dist == 1.0:
                score += weights[attr]["bonus"]
                reasons.append(f"{attr.replace('_', ' ').title()}: {title_val}")
            elif dist >= 0.6:
                score += weights[attr]["bonus"] * 0.4
                reasons.append(f"{attr.replace('_', ' ').title()}: ~{title_val}")
            elif dist >= 0.3:
                score += weights[attr]["penalty"] * 0.4
            else:
                score += weights[attr]["penalty"]
        else:
            # No data - small penalty
            score += weights[attr]["penalty"] * 0.3

    # --- Country matching ---
    user_country = user_attrs.get("country", "")
    title_countries = title.get("production_countries", [])
    if user_country:
        country_score = match_country(user_country, title_countries)
        if country_score == 1.0:
            score += weights["country"]["bonus"]
            if title_countries:
                reasons.append(f"Country: {title_countries[0]}")
        elif country_score >= 0.3:
            score += weights["country"]["bonus"] * 0.3
        else:
            score += weights["country"]["penalty"]

    # --- Runtime matching ---
    user_runtime = user_attrs.get("runtime", "")
    title_runtime = title.get("runtime")
    if user_runtime:
        runtime_score = match_runtime(user_runtime, title_runtime)
        if runtime_score == 1.0:
            score += weights["runtime"]["bonus"]
            reasons.append(f"Runtime: {title_runtime}min")
        elif runtime_score >= 0.5:
            score += weights["runtime"]["bonus"] * 0.3
        else:
            score += weights["runtime"]["penalty"]

    # --- Recency bonus (up to 4 extra points) ---
    release_date = title.get("release_date", "")
    if release_date and len(release_date) >= 4:
        try:
            from datetime import datetime
            year = int(release_date[:4])
            current_year = datetime.now().year
            years_old = current_year - year
            if years_old <= 1:
                score += 4
            elif years_old <= 2:
                score += 2
            elif years_old <= 3:
                score += 1
        except ValueError:
            pass

    # Clamp to 0-100
    score = max(0, min(100, score))

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
