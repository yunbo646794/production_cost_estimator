import os
import sys
import json
import streamlit as st
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from similarity import find_comparable_titles
from estimator import adjust_for_inflation, format_currency

load_dotenv()

st.set_page_config(page_title="Cost Estimator", page_icon="💰", layout="wide")

st.title("💰 Production Cost Estimator")

st.markdown("Select attributes for your project to find comparable titles and estimate production costs.")

# Sidebar - must be defined before main content uses the toggle
with st.sidebar:
    st.header("Settings")
    adjust_inflation = st.toggle("Adjust for inflation", value=True,
                                  help="Convert all budgets to 2024 dollars")

    st.divider()

    st.header("Database Stats")
    # Will be populated after load_titles_db is defined

# Load reference data - use absolute path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


@st.cache_data
def load_actor_tiers():
    with open(os.path.join(DATA_DIR, "actor_tiers.json"), "r") as f:
        return json.load(f)


@st.cache_data
def load_studio_tiers():
    with open(os.path.join(DATA_DIR, "studio_tiers.json"), "r") as f:
        return json.load(f)


def load_titles_db():
    """Load titles database (no caching - always read fresh data)."""
    try:
        with open(os.path.join(DATA_DIR, "titles_db.json"), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"titles": []}


# Attribute Definitions
FORMAT_OPTIONS = ["Feature Film", "TV Series", "Limited Series", "Documentary", "Animation"]
GENRE_OPTIONS = ["Action/Adventure", "Drama", "Comedy", "Horror/Thriller", "Sci-Fi/Fantasy"]
RUNTIME_OPTIONS = ["Short", "Standard", "Long", "Epic"]
PERIOD_OPTIONS = ["Contemporary", "Recent Past (1980-2010)", "Period (1900-1980)", "Historical (pre-1900)", "Futuristic"]
STAR_POWER_OPTIONS = ["A-List", "B-List", "Rising Stars", "Ensemble/Unknown"]
VFX_OPTIONS = ["Heavy", "Moderate", "Light", "Practical Only"]
LOCATION_OPTIONS = ["Contained (1-2)", "Limited (3-5)", "Moderate (6-10)", "Extensive (10+)", "Global"]
ACTION_OPTIONS = ["High", "Moderate", "Light", "Dialogue-Driven"]
COUNTRY_OPTIONS = ["USA (Hollywood)", "UK", "Canada/Australia", "Europe (non-UK)", "Asia/Other"]
SCALE_OPTIONS = ["Blockbuster ($100M+)", "Major Studio ($50-100M)", "Mid-Budget ($20-50M)", "Indie ($5-20M)", "Micro (<$5M)"]

st.divider()

# Input Form - 10 Attributes
st.subheader("Project Attributes")

col1, col2 = st.columns(2)

with col1:
    format_type = st.selectbox("1. Format", FORMAT_OPTIONS, index=0)
    genre = st.selectbox("2. Primary Genre", GENRE_OPTIONS, index=1)
    runtime = st.selectbox("3. Runtime", RUNTIME_OPTIONS, index=1,
                          help="Film: Short <90min, Standard 90-120min, Long 120-150min, Epic 150+min")
    period = st.selectbox("4. Period/Era", PERIOD_OPTIONS, index=0)
    star_power = st.selectbox("5. Star Power", STAR_POWER_OPTIONS, index=2)

with col2:
    vfx = st.selectbox("6. VFX Intensity", VFX_OPTIONS, index=2)
    locations = st.selectbox("7. Location Count", LOCATION_OPTIONS, index=1)
    action = st.selectbox("8. Action Complexity", ACTION_OPTIONS, index=2)
    country = st.selectbox("9. Production Country", COUNTRY_OPTIONS, index=0)
    scale = st.selectbox("10. Production Scale", SCALE_OPTIONS, index=2)

st.divider()

# Estimate Button
if st.button("🔍 Find Comparable Titles & Estimate", type="primary"):
    db = load_titles_db()
    titles = db.get("titles", [])

    if len(titles) < 3:
        st.warning(f"⚠️ Only {len(titles)} titles in database. Add more titles via Title Search for better estimates!")

    if titles:
        # Build user attributes dict for similarity matching
        user_attrs = {
            "genre": genre,
            "scale": scale,
            "vfx": vfx,
            "action": action,
            "period": period,
            "star_power": star_power,
        }

        # Find comparable titles
        comparables = find_comparable_titles(user_attrs, titles, limit=5)

        st.subheader("Comparable Titles")

        if comparables:
            for comp in comparables:
                title = comp["title"]
                score = comp["score"]
                reasons = comp["reasons"]

                with st.container():
                    tcol1, tcol2, tcol3 = st.columns([1, 3, 1])
                    with tcol1:
                        if title.get("poster_url"):
                            st.image(title["poster_url"], width=80)
                    with tcol2:
                        year_str = title.get("release_date", "")[:4] if title.get("release_date") else "N/A"
                        st.markdown(f"**{title.get('title', 'Unknown')}** ({year_str})")
                        if reasons:
                            st.caption(f"**Why similar:** {', '.join(reasons)}")
                        else:
                            st.caption(f"{', '.join(title.get('genres', [])[:3])}")
                    with tcol3:
                        st.metric("Match", f"{score:.0f}%")
                        if title.get("budget_raw"):
                            original = title["budget_raw"]
                            if adjust_inflation and year_str.isdigit():
                                adjusted = adjust_for_inflation(original, int(year_str))
                                st.caption(f"Budget: {format_currency(original)} → {format_currency(adjusted)} (2024$)")
                            else:
                                st.caption(f"Budget: {format_currency(original)}")
                    st.divider()

            # Calculate budget estimate from comparable titles
            budgets = []
            for c in comparables:
                if c["title"].get("budget_raw"):
                    original = c["title"]["budget_raw"]
                    year_str = c["title"].get("release_date", "")[:4]
                    if adjust_inflation and year_str.isdigit():
                        budgets.append(adjust_for_inflation(original, int(year_str)))
                    else:
                        budgets.append(original)

            if budgets:
                avg_budget = sum(budgets) / len(budgets)
                low_budget = min(budgets)
                high_budget = max(budgets)

                st.subheader("Estimated Budget Range")
                if adjust_inflation:
                    st.caption("📈 All budgets adjusted to 2024 dollars")
                est_cols = st.columns(3)
                with est_cols[0]:
                    st.metric("Low Estimate", format_currency(int(low_budget)),
                              help="Lowest budget among comparable titles")
                with est_cols[1]:
                    st.metric("Base Estimate", format_currency(int(avg_budget)),
                              help="Average budget of comparable titles")
                with est_cols[2]:
                    st.metric("High Estimate", format_currency(int(high_budget)),
                              help="Highest budget among comparable titles")

                st.caption(f"📊 Based on {len(budgets)} comparable titles with budget data")
            else:
                st.info("No budget data available for comparable titles.")
        else:
            st.info("No similar titles found. Try adjusting your attributes.")

    else:
        st.error("No titles in database! Go to Title Search and save some titles first.")

# Update sidebar with database stats
with st.sidebar:
    db = load_titles_db()
    st.metric("Titles Saved", len(db.get("titles", [])))
    st.divider()
    st.caption("Build your database by saving titles from the Title Search page.")
