"""
Script to populate the titles database with popular movies across genres and budgets.
Run this once to seed the database for the Cost Estimator.
"""
import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from api import TMDbClient, get_merged_details

load_dotenv()

# Popular movies to seed the database (diverse genres, eras, budgets)
SEED_MOVIES = [
    # Blockbusters
    ("The Dark Knight", 155),
    ("Avatar", 19995),
    ("Avengers: Endgame", 299534),
    ("Titanic", 597),
    ("Jurassic Park", 329),
    ("The Lord of the Rings: The Return of the King", 122),
    ("Star Wars: The Force Awakens", 140607),
    ("Inception", 27205),
    ("The Matrix", 603),
    ("Gladiator", 98),

    # Mid-Budget
    ("The Shawshank Redemption", 278),
    ("Pulp Fiction", 680),
    ("Fight Club", 550),
    ("Forrest Gump", 13),
    ("The Silence of the Lambs", 274),
    ("Se7en", 807),
    ("Goodfellas", 769),
    ("The Departed", 1422),
    ("No Country for Old Men", 6977),
    ("There Will Be Blood", 7345),

    # Horror/Thriller (typically lower budget)
    ("Get Out", 419430),
    ("A Quiet Place", 447332),
    ("The Conjuring", 138843),
    ("It", 346364),
    ("Hereditary", 493559),
    ("Parasite", 496243),
    ("The Witch", 310131),
    ("Midsommar", 530385),

    # Comedy
    ("The Hangover", 18785),
    ("Bridesmaids", 65898),
    ("Superbad", 8363),
    ("Step Brothers", 12133),

    # Drama/Indie
    ("Moonlight", 376867),
    ("Lady Bird", 391713),
    ("The Florida Project", 399106),
    ("Manchester by the Sea", 334541),
    ("Whiplash", 244786),
    ("Room", 264644),

    # Sci-Fi
    ("Interstellar", 157336),
    ("Arrival", 329865),
    ("Blade Runner 2049", 335984),
    ("Ex Machina", 264660),
    ("Dune", 438631),

    # Animation
    ("Spider-Man: Into the Spider-Verse", 324857),
    ("Toy Story", 862),
    ("Finding Nemo", 12),
    ("Coco", 354912),
    ("The Lion King", 8587),
]

def populate_database():
    tmdb_key = os.getenv("TMDB_API_KEY")
    if not tmdb_key:
        print("Error: TMDB_API_KEY not found in environment")
        return

    tmdb = TMDbClient(tmdb_key)

    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "titles_db.json")

    # Load existing database
    try:
        with open(db_path, "r") as f:
            db = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        db = {"version": "1.0", "titles": []}

    existing_ids = [t.get("tmdb_id") for t in db["titles"]]
    added = 0
    skipped = 0

    print(f"Starting with {len(existing_ids)} existing titles...")

    for title, tmdb_id in SEED_MOVIES:
        if tmdb_id in existing_ids:
            print(f"  Skipping {title} (already in database)")
            skipped += 1
            continue

        try:
            data, errors = get_merged_details(tmdb, tmdb_id, "movie")
            if data:
                db["titles"].append(data)
                existing_ids.append(tmdb_id)
                added += 1
                budget = data.get("budget", "N/A")
                print(f"  Added: {title} - Budget: {budget}")
            else:
                print(f"  Failed to fetch: {title}")
        except Exception as e:
            print(f"  Error fetching {title}: {e}")

    # Save database
    with open(db_path, "w") as f:
        json.dump(db, f, indent=2)

    print(f"\nDone! Added {added} titles, skipped {skipped}.")
    print(f"Total titles in database: {len(db['titles'])}")

if __name__ == "__main__":
    populate_database()
