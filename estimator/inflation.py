"""
Inflation adjustment for historical movie budgets.
Uses CPI data from Bureau of Labor Statistics.
"""

# CPI data (annual averages, normalized to 2024 = 100)
# Source: Bureau of Labor Statistics, Consumer Price Index
CPI_DATA = {
    1980: 26.0, 1981: 28.7, 1982: 30.5, 1983: 31.5, 1984: 32.8,
    1985: 34.0, 1986: 34.6, 1987: 35.9, 1988: 37.4, 1989: 39.2,
    1990: 41.3, 1991: 43.0, 1992: 44.3, 1993: 45.6, 1994: 46.8,
    1995: 48.1, 1996: 49.5, 1997: 50.7, 1998: 51.5, 1999: 52.6,
    2000: 54.4, 2001: 56.0, 2002: 56.9, 2003: 58.2, 2004: 59.7,
    2005: 61.7, 2006: 63.7, 2007: 65.5, 2008: 68.1, 2009: 67.8,
    2010: 68.9, 2011: 71.1, 2012: 72.6, 2013: 73.6, 2014: 74.8,
    2015: 74.9, 2016: 75.8, 2017: 77.5, 2018: 79.4, 2019: 80.8,
    2020: 81.8, 2021: 85.7, 2022: 92.6, 2023: 96.5, 2024: 100.0,
    2025: 102.5, 2026: 105.0,  # Projected
}


def adjust_for_inflation(amount: int, from_year: int, to_year: int = 2024) -> int:
    """
    Adjust budget from historical year to target year dollars.

    Args:
        amount: Original budget amount
        from_year: Year of the original budget
        to_year: Target year for adjustment (default: 2024)

    Returns:
        Adjusted budget in target year dollars
    """
    if not amount:
        return amount

    # Handle years outside our data range
    from_cpi = CPI_DATA.get(from_year)
    to_cpi = CPI_DATA.get(to_year)

    if not from_cpi or not to_cpi:
        return amount

    multiplier = to_cpi / from_cpi
    return int(amount * multiplier)


def get_inflation_multiplier(from_year: int, to_year: int = 2024) -> float:
    """
    Get the inflation multiplier between two years.

    Args:
        from_year: Starting year
        to_year: Target year (default: 2024)

    Returns:
        Multiplier to convert from_year dollars to to_year dollars
    """
    from_cpi = CPI_DATA.get(from_year)
    to_cpi = CPI_DATA.get(to_year)

    if not from_cpi or not to_cpi:
        return 1.0

    return to_cpi / from_cpi


def format_currency(amount: int) -> str:
    """Format budget as readable currency string."""
    if not amount:
        return "N/A"
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.0f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:,}"
