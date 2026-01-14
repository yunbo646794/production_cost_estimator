import re
import requests
from bs4 import BeautifulSoup


HEADERS = {"User-Agent": "MovieInfoApp/1.0 (https://github.com/example; contact@example.com)"}


def search_wikipedia(title: str, year: str = None) -> str | None:
    """Search Wikipedia and return the page URL for a movie/TV show."""
    search_query = f"{title} {year} film" if year else f"{title} film"

    # Use Wikipedia API to search
    params = {
        "action": "query",
        "list": "search",
        "srsearch": search_query,
        "format": "json",
        "srlimit": 5
    }

    response = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=HEADERS)
    data = response.json()

    results = data.get("query", {}).get("search", [])
    if not results:
        return None

    # Return the first result's page title
    return results[0].get("title")


def get_budget_from_wikipedia(title: str, year: str = None) -> dict:
    """
    Fetch budget information from Wikipedia.
    Returns dict with 'budget', 'budget_raw', 'source', and 'url'.
    """
    result = {
        "budget": None,
        "budget_raw": None,
        "source": None,
        "url": None
    }

    try:
        # Find the Wikipedia page
        page_title = search_wikipedia(title, year)
        if not page_title:
            return result

        # Fetch the page content
        url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Find the infobox
        infobox = soup.find("table", class_="infobox")
        if not infobox:
            return result

        # Look for budget row
        for row in infobox.find_all("tr"):
            header = row.find("th")
            if header and "budget" in header.get_text().lower():
                value_cell = row.find("td")
                if value_cell:
                    budget_text = value_cell.get_text(strip=True)
                    parsed = parse_budget(budget_text)
                    if parsed:
                        result["budget"] = format_budget(parsed)
                        result["budget_raw"] = parsed
                        result["source"] = "Wikipedia"
                        # Create URL with text fragment to highlight budget
                        # Extract clean budget text for highlighting (remove footnotes)
                        clean_budget = re.sub(r'\[.*?\]', '', budget_text).strip()
                        highlight_text = clean_budget.replace(' ', '%20').replace('$', '%24')
                        result["url"] = f"{url}#:~:text={highlight_text}"
                break

        return result

    except Exception:
        return result


def parse_budget(text: str) -> int | None:
    """Parse budget text like '$185 million' or '$185,000,000' into integer."""
    if not text:
        return None

    # Clean the text
    text = text.lower().replace(",", "").replace(" ", "")

    # Try to find dollar amounts
    # Pattern: $XXX million/billion or $XXX,XXX,XXX

    # Match patterns like $185million, $1.5billion
    match = re.search(r"\$?([\d.]+)\s*(million|billion|mil|bil)", text)
    if match:
        number = float(match.group(1))
        unit = match.group(2)
        if "billion" in unit or "bil" in unit:
            return int(number * 1_000_000_000)
        else:
            return int(number * 1_000_000)

    # Match patterns like $185000000
    match = re.search(r"\$?([\d]+)", text)
    if match:
        number = int(match.group(1))
        if number > 10000:  # Likely a real budget amount
            return number

    return None


def format_budget(amount: int) -> str:
    """Format budget amount as readable string."""
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.0f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:,}"
