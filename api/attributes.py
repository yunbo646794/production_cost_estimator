"""
Attribute auto-detection for Production Cost Estimator.
Computes 5 attributes from TMDb movie data.
"""
import os
import json

# Load tier data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_actor_tiers():
    with open(os.path.join(DATA_DIR, "actor_tiers.json")) as f:
        return json.load(f)


def load_studio_tiers():
    with open(os.path.join(DATA_DIR, "studio_tiers.json")) as f:
        return json.load(f)


def detect_period_era(overview: str, title: str = "") -> str:
    """Detect period setting from overview text and title."""
    text = ((overview or "") + " " + (title or "")).lower()

    if not text.strip():
        return "Contemporary"

    # Historical (pre-1900)
    historical = ["medieval", "ancient", "victorian", "1800s", "civil war",
                  "renaissance", "roman empire", "greek", "egyptian", "colonial",
                  "18th century", "17th century", "16th century",
                  "gladiator", "emperor", "rome", "roman", "viking", "samurai",
                  "pirate", "musketeer", "napoleon", "revolution"]
    if any(kw in text for kw in historical):
        return "Historical (pre-1900)"

    # Period (1900-1980)
    period = ["world war", "wwi", "wwii", "1920s", "1930s", "1940s", "1950s",
              "1960s", "1970s", "prohibition", "vietnam", "great depression",
              "titanic", "1912", "1910s", "holocaust", "nazi"]
    if any(kw in text for kw in period):
        return "Period (1900-1980)"

    # Recent Past (1980-2010)
    recent = ["1980s", "1990s", "2000s", "cold war", "berlin wall", " 80s", " 90s"]
    if any(kw in text for kw in recent):
        return "Recent Past (1980-2010)"

    # Futuristic
    future = ["future", "2100", "space station", "dystopia", "cyberpunk",
              "post-apocalyptic", "year 20", "ai uprising", "android",
              "spaceship", "interstellar", "galaxy", "alien planet"]
    if any(kw in text for kw in future):
        return "Futuristic"

    return "Contemporary"


def detect_vfx_intensity(genres: list, budget_raw: int) -> str:
    """Detect VFX intensity from genres and budget."""
    genre_set = set(g.lower() for g in (genres or []))
    budget = budget_raw or 0

    # Animation is always Heavy (100% VFX)
    if "animation" in genre_set:
        return "Heavy"

    heavy_genres = {"science fiction", "fantasy"}
    moderate_genres = {"action", "adventure"}
    practical_genres = {"horror", "thriller"}

    if genre_set & heavy_genres and budget >= 100_000_000:
        return "Heavy"
    if genre_set & heavy_genres or genre_set & moderate_genres:
        return "Moderate"
    if genre_set & practical_genres or budget < 10_000_000:
        return "Practical Only"
    return "Light"


def detect_action_complexity(genres: list, crew_jobs: list) -> str:
    """Detect action complexity from genre and crew."""
    genre_set = set(g.lower() for g in (genres or []))
    jobs = set(j.lower() for j in (crew_jobs or []))

    action_genres = {"action", "adventure", "war"}
    stunt_jobs = {"stunt coordinator", "stunt double", "fight choreographer"}

    has_action_genre = bool(genre_set & action_genres)
    has_stunt_crew = bool(jobs & stunt_jobs)

    if has_action_genre and has_stunt_crew:
        return "High"
    if has_action_genre or has_stunt_crew:
        return "Moderate"
    if genre_set & {"drama", "comedy", "romance"}:
        return "Dialogue-Driven"
    return "Light"


def detect_production_scale(companies: list, budget_raw: int) -> str:
    """Detect production scale from actual budget only."""
    budget = budget_raw or 0

    if budget >= 100_000_000:
        return "Blockbuster ($100M+)"
    if budget >= 50_000_000:
        return "Major Studio ($50-100M)"
    if budget >= 20_000_000:
        return "Mid-Budget ($20-50M)"
    if budget >= 5_000_000:
        return "Indie ($5-20M)"
    if budget > 0:
        return "Micro (<$5M)"
    return "Unknown"  # No budget data available


def detect_star_power(cast_names: list) -> str:
    """Detect star power from cast names."""
    tiers = load_actor_tiers()["tiers"]
    a_list = set(tiers["A-List"]["actors"])
    b_list = set(tiers["B-List"]["actors"])

    top_cast = (cast_names or [])[:5]

    if any(name in a_list for name in top_cast[:3]):
        return "A-List"
    if any(name in b_list for name in top_cast):
        return "B-List"
    if top_cast:
        return "Rising Stars"
    return "Ensemble/Unknown"


def compute_all_attributes(data: dict, crew_jobs: list = None) -> dict:
    """Compute all 5 auto-detectable attributes."""
    cast_names = [c["name"] for c in data.get("cast", [])]

    return {
        "period": detect_period_era(data.get("overview"), data.get("title")),
        "vfx": detect_vfx_intensity(data.get("genres"), data.get("budget_raw")),
        "action": detect_action_complexity(data.get("genres"), crew_jobs),
        "scale": detect_production_scale(data.get("production_companies"), data.get("budget_raw")),
        "star_power": detect_star_power(cast_names),
    }
