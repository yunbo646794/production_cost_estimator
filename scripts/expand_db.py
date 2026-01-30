#!/usr/bin/env python3
"""
Expand titles_db.json to ~10,000 movies with good genre coverage.

Fetches movies from 2019-2024 (last 6 years) across all major genres.
Ensures budget data is available (TMDb + Wikipedia fallback).

Usage:
    python scripts/expand_db.py

Environment:
    TMDB_API_KEY must be set in .env file
"""

import os
import sys
import json
import time
from datetime import datetime
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from api.tmdb import TMDbClient
from api.merged import get_merged_details

load_dotenv()

# Configuration
START_YEAR = 2019       # Last 6 years per industry standard
END_YEAR = 2024
TARGET_TOTAL = 5000     # Target ~5,000 titles
RATE_LIMIT_DELAY = 0.15  # Seconds between API calls (TMDb allows ~40/sec)
MIN_VOTE_COUNT = 10     # Low threshold to include indie films

# TMDb genre IDs for good coverage
GENRES = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western",
}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "titles_db.json")


def discover_movies(client: TMDbClient, year: int, genre_id: int = None, page: int = 1) -> list:
    """Discover movies with optional genre filter."""
    params = {
        "sort_by": "popularity.desc",
        "primary_release_year": year,
        "page": page,
        "vote_count.gte": MIN_VOTE_COUNT,
    }
    if genre_id:
        params["with_genres"] = genre_id

    data = client._get("/discover/movie", params)
    return data.get("results", []), data.get("total_pages", 0)


def main():
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("ERROR: TMDB_API_KEY not found in environment")
        sys.exit(1)

    client = TMDbClient(api_key)

    # Load existing database
    existing_db = {"version": "1.0", "titles": []}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            existing_db = json.load(f)

    existing_ids = {t.get("tmdb_id") for t in existing_db.get("titles", [])}
    all_titles = list(existing_db.get("titles", []))

    print(f"Existing database: {len(existing_ids)} titles")
    print(f"Target: {TARGET_TOTAL} titles")
    print(f"Years: {START_YEAR}-{END_YEAR}")
    print("=" * 60)

    # Track stats
    new_count = 0
    skipped_no_budget = 0
    skipped_duplicate = 0
    errors = 0
    genre_counts = defaultdict(int)

    # Calculate targets
    years = list(range(START_YEAR, END_YEAR + 1))
    titles_needed = TARGET_TOTAL - len(existing_ids)
    titles_per_year = max(100, titles_needed // len(years))

    print(f"Need {titles_needed} more titles (~{titles_per_year}/year)")
    print("=" * 60)

    for year in years:
        year_count = 0
        year_target = titles_per_year
        print(f"\n{year}: targeting {year_target} titles")

        # First pass: fetch without genre filter (most popular)
        for page in range(1, 50):  # Up to 50 pages = 1000 movies
            if year_count >= year_target:
                break

            try:
                movies, total_pages = discover_movies(client, year, page=page)
                if not movies or page > total_pages:
                    break

                for movie in movies:
                    if year_count >= year_target:
                        break

                    tmdb_id = movie.get("id")
                    if tmdb_id in existing_ids:
                        skipped_duplicate += 1
                        continue

                    time.sleep(RATE_LIMIT_DELAY)

                    try:
                        details, errs = get_merged_details(client, tmdb_id, "movie", skip_wikipedia=False)
                        if details and details.get("budget_raw") and details["budget_raw"] > 0:
                            all_titles.append(details)
                            existing_ids.add(tmdb_id)
                            year_count += 1
                            new_count += 1

                            # Track genre
                            for g in details.get("genres", []):
                                genre_counts[g] += 1

                            if new_count % 25 == 0:
                                print(f"  Added {new_count} titles total ({len(all_titles)} in DB)")
                                # Save periodically
                                save_db(all_titles, OUTPUT_FILE)
                        else:
                            skipped_no_budget += 1
                    except Exception as e:
                        errors += 1

            except Exception as e:
                print(f"  Error on page {page}: {e}")
                errors += 1

        print(f"  {year}: added {year_count} titles")

        # Check if we've reached target
        if len(all_titles) >= TARGET_TOTAL:
            print(f"\nReached target of {TARGET_TOTAL} titles!")
            break

    # Final save
    save_db(all_titles, OUTPUT_FILE)

    print("\n" + "=" * 60)
    print("DONE!")
    print(f"  New titles added: {new_count}")
    print(f"  Skipped (no budget): {skipped_no_budget}")
    print(f"  Skipped (duplicate): {skipped_duplicate}")
    print(f"  Errors: {errors}")
    print(f"  Total titles in database: {len(all_titles)}")
    print(f"\nGenre distribution:")
    for genre, count in sorted(genre_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"    {genre}: {count}")


def save_db(titles: list, path: str):
    """Save database to file."""
    output_db = {
        "version": "1.0",
        "last_updated": datetime.now().isoformat(),
        "titles": titles,
    }
    with open(path, "w") as f:
        json.dump(output_db, f, indent=2)


if __name__ == "__main__":
    main()
