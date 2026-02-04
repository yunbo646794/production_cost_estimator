from .tmdb import TMDbClient, get_poster_url, get_profile_url, get_logo_url
from .wikipedia import get_budget_from_wikipedia
from .attributes import compute_all_attributes


def format_currency(amount: int) -> str:
    """Format budget/revenue as readable currency."""
    if amount is None or amount == 0:
        return None
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.0f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:,}"


def extract_crew(credits: dict) -> tuple[dict, list]:
    """Extract key crew members from credits and all job titles."""
    crew = credits.get("crew", [])
    result = {
        # Key Creative
        "directors": [],
        "writers": [],
        "producers": [],
        "composers": [],
        "cinematographers": [],
        # Production Design
        "production_designers": [],
        "art_directors": [],
        "set_decorators": [],
        "costume_designers": [],
        # Post-Production
        "editors": [],
        "sound_designers": [],
        # VFX & Stunts
        "vfx_supervisors": [],
        "stunt_coordinators": [],
        # Makeup
        "makeup_heads": [],
    }

    job_mapping = {
        # Key Creative
        "Director": "directors",
        "Writer": "writers",
        "Screenplay": "writers",
        "Producer": "producers",
        "Executive Producer": "producers",
        "Original Music Composer": "composers",
        "Director of Photography": "cinematographers",
        # Production Design
        "Production Designer": "production_designers",
        "Production Design": "production_designers",
        "Art Director": "art_directors",
        "Art Direction": "art_directors",
        "Set Decorator": "set_decorators",
        "Set Decoration": "set_decorators",
        "Costume Designer": "costume_designers",
        "Costume Design": "costume_designers",
        # Post-Production
        "Editor": "editors",
        "Film Editor": "editors",
        "Sound Designer": "sound_designers",
        "Supervising Sound Editor": "sound_designers",
        # VFX & Stunts
        "Visual Effects Supervisor": "vfx_supervisors",
        "VFX Supervisor": "vfx_supervisors",
        "Stunt Coordinator": "stunt_coordinators",
        # Makeup
        "Makeup Department Head": "makeup_heads",
        "Makeup Designer": "makeup_heads",
    }

    all_jobs = []
    for person in crew:
        job = person.get("job")
        if job:
            all_jobs.append(job)
        if job in job_mapping:
            key = job_mapping[job]
            name = person.get("name")
            if name and name not in result[key]:
                result[key].append(name)

    return result, all_jobs


def extract_cast(credits: dict, limit: int = 10) -> list:
    """Extract top cast members."""
    cast = credits.get("cast", [])[:limit]
    return [
        {
            "name": person.get("name"),
            "character": person.get("character"),
            "profile_url": get_profile_url(person.get("profile_path")),
        }
        for person in cast
    ]


def get_merged_details(
    tmdb_client: TMDbClient,
    tmdb_id: int,
    media_type: str,
    skip_wikipedia: bool = False,
) -> tuple[dict, list]:
    """
    Fetch movie/TV details from TMDb.
    Returns (data, errors) tuple.

    Args:
        skip_wikipedia: If True, skip Wikipedia fallback for faster processing.
    """
    errors = []
    tmdb_data = None
    credits = None

    # Fetch TMDb data
    try:
        if media_type == "movie":
            tmdb_data = tmdb_client.get_movie_details(tmdb_id)
            credits = tmdb_client.get_movie_credits(tmdb_id)
        else:  # tv
            tmdb_data = tmdb_client.get_tv_details(tmdb_id)
            credits = tmdb_client.get_tv_credits(tmdb_id)
    except Exception as e:
        errors.append(f"TMDb error: {str(e)}")

    if not tmdb_data:
        return None, errors

    # Extract crew and cast
    crew, crew_jobs = extract_crew(credits) if credits else ({}, [])
    cast = extract_cast(credits) if credits else []

    # Build result
    is_movie = media_type == "movie"
    title = tmdb_data.get("title") if is_movie else tmdb_data.get("name")
    release_date = tmdb_data.get("release_date") if is_movie else tmdb_data.get("first_air_date")
    year = release_date[:4] if release_date else None

    # URLs for sources
    tmdb_url = f"https://www.themoviedb.org/{media_type}/{tmdb_id}"
    budget_source_url = None

    # Get budget from TMDb
    budget = tmdb_data.get("budget") if is_movie else None
    budget_formatted = format_currency(budget)
    budget_source = "TMDb" if budget else None
    if budget:
        budget_source_url = tmdb_url

    # Fallback to Wikipedia if TMDb budget is missing (unless skipped)
    if is_movie and not budget and not skip_wikipedia:
        try:
            wiki_data = get_budget_from_wikipedia(title, year)
            if wiki_data.get("budget_raw"):
                budget = wiki_data["budget_raw"]
                budget_formatted = wiki_data["budget"]
                budget_source = "Wikipedia"
                budget_source_url = wiki_data.get("url")
        except Exception:
            pass  # Silently fail Wikipedia lookup

    # Extract collection/franchise info
    collection = tmdb_data.get("belongs_to_collection")
    collection_name = collection.get("name") if collection else None
    collection_id = collection.get("id") if collection else None

    result = {
        # Basic info
        "title": title,
        "original_title": tmdb_data.get("original_title") if is_movie else tmdb_data.get("original_name"),
        "overview": tmdb_data.get("overview"),
        "tagline": tmdb_data.get("tagline"),
        "homepage": tmdb_data.get("homepage"),
        "poster_url": get_poster_url(tmdb_data.get("poster_path")),
        "release_date": release_date,
        "genres": [g["name"] for g in tmdb_data.get("genres", [])],
        "runtime": tmdb_data.get("runtime") if is_movie else (tmdb_data.get("episode_run_time", [None])[0] if tmdb_data.get("episode_run_time") else None),
        "status": tmdb_data.get("status"),
        "original_language": tmdb_data.get("original_language"),
        "spoken_languages": [lang["english_name"] for lang in tmdb_data.get("spoken_languages", [])],
        "production_countries": [c["name"] for c in tmdb_data.get("production_countries", [])],
        "production_companies": [c["name"] for c in tmdb_data.get("production_companies", [])],
        "production_companies_full": [
            {
                "name": c["name"],
                "logo_url": get_logo_url(c.get("logo_path")),
                "origin_country": c.get("origin_country"),
            }
            for c in tmdb_data.get("production_companies", [])
        ],
        "media_type": media_type,
        "tmdb_id": tmdb_id,

        # Franchise/Collection (movies only)
        "collection": collection_name,
        "collection_id": collection_id,

        # Financials (movies only)
        "budget": budget_formatted,
        "revenue": format_currency(tmdb_data.get("revenue")) if is_movie else None,
        "budget_raw": budget,
        "revenue_raw": tmdb_data.get("revenue") if is_movie else None,
        "budget_source": budget_source,
        "budget_source_url": budget_source_url,
        "tmdb_url": tmdb_url,

        # Ratings (TMDb)
        "vote_average": tmdb_data.get("vote_average"),
        "vote_count": tmdb_data.get("vote_count"),

        # TV specific
        "number_of_seasons": tmdb_data.get("number_of_seasons") if not is_movie else None,
        "number_of_episodes": tmdb_data.get("number_of_episodes") if not is_movie else None,
        "networks": [n["name"] for n in tmdb_data.get("networks", [])] if not is_movie else None,
        "created_by": [c["name"] for c in tmdb_data.get("created_by", [])] if not is_movie else None,

        # Key Creative Crew
        "directors": crew.get("directors", []),
        "writers": crew.get("writers", []),
        "producers": crew.get("producers", [])[:3],
        "composers": crew.get("composers", []),
        "cinematographers": crew.get("cinematographers", []),

        # Production Design Crew
        "production_designers": crew.get("production_designers", []),
        "art_directors": crew.get("art_directors", []),
        "set_decorators": crew.get("set_decorators", []),
        "costume_designers": crew.get("costume_designers", []),
        "makeup_heads": crew.get("makeup_heads", []),

        # Post-Production Crew
        "editors": crew.get("editors", []),
        "sound_designers": crew.get("sound_designers", []),

        # VFX & Stunts Crew
        "vfx_supervisors": crew.get("vfx_supervisors", []),
        "stunt_coordinators": crew.get("stunt_coordinators", []),

        # Cast
        "cast": cast,
    }

    # Compute auto-detected attributes
    computed = compute_all_attributes(result, crew_jobs)
    result.update({
        "computed_period": computed["period"],
        "computed_vfx": computed["vfx"],
        "computed_action": computed["action"],
        "computed_scale": computed["scale"],
        "computed_star_power": computed["star_power"],
    })

    return result, errors
