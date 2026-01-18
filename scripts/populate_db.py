#!/usr/bin/env python3
"""
Populate titles_db.json with movies from TMDb.

Fetches popular movies with budget data for years 2015-2024.
Uses the existing API infrastructure to get full details.

Usage:
    python scripts/populate_db.py

Environment:
    TMDB_API_KEY must be set in .env file
"""

import os
import sys
import json
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from api.tmdb import TMDbClient
from api.merged import get_merged_details

load_dotenv()

# Configuration - adjust these for testing vs production
START_YEAR = 2015       # 10 years of data
END_YEAR = 2024
MOVIES_PER_YEAR = 100   # Target ~1000 total titles
MAX_PAGES_PER_YEAR = 10  # TMDb returns 20 results per page
RATE_LIMIT_DELAY = 0.25  # Seconds between API calls to avoid rate limiting
MIN_VOTE_COUNT = 20     # Lowered from 100 to include more indie films

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "titles_db.json")


def discover_movies_by_year(client: TMDbClient, year: int, page: int = 1) -> list:
    """
    Discover popular movies from a specific year.
    Uses TMDb discover endpoint with filters.
    """
    params = {
        "sort_by": "popularity.desc",
        "primary_release_year": year,
        "page": page,
        "vote_count.gte": MIN_VOTE_COUNT,  # Lowered to include more indie films
        "with_original_language": "en",  # English language films (tend to have budget data)
    }
    data = client._get("/discover/movie", params)
    return data.get("results", [])


def main():
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("ERROR: TMDB_API_KEY not found in environment")
        sys.exit(1)

    client = TMDbClient(api_key)

    # Load existing database to preserve any manually added titles
    existing_db = {"version": "1.0", "titles": []}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            existing_db = json.load(f)

    # Track existing TMDb IDs to avoid duplicates
    existing_ids = {t.get("tmdb_id") for t in existing_db.get("titles", [])}
    print(f"Existing database has {len(existing_ids)} titles")

    all_titles = list(existing_db.get("titles", []))
    new_count = 0
    skipped_no_budget = 0
    errors = 0

    print(f"\nFetching movies from {START_YEAR} to {END_YEAR}...")
    print("=" * 60)

    for year in range(START_YEAR, END_YEAR + 1):
        year_titles = 0
        print(f"\n{year}:", end=" ")

        for page in range(1, MAX_PAGES_PER_YEAR + 1):
            if year_titles >= MOVIES_PER_YEAR:
                break

            try:
                movies = discover_movies_by_year(client, year, page)
                if not movies:
                    break

                for movie in movies:
                    if year_titles >= MOVIES_PER_YEAR:
                        break

                    tmdb_id = movie.get("id")
                    if tmdb_id in existing_ids:
                        continue

                    # Get full details
                    time.sleep(RATE_LIMIT_DELAY)
                    try:
                        details, errs = get_merged_details(client, tmdb_id, "movie")
                        if details and details.get("budget_raw") and details["budget_raw"] > 0:
                            all_titles.append(details)
                            existing_ids.add(tmdb_id)
                            year_titles += 1
                            new_count += 1
                            print(".", end="", flush=True)
                        else:
                            skipped_no_budget += 1
                    except Exception as e:
                        errors += 1

            except Exception as e:
                print(f"\nError fetching page {page} for {year}: {e}")
                errors += 1

        print(f" ({year_titles} titles)")

    # Save updated database
    output_db = {
        "version": "1.0",
        "last_updated": datetime.now().isoformat(),
        "titles": all_titles,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_db, f, indent=2)

    print("\n" + "=" * 60)
    print(f"DONE!")
    print(f"  New titles added: {new_count}")
    print(f"  Skipped (no budget): {skipped_no_budget}")
    print(f"  Errors: {errors}")
    print(f"  Total titles in database: {len(all_titles)}")
    print(f"  Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
