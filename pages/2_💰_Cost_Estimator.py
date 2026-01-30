import os
import sys
import json
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from similarity import find_comparable_titles
from estimator import adjust_for_inflation, format_currency

load_dotenv()

st.set_page_config(page_title="Cost Estimator", page_icon="💰", layout="wide")

# Google Analytics
GA_TRACKING_CODE = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-7J88HTR1H2"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-7J88HTR1H2');
</script>
"""
components.html(GA_TRACKING_CODE, height=0)


def get_recency_multiplier(year: int) -> float:
    """Get recency weight based on release year.

    Recent films are more relevant to current production costs.
    Note: Comp titles are already filtered to last 6 years.
    """
    from datetime import datetime
    current_year = datetime.now().year

    years_old = current_year - year

    if years_old <= 1:
        return 2.0   # This year or last year - most relevant
    elif years_old <= 2:
        return 1.7   # 2 years old
    elif years_old <= 3:
        return 1.4   # 3 years old
    elif years_old <= 4:
        return 1.1   # 4 years old
    elif years_old <= 5:
        return 0.9   # 5 years old
    else:
        return 0.7   # 6 years old (edge of window)

st.title("💰 Production Cost Estimator")

st.markdown("Select attributes for your project to find comparable titles and estimate production costs.")

# Sidebar - must be defined before main content uses the toggle
with st.sidebar:
    adjust_inflation = st.toggle("⚙️ Adjust for inflation", value=True,
                                  help="Convert all budgets to 2024 dollars")

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
            "country": country,
            "runtime": runtime,
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
                        tmdb_link = title.get("tmdb_url", "")
                        if tmdb_link:
                            st.markdown(f"**[{title.get('title', 'Unknown')}]({tmdb_link})** ({year_str})")
                        else:
                            st.markdown(f"**{title.get('title', 'Unknown')}** ({year_str})")
                        if reasons:
                            tags = " ".join(f"`{r}`" for r in reasons)
                            st.markdown(f"**Why similar:** {tags}", help="Attributes matching your project")
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

            # Calculate budget estimate from comparable titles (weighted by similarity + recency)
            # Always use 2024-adjusted dollars for the final estimate
            weighted_data = []
            for c in comparables:
                if c["title"].get("budget_raw"):
                    original = c["title"]["budget_raw"]
                    year_str = c["title"].get("release_date", "")[:4]
                    if year_str.isdigit():
                        year = int(year_str)
                        budget = adjust_for_inflation(original, year)
                        similarity = c["score"]
                        recency = get_recency_multiplier(year)
                        combined_weight = similarity * recency
                        weighted_data.append({
                            "title": c["title"].get("title", "Unknown"),
                            "year": year,
                            "budget": budget,
                            "original_budget": original,
                            "similarity": similarity,
                            "recency": recency,
                            "weight": combined_weight,
                        })

            if weighted_data:
                # Calculate weighted average
                total_weight = sum(d["weight"] for d in weighted_data)
                for d in weighted_data:
                    d["contribution"] = (d["weight"] / total_weight) * d["budget"]

                avg_budget = sum(d["contribution"] for d in weighted_data)
                low_budget = min(d["budget"] for d in weighted_data)
                high_budget = max(d["budget"] for d in weighted_data)

                st.subheader("Estimated Budget Range")
                st.caption("All budgets adjusted to 2024 dollars | Weighted by similarity + recency")

                # --- Visual Budget Range Bar ---
                range_html = f"""
                <div style="background: #1e1e2f; border-radius: 12px; padding: 24px; margin: 10px 0 20px 0; border: 1px solid rgba(212,175,55,0.2);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 16px;">
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px;">Low</div>
                            <div style="font-size: 24px; font-weight: 700; color: #63b3ed;">{format_currency(int(low_budget))}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #d4af37; text-transform: uppercase; letter-spacing: 1px;">Base Estimate</div>
                            <div style="font-size: 36px; font-weight: 700; color: #d4af37;">{format_currency(int(avg_budget))}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px;">High</div>
                            <div style="font-size: 24px; font-weight: 700; color: #fc8181;">{format_currency(int(high_budget))}</div>
                        </div>
                    </div>
                    <div style="position: relative; height: 12px; background: linear-gradient(90deg, #63b3ed 0%, #d4af37 50%, #fc8181 100%); border-radius: 6px; margin: 0 10px;">
                        <div style="position: absolute; top: -4px; left: 50%; transform: translateX(-50%); width: 20px; height: 20px; background: #d4af37; border-radius: 50%; border: 3px solid #1e1e2f;"></div>
                    </div>
                    <div style="text-align: center; margin-top: 12px;">
                        <span style="font-size: 12px; color: #718096;">Based on {len(weighted_data)} comparable titles</span>
                    </div>
                </div>
                """
                st.markdown(range_html, unsafe_allow_html=True)

                # --- Budget Contribution Chart ---
                sorted_data = sorted(weighted_data, key=lambda x: x["contribution"], reverse=True)
                max_contribution = max(d["contribution"] for d in sorted_data)

                with st.expander("📊 Contribution Breakdown", expanded=True):
                    for d in sorted_data:
                        pct = (d["contribution"] / avg_budget) * 100
                        bar_width = (d["contribution"] / max_contribution) * 100

                        bar_html = f"""
                        <div style="margin-bottom: 12px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                <span style="font-weight: 600; font-size: 14px;">{d['title']} <span style="color: #718096; font-weight: 400;">({d['year']})</span></span>
                                <span style="font-weight: 600; font-size: 14px;">{format_currency(int(d['contribution']))} <span style="color: #718096; font-weight: 400;">({pct:.0f}%)</span></span>
                            </div>
                            <div style="background: #2d3748; border-radius: 4px; height: 24px; overflow: hidden;">
                                <div style="background: linear-gradient(90deg, #d4af37, #b8960c); width: {bar_width}%; height: 100%; border-radius: 4px; display: flex; align-items: center; padding-left: 8px;">
                                    <span style="font-size: 11px; color: #1a1a2e; font-weight: 600;">{d['similarity']:.0f}% sim · {d['recency']}x rec · {format_currency(d['budget'])}</span>
                                </div>
                            </div>
                        </div>
                        """
                        st.markdown(bar_html, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div style="text-align: right; padding-top: 8px; border-top: 1px solid #2d3748; margin-top: 8px;">
                        <span style="font-weight: 700; font-size: 16px;">Weighted Total: {format_currency(int(avg_budget))}</span>
                    </div>
                    """, unsafe_allow_html=True)

                # --- Methodology ---
                with st.expander("📋 Methodology"):
                    st.markdown("""
**How it works:** Weighted average of comparable titles from the **last 6 years**

Each title's influence = `Similarity Score × Recency Multiplier`

| Recency | Multiplier | Rationale |
|---------|-----------|-----------|
| 0-1 years | **2.0x** | Most relevant to current costs |
| 2 years | **1.7x** | Recent market conditions |
| 3 years | **1.4x** | Moderately relevant |
| 4 years | **1.1x** | Baseline |
| 5 years | **0.9x** | Slightly outdated |
| 6 years | **0.7x** | Edge of relevance window |

**Why 6 years?** Industry standard — producers typically use recent comps for pitch decks.
                    """)
            else:
                st.info("No budget data available for comparable titles.")
        else:
            st.info("No similar titles found. Try adjusting your attributes.")

    else:
        st.error("No titles in database! Go to Title Search and save some titles first.")

# Update sidebar with attribution
with st.sidebar:
    st.caption("Data from [TMDb](https://www.themoviedb.org)")

# Floating Feedback Bar
FEEDBACK_BAR = """
<style>
.feedback-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%);
    padding: 12px 20px;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 15px;
    z-index: 9999;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
}
.feedback-bar p {
    color: white;
    margin: 0;
    font-size: 14px;
}
.feedback-bar a {
    background: #ff6b6b;
    color: white;
    padding: 8px 20px;
    border-radius: 20px;
    text-decoration: none;
    font-weight: bold;
    font-size: 14px;
    transition: background 0.3s;
}
.feedback-bar a:hover {
    background: #ff5252;
}
</style>
<div class="feedback-bar">
    <p>💡 Help us improve this tool!</p>
    <a href="https://docs.google.com/forms/d/e/1FAIpQLSeD9j4-d0kVdt_UhT0etGqislY-Ue79PllVf9-akGLRu0r--A/viewform" target="_blank">Give Feedback</a>
</div>
"""
st.markdown(FEEDBACK_BAR, unsafe_allow_html=True)
