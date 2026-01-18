#!/usr/bin/env python3
"""
Add curated TV shows to the titles database.

Uses the hand-picked list in tv_shows.json with known per-episode budgets.
Fetches details from TMDb and adds budget data from our curated list.

Usage:
    python scripts/add_tv_shows.py
"""

import os
import sys
import json
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from api.tmdb import TMDbClient, get_poster_url, get_profile_url
from api.attributes import compute_all_attributes

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
TV_SHOWS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tv_shows.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "titles_db.json")


def format_currency(amount: int) -> str:
    """Format budget as readable currency."""
    if not amount:
        return None
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.0f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:,}"


def get_tv_details_with_budget(client: TMDbClient, tmdb_id: int, budget_per_episode: int, notes: str) -> dict:
    """Fetch TV show details and add curated budget data."""
    try:
        # Get TMDb data
        tmdb_data = client.get_tv_details(tmdb_id)
        credits = client.get_tv_credits(tmdb_id)
    except Exception as e:
        print(f"  Error fetching TMDb data: {e}")
        return None

    if not tmdb_data:
        return None

    # Extract cast
    cast_list = credits.get("cast", [])[:10] if credits else []
    cast = [
        {
            "name": person.get("name"),
            "character": person.get("character"),
            "profile_url": get_profile_url(person.get("profile_path")),
        }
        for person in cast_list
    ]

    # Extract crew
    crew = credits.get("crew", []) if credits else []
    directors = [p["name"] for p in crew if p.get("job") == "Director"][:3]
    writers = [p["name"] for p in crew if p.get("job") in ("Writer", "Screenplay")][:5]
    producers = [p["name"] for p in crew if "Producer" in (p.get("job") or "")][:3]

    # Calculate total budget estimate (per episode * episodes in first season or average)
    num_episodes = tmdb_data.get("number_of_episodes", 10)
    total_budget_estimate = budget_per_episode * min(num_episodes, 20)  # Cap at 20 episodes

    result = {
        "title": tmdb_data.get("name"),
        "original_title": tmdb_data.get("original_name"),
        "overview": tmdb_data.get("overview"),
        "poster_url": get_poster_url(tmdb_data.get("poster_path")),
        "release_date": tmdb_data.get("first_air_date"),
        "genres": [g["name"] for g in tmdb_data.get("genres", [])],
        "runtime": tmdb_data.get("episode_run_time", [60])[0] if tmdb_data.get("episode_run_time") else 60,
        "status": tmdb_data.get("status"),
        "original_language": tmdb_data.get("original_language"),
        "production_countries": [c["name"] for c in tmdb_data.get("production_countries", [])],
        "production_companies": [c["name"] for c in tmdb_data.get("production_companies", [])],
        "media_type": "tv",
        "tmdb_id": tmdb_id,

        # Budget - per episode (curated)
        "budget": f"{format_currency(budget_per_episode)}/ep",
        "budget_raw": budget_per_episode,  # Per episode for consistency
        "budget_source": f"Curated ({notes})",
        "budget_source_url": None,
        "budget_notes": f"Per episode: {format_currency(budget_per_episode)}. Est. total: {format_currency(total_budget_estimate)}",
        "tmdb_url": f"https://www.themoviedb.org/tv/{tmdb_id}",

        # TV specific
        "number_of_seasons": tmdb_data.get("number_of_seasons"),
        "number_of_episodes": num_episodes,
        "networks": [n["name"] for n in tmdb_data.get("networks", [])],
        "created_by": [c["name"] for c in tmdb_data.get("created_by", [])],

        # Ratings
        "vote_average": tmdb_data.get("vote_average"),
        "vote_count": tmdb_data.get("vote_count"),

        # Crew
        "directors": directors,
        "writers": writers,
        "producers": producers,
        "composers": [],
        "cinematographers": [],
        "cast": cast,

        # No revenue for TV
        "revenue": None,
        "revenue_raw": None,
    }

    # Compute attributes
    crew_jobs = [p.get("job") for p in crew if p.get("job")]
    computed = compute_all_attributes(result, crew_jobs)
    result.update({
        "computed_period": computed["period"],
        "computed_vfx": computed["vfx"],
        "computed_action": computed["action"],
        "computed_scale": computed["scale"],
        "computed_star_power": computed["star_power"],
    })

    return result


def main():
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("ERROR: TMDB_API_KEY not found in environment")
        sys.exit(1)

    client = TMDbClient(api_key)

    # Load TV shows list
    with open(TV_SHOWS_FILE, "r") as f:
        tv_data = json.load(f)

    shows = tv_data.get("shows", [])
    print(f"Found {len(shows)} TV shows to add")

    # Load existing database
    existing_db = {"version": "1.0", "titles": []}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            existing_db = json.load(f)

    existing_ids = {t.get("tmdb_id") for t in existing_db.get("titles", [])}
    print(f"Existing database has {len(existing_ids)} titles")

    all_titles = list(existing_db.get("titles", []))
    added = 0
    skipped = 0
    errors = 0

    print("\nAdding TV shows...")
    print("=" * 60)

    for show in shows:
        name = show["name"]
        tmdb_id = show["tmdb_id"]
        budget = show["budget_per_episode"]
        notes = show.get("notes", "")

        if tmdb_id in existing_ids:
            print(f"  Skipping {name} (already in database)")
            skipped += 1
            continue

        time.sleep(0.25)  # Rate limiting

        details = get_tv_details_with_budget(client, tmdb_id, budget, notes)
        if details:
            all_titles.append(details)
            existing_ids.add(tmdb_id)
            added += 1
            print(f"  Added: {name} - {format_currency(budget)}/episode")
        else:
            errors += 1
            print(f"  Failed: {name}")

    # Save database
    output_db = {
        "version": "1.0",
        "last_updated": existing_db.get("last_updated"),
        "titles": all_titles,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_db, f, indent=2)

    print("\n" + "=" * 60)
    print(f"DONE!")
    print(f"  TV shows added: {added}")
    print(f"  Skipped (already exists): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total titles in database: {len(all_titles)}")


if __name__ == "__main__":
    main()
