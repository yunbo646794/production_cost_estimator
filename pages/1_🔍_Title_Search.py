import os
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from streamlit_searchbox import st_searchbox
from api import TMDbClient, get_merged_details

load_dotenv()

st.set_page_config(page_title="Title Search", page_icon="🔍", layout="wide")

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


def get_secret(key: str, default: str = "") -> str:
    """Get secret from st.secrets (Streamlit Cloud) or environment (local dev)."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, AttributeError):
        return os.getenv(key, default)


st.title("🔍 Title Search")
st.caption("Reference tool - search movie and TV show information from TMDb")

# Sidebar - API Configuration
with st.sidebar:
    st.header("API Key")
    tmdb_key = st.text_input(
        "TMDb API Key",
        value=get_secret("TMDB_API_KEY"),
        type="password",
        key="tmdb_key_search"
    )
    st.markdown("[Get free API key](https://www.themoviedb.org/settings/api)")
    st.divider()
    st.caption("Data from [TMDb](https://www.themoviedb.org)")


def search_tmdb(query: str):
    """Search TMDb and return results for the searchbox dropdown."""
    # Get API key inside function to ensure it's available during callback
    api_key = get_secret("TMDB_API_KEY")
    if not query or not api_key:
        return []
    try:
        tmdb = TMDbClient(api_key)
        results = tmdb.search_multi(query)
        options = []
        for item in results[:10]:
            media_type = item.get("media_type", "movie")
            title_text = item.get("title") or item.get("name", "Unknown")
            year = (item.get("release_date") or item.get("first_air_date") or "")[:4]
            type_icon = "🎬" if media_type == "movie" else "📺"
            label = f"{type_icon} {title_text} ({year})" if year else f"{type_icon} {title_text}"
            options.append((label, {"tmdb_id": item["id"], "media_type": media_type}))
        return options
    except Exception:
        return []


# Search with autocomplete dropdown
selected = st_searchbox(
    search_tmdb,
    key="movie_search",
    placeholder="Search for a movie or TV show...",
    default_options=[("🎬 The Dark Knight (2008)", {"tmdb_id": 155, "media_type": "movie"})],
)

# Display selected item details
if selected:
    tmdb_id = selected["tmdb_id"]
    media_type = selected["media_type"]

    with st.spinner("Loading details..."):
        api_key = get_secret("TMDB_API_KEY")
        tmdb = TMDbClient(api_key)
        data, errors = get_merged_details(tmdb, tmdb_id, media_type)

    if errors:
        for error in errors:
            st.warning(error)

    if data:
        st.divider()

        col1, col2 = st.columns([1, 3])

        with col1:
            if data["poster_url"]:
                st.image(data["poster_url"], width=250)

        with col2:
            st.header(data["title"])
            if data["original_title"] and data["original_title"] != data["title"]:
                st.caption(f"Original: {data['original_title']}")

            info_parts = []
            if data["release_date"]:
                info_parts.append(data["release_date"][:4])
            if data["runtime"]:
                info_parts.append(f"{data['runtime']} min")
            if data["status"]:
                info_parts.append(data["status"])
            st.caption(" | ".join(info_parts))

            if data["genres"]:
                st.markdown(f"**Genres:** {', '.join(data['genres'])}")

            if data["vote_average"]:
                st.markdown(f"**Rating:** ⭐ {data['vote_average']:.1f}/10 ({data['vote_count']:,} votes)")

            if data["media_type"] == "movie" and data["directors"]:
                st.markdown(f"**Director:** {', '.join(data['directors'])}")
            elif data.get("created_by"):
                st.markdown(f"**Created by:** {', '.join(data['created_by'])}")

            if data["media_type"] == "tv":
                tv_info = []
                if data["number_of_seasons"]:
                    tv_info.append(f"{data['number_of_seasons']} seasons")
                if data["number_of_episodes"]:
                    tv_info.append(f"{data['number_of_episodes']} episodes")
                if tv_info:
                    st.markdown(f"**Episodes:** {', '.join(tv_info)}")
                if data.get("networks"):
                    st.markdown(f"**Network:** {', '.join(data['networks'])}")

        # Plot
        st.subheader("Plot")
        st.write(data["overview"] or "No overview available.")

        # Financials (movies only)
        if data["media_type"] == "movie":
            st.subheader("Financials")

            if data["budget"] or data["revenue"]:
                fin_cols = st.columns(3)

                with fin_cols[0]:
                    st.metric("Budget", data["budget"] or "N/A")

                with fin_cols[1]:
                    st.metric("Revenue", data["revenue"] or "N/A")

                with fin_cols[2]:
                    if data["budget_raw"] and data["revenue_raw"] and data["budget_raw"] > 0:
                        profit = data["revenue_raw"] - data["budget_raw"]
                        roi = (profit / data["budget_raw"]) * 100
                        profit_str = f"${profit / 1_000_000:.0f}M" if abs(profit) >= 1_000_000 else f"${profit:,}"
                        st.metric("Profit", profit_str, delta=f"{roi:.0f}% ROI")
                    else:
                        st.metric("Profit", "N/A")

                source_links = []
                if data.get("budget_source") and data.get("budget_source_url"):
                    source_links.append(f"Budget: [{data['budget_source']}]({data['budget_source_url']})")
                elif data.get("budget_source"):
                    source_links.append(f"Budget: {data['budget_source']}")
                if data.get("revenue") and data.get("tmdb_url"):
                    source_links.append(f"Revenue: [TMDb]({data['tmdb_url']})")
                if source_links:
                    st.caption(f"📊 Data sources: {' | '.join(source_links)}")
            else:
                st.info("No budget or revenue information found in TMDb or Wikipedia.")

        # Crew section
        with st.expander("Crew"):
            crew_items = []
            if data["directors"]:
                crew_items.append(f"**Director:** {', '.join(data['directors'])}")
            if data["writers"]:
                crew_items.append(f"**Writers:** {', '.join(data['writers'][:5])}")
            if data["producers"]:
                crew_items.append(f"**Producers:** {', '.join(data['producers'])}")
            if data["composers"]:
                crew_items.append(f"**Composer:** {', '.join(data['composers'])}")
            if data["cinematographers"]:
                crew_items.append(f"**Cinematography:** {', '.join(data['cinematographers'])}")

            if crew_items:
                for item in crew_items:
                    st.markdown(item)
            else:
                st.write("No crew information available.")

        # Cast section
        with st.expander("Cast"):
            if data["cast"]:
                for actor in data["cast"]:
                    cast_col1, cast_col2 = st.columns([1, 4])
                    with cast_col1:
                        if actor["profile_url"]:
                            st.image(actor["profile_url"], width=60)
                    with cast_col2:
                        st.markdown(f"**{actor['name']}** as {actor['character']}")
            else:
                st.write("No cast information available.")

        # Additional info
        with st.expander("Additional Info"):
            if data["production_companies"]:
                st.markdown(f"**Production:** {', '.join(data['production_companies'][:5])}")
            if data["production_countries"]:
                st.markdown(f"**Countries:** {', '.join(data['production_countries'])}")
            if data["original_language"]:
                st.markdown(f"**Language:** {data['original_language'].upper()}")

        # Computed Attributes (for Cost Estimator)
        with st.expander("Computed Attributes", expanded=True):
            st.caption("Auto-detected attributes used for finding comparable titles in the Cost Estimator")

            # Get raw data for explanations
            budget_raw = data.get("budget_raw", 0)
            genres = data.get("genres", [])
            cast_names = [c["name"] for c in data.get("cast", [])][:3]

            # Create styled attribute cards
            attr_html = """
            <style>
            .attr-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 10px 0; }
            .attr-card { background: #f0f2f6; border-radius: 8px; padding: 12px; text-align: center; }
            .attr-label { font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px; }
            .attr-value { font-size: 14px; font-weight: 600; color: #1e3a5f; }
            .attr-reason { font-size: 10px; color: #888; margin-top: 4px; }
            </style>
            <div class="attr-grid">
            """

            # Period
            period = data.get("computed_period", "N/A")
            period_reason = "from plot keywords" if period != "Contemporary" else "default (modern setting)"
            attr_html += f'<div class="attr-card"><div class="attr-label">Period</div><div class="attr-value">{period}</div><div class="attr-reason">{period_reason}</div></div>'

            # VFX
            vfx = data.get("computed_vfx", "N/A")
            vfx_genres = [g for g in genres if g.lower() in ["science fiction", "fantasy", "animation", "action", "adventure"]]
            vfx_reason = f"genres: {', '.join(vfx_genres[:2])}" if vfx_genres else "based on genre mix"
            attr_html += f'<div class="attr-card"><div class="attr-label">VFX Level</div><div class="attr-value">{vfx}</div><div class="attr-reason">{vfx_reason}</div></div>'

            # Action
            action = data.get("computed_action", "N/A")
            action_genres = [g for g in genres if g.lower() in ["action", "adventure", "war", "drama", "comedy"]]
            action_reason = f"genre: {action_genres[0]}" if action_genres else "from crew data"
            attr_html += f'<div class="attr-card"><div class="attr-label">Action</div><div class="attr-value">{action}</div><div class="attr-reason">{action_reason}</div></div>'

            # Scale
            scale = data.get("computed_scale", "N/A")
            if budget_raw and budget_raw > 0:
                if budget_raw >= 1_000_000:
                    scale_reason = f"budget: ${budget_raw/1_000_000:.0f}M"
                else:
                    scale_reason = f"budget: ${budget_raw/1_000:.0f}K"
            else:
                scale_reason = "no budget data"
            scale_short = scale.split(" (")[0] if "(" in scale else scale
            attr_html += f'<div class="attr-card"><div class="attr-label">Scale</div><div class="attr-value">{scale_short}</div><div class="attr-reason">{scale_reason}</div></div>'

            # Star Power
            star = data.get("computed_star_power", "N/A")
            if cast_names:
                star_reason = f"cast: {cast_names[0]}"
            else:
                star_reason = "no cast data"
            attr_html += f'<div class="attr-card"><div class="attr-label">Star Power</div><div class="attr-value">{star}</div><div class="attr-reason">{star_reason}</div></div>'

            attr_html += "</div>"
            st.markdown(attr_html, unsafe_allow_html=True)

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
