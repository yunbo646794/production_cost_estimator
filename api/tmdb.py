import requests

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/"
POSTER_SIZE = "w500"
PROFILE_SIZE = "w185"


def get_poster_url(poster_path: str) -> str | None:
    """Construct full poster URL from TMDb path."""
    if poster_path:
        return f"{TMDB_IMAGE_BASE}{POSTER_SIZE}{poster_path}"
    return None


def get_profile_url(profile_path: str) -> str | None:
    """Construct full profile image URL from TMDb path."""
    if profile_path:
        return f"{TMDB_IMAGE_BASE}{PROFILE_SIZE}{profile_path}"
    return None


class TMDbClient:
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make a GET request to TMDb API."""
        params = params or {}
        params["api_key"] = self.api_key
        response = requests.get(f"{self.BASE_URL}{endpoint}", params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def search_multi(self, query: str) -> list:
        """Search movies, TV shows, and people."""
        data = self._get("/search/multi", {"query": query})
        results = data.get("results", [])
        # Filter to only movies and TV shows
        return [r for r in results if r.get("media_type") in ("movie", "tv")]

    def get_movie_details(self, tmdb_id: int) -> dict:
        """Get movie details including budget and revenue."""
        return self._get(f"/movie/{tmdb_id}")

    def get_movie_credits(self, tmdb_id: int) -> dict:
        """Get movie cast and crew."""
        return self._get(f"/movie/{tmdb_id}/credits")

    def get_tv_details(self, tmdb_id: int) -> dict:
        """Get TV show details."""
        return self._get(f"/tv/{tmdb_id}")

    def get_tv_credits(self, tmdb_id: int) -> dict:
        """Get TV show cast and crew."""
        return self._get(f"/tv/{tmdb_id}/credits")

    def get_external_ids(self, tmdb_id: int, media_type: str) -> dict:
        """Get external IDs (IMDb, etc.) for a movie or TV show."""
        return self._get(f"/{media_type}/{tmdb_id}/external_ids")
