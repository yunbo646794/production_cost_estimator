from .tmdb import TMDbClient, get_poster_url, get_profile_url


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


def extract_crew(credits: dict) -> dict:
    """Extract key crew members from credits."""
    crew = credits.get("crew", [])
    result = {
        "directors": [],
        "writers": [],
        "producers": [],
        "composers": [],
        "cinematographers": [],
    }

    job_mapping = {
        "Director": "directors",
        "Writer": "writers",
        "Screenplay": "writers",
        "Producer": "producers",
        "Executive Producer": "producers",
        "Original Music Composer": "composers",
        "Director of Photography": "cinematographers",
    }

    for person in crew:
        job = person.get("job")
        if job in job_mapping:
            key = job_mapping[job]
            name = person.get("name")
            if name and name not in result[key]:
                result[key].append(name)

    return result


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
) -> tuple[dict, list]:
    """
    Fetch movie/TV details from TMDb.
    Returns (data, errors) tuple.
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
    crew = extract_crew(credits) if credits else {}
    cast = extract_cast(credits) if credits else []

    # Build result
    is_movie = media_type == "movie"

    result = {
        # Basic info
        "title": tmdb_data.get("title") if is_movie else tmdb_data.get("name"),
        "original_title": tmdb_data.get("original_title") if is_movie else tmdb_data.get("original_name"),
        "overview": tmdb_data.get("overview"),
        "poster_url": get_poster_url(tmdb_data.get("poster_path")),
        "release_date": tmdb_data.get("release_date") if is_movie else tmdb_data.get("first_air_date"),
        "genres": [g["name"] for g in tmdb_data.get("genres", [])],
        "runtime": tmdb_data.get("runtime") if is_movie else (tmdb_data.get("episode_run_time", [None])[0] if tmdb_data.get("episode_run_time") else None),
        "status": tmdb_data.get("status"),
        "original_language": tmdb_data.get("original_language"),
        "production_countries": [c["name"] for c in tmdb_data.get("production_countries", [])],
        "production_companies": [c["name"] for c in tmdb_data.get("production_companies", [])],
        "media_type": media_type,
        "tmdb_id": tmdb_id,

        # Financials (movies only)
        "budget": format_currency(tmdb_data.get("budget")) if is_movie else None,
        "revenue": format_currency(tmdb_data.get("revenue")) if is_movie else None,
        "budget_raw": tmdb_data.get("budget") if is_movie else None,
        "revenue_raw": tmdb_data.get("revenue") if is_movie else None,

        # Ratings (TMDb)
        "vote_average": tmdb_data.get("vote_average"),
        "vote_count": tmdb_data.get("vote_count"),

        # TV specific
        "number_of_seasons": tmdb_data.get("number_of_seasons") if not is_movie else None,
        "number_of_episodes": tmdb_data.get("number_of_episodes") if not is_movie else None,
        "networks": [n["name"] for n in tmdb_data.get("networks", [])] if not is_movie else None,
        "created_by": [c["name"] for c in tmdb_data.get("created_by", [])] if not is_movie else None,

        # Crew and cast
        "directors": crew.get("directors", []),
        "writers": crew.get("writers", []),
        "producers": crew.get("producers", [])[:3],
        "composers": crew.get("composers", []),
        "cinematographers": crew.get("cinematographers", []),
        "cast": cast,
    }

    return result, errors
