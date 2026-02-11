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
    "Horror": ["Horror"],
    "Thriller": ["Thriller"],
    "Sci-Fi/Fantasy": ["Science Fiction", "Fantasy"],
    "Romance": ["Romance"],
    "Documentary": ["Documentary"],
    "Kids/Family": ["Family", "Animation"],
}

# Scale tiers in order (for adjacency matching)
SCALE_TIERS = [
    "Blockbuster",
    "Major Studio",
    "Mid-Budget",
    "Low-Budget",
    "Ultra-Low",
    "Micro",
]

# Map new UI scale names to old DB names for backward compatibility
SCALE_NAME_MAP = {
    "Low-Budget": "Indie",      # New UI name -> Old DB name
    "Ultra-Low": "Micro",       # UI "Ultra-Low ($2.5-5M)" -> DB "Micro (<$5M)"
}

# Attribute adjacency for partial matching
ADJACENCY = {
    "vfx": ["Heavy", "Moderate", "Light", "Practical Only"],
    "action": ["High", "Moderate", "Light", "Dialogue-Driven"],
    "period": ["Futuristic", "Contemporary", "Recent Past (1980-2010)", "Period (1900-1980)", "Historical (pre-1900)"],
    "star_power": ["A-List", "A-List Cusp", "B-List", "Rising Stars", "Ensemble/Unknown"],
}

# Country mapping from dropdown options to TMDb production country names
COUNTRY_MAP = {
    "USA": ["United States of America"],
    "Canada": ["Canada"],
    "UK/Ireland": ["United Kingdom", "Ireland"],
    "Australia/New Zealand": ["Australia", "New Zealand"],
    "LATAM": ["Mexico", "Brazil", "Argentina", "Chile", "Colombia", "Peru", "Venezuela", "Ecuador", "Bolivia", "Paraguay", "Uruguay", "Cuba", "Dominican Republic", "Puerto Rico", "Costa Rica", "Panama", "Guatemala", "Honduras", "El Salvador", "Nicaragua"],
    "Europe": ["France", "Germany", "Spain", "Italy", "Belgium", "Netherlands", "Sweden", "Norway", "Denmark", "Finland", "Austria", "Switzerland", "Poland", "Czech Republic", "Hungary", "Romania", "Portugal", "Greece", "Russia", "Ukraine"],
    "Asia": [],  # Catch-all for non-Western
}

# Runtime tier boundaries (minutes)
RUNTIME_TIERS = {
    "15 min": (0, 22),
    "30 min": (22, 45),
    "60 min": (45, 75),
    "90 min": (75, 105),
    "120 min": (105, 135),
    "150+ min": (135, 999),
}


def matches_genre(user_genres: list, title_genres: list) -> tuple[float, str]:
    """
    Check if user's selected genres match any of the title's genres.
    Returns (score 0.0-1.0, matched_genre_name or None).
    Supports multiple user genre selections.
    """
    if not title_genres or not user_genres:
        return 0.0, None

    # Check each user genre for matches
    for user_genre in user_genres:
        target_genres = GENRE_MAP.get(user_genre, [])
        for title_genre in title_genres:
            if title_genre in target_genres:
                return 1.0, title_genre

    # Check for related genres (partial match)
    related_map = {
        "Action/Adventure": ["Thriller", "Science Fiction", "War"],
        "Drama": ["Romance", "Crime", "History"],
        "Horror": ["Thriller", "Mystery"],
        "Thriller": ["Horror", "Mystery", "Crime"],
        "Sci-Fi/Fantasy": ["Adventure", "Action"],
        "Comedy": ["Romance"],
        "Romance": ["Drama", "Comedy"],
        "Kids/Family": ["Comedy", "Adventure", "Fantasy"],
    }

    for user_genre in user_genres:
        related = related_map.get(user_genre, [])
        for title_genre in title_genres:
            if title_genre in related:
                return 0.5, title_genre

    return 0.0, None


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

    # "Asia" matches anything not in the Western categories
    # Primary country (first listed) must be non-western
    if user_country == "Asia":
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
    english_speaking = {"United States of America", "United Kingdom", "Canada", "Australia", "New Zealand", "Ireland"}
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
    tier_order = ["15 min", "30 min", "60 min", "90 min", "120 min", "150+ min"]
    try:
        user_idx = tier_order.index(user_runtime)
        title_idx = tier_order.index(title_tier)
        distance = abs(user_idx - title_idx)
        if distance == 1:
            return 0.5
        elif distance == 2:
            return 0.25
    except ValueError:
        pass

    return 0.0


def compute_similarity(user_attrs: dict, title: dict) -> tuple[float, list]:
    """
    Compute similarity score between user-selected attributes and a database title.
    Returns (score 0-100, list of matching reasons).

    Uses percentage-based scoring where each attribute contributes weighted points
    toward a maximum. Score = (earned / max) * 100 for full 0-100 range usage.
    Scale is excluded since filter_by_scale() already enforces it as a hard filter.
    """
    earned = 0.0
    reasons = []

    # Weights per attribute (total max = 96, recency bonus can push to 100)
    weights = {
        "genre": 25,
        "vfx": 15,
        "action": 12,
        "period": 12,
        "star_power": 12,
        "country": 10,
        "runtime": 10,
    }
    max_points = sum(weights.values())  # 96

    # --- Genre matching (supports multi-select) ---
    user_genres = user_attrs.get("genres", [])
    title_genres = title.get("genres", [])
    genre_score, matched_genre = matches_genre(user_genres, title_genres)
    if genre_score == 1.0:
        earned += weights["genre"]
        if matched_genre:
            reasons.append(f"Genre: {matched_genre}")
    elif genre_score >= 0.5:
        earned += weights["genre"] * 0.5
        if matched_genre:
            reasons.append(f"Genre: ~{matched_genre}")

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
                earned += weights[attr]
                reasons.append(f"{attr.replace('_', ' ').title()}: {title_val}")
            elif dist >= 0.5:
                # Adjacent (1 step away): 60% credit
                earned += weights[attr] * 0.6
                reasons.append(f"{attr.replace('_', ' ').title()}: ~{title_val}")
            elif dist >= 0.3:
                # 2 steps away: 25% credit
                earned += weights[attr] * 0.25
            # else: mismatch or far, 0 points
        # else: no data, 0 points

    # --- Country matching ---
    user_country = user_attrs.get("country", "")
    title_countries = title.get("production_countries", [])
    if user_country:
        country_score = match_country(user_country, title_countries)
        if country_score == 1.0:
            earned += weights["country"]
            if title_countries:
                reasons.append(f"Country: {title_countries[0]}")
        elif country_score >= 0.3:
            earned += weights["country"] * 0.6

    # --- Runtime matching ---
    user_runtime = user_attrs.get("runtime", "")
    title_runtime = title.get("runtime")
    if user_runtime:
        runtime_score = match_runtime(user_runtime, title_runtime)
        if runtime_score == 1.0:
            earned += weights["runtime"]
            reasons.append(f"Runtime: {title_runtime}min")
        elif runtime_score >= 0.5:
            earned += weights["runtime"] * 0.6

    # Compute percentage score
    score = (earned / max_points) * 100

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
    score = max(0, min(100, round(score)))

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

    # Map new UI names to old DB names for compatibility
    user_tier = SCALE_NAME_MAP.get(user_tier, user_tier)

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
