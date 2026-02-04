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

# Initialize comparison list in session state
if "compare_titles" not in st.session_state:
    st.session_state.compare_titles = []

# Sidebar
with st.sidebar:
    st.caption("Data from [TMDb](https://www.themoviedb.org)")

    # Comparison controls in sidebar
    if st.session_state.compare_titles:
        st.divider()
        st.subheader(f"Compare ({len(st.session_state.compare_titles)}/5)")
        for i, t in enumerate(st.session_state.compare_titles):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(t.get("title", "Unknown")[:20])
            with col2:
                if st.button("✕", key=f"remove_{i}"):
                    st.session_state.compare_titles.pop(i)
                    st.rerun()
        if st.button("Clear All"):
            st.session_state.compare_titles = []
            st.rerun()


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

# Load data early so button can appear at top
data = None
errors = []
if selected:
    tmdb_id = selected["tmdb_id"]
    media_type = selected["media_type"]
    with st.spinner("Loading details..."):
        api_key = get_secret("TMDB_API_KEY")
        tmdb = TMDbClient(api_key)
        data, errors = get_merged_details(tmdb, tmdb_id, media_type)

# Add to Comparison button (at top for visibility)
if data:
    can_add = len(st.session_state.compare_titles) < 5
    already_added = any(t.get("tmdb_id") == data.get("tmdb_id") for t in st.session_state.compare_titles)
    if can_add and not already_added:
        if st.button("➕ Add to Comparison", type="secondary", key=f"add_top_{data.get('tmdb_id')}"):
            st.session_state.compare_titles.append(data)
            st.success(f"Added '{data['title']}' to comparison")
            st.rerun()
    elif already_added:
        st.info("✓ Already in comparison")
    else:
        st.warning("Comparison full (max 5 titles)")

# Comparison status prompt
compare_count = len(st.session_state.compare_titles)
if compare_count == 0:
    st.info("📊 **Compare titles:** Search and add up to 5 titles to compare side-by-side")
elif compare_count < 2:
    st.info(f"📊 **{compare_count}/5 titles added** — Add at least one more to compare")
else:
    st.success(f"📊 **{compare_count}/5 titles ready to compare** — Scroll down to see comparison")

# Display selected item details
if selected:
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
            tmdb_link = data.get("tmdb_url", "")
            if tmdb_link:
                st.markdown(f"# [{data['title']}]({tmdb_link})")
            else:
                st.header(data["title"])
            if data["original_title"] and data["original_title"] != data["title"]:
                st.caption(f"Original: {data['original_title']}")

            if data.get("tagline"):
                st.markdown(f"*\"{data['tagline']}\"*")

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
                st.info("💡 Budget/revenue data not found in Wikipedia or TMDb.")

        # Crew section with tabs
        st.subheader("Crew")
        crew_tabs = st.tabs(["Key Creative", "Production Design", "Post-Production", "VFX & Stunts"])

        with crew_tabs[0]:  # Key Creative
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
                st.caption("No key creative crew information available.")

        with crew_tabs[1]:  # Production Design
            design_items = []
            if data.get("production_designers"):
                design_items.append(f"**Production Designer:** {', '.join(data['production_designers'])}")
            if data.get("art_directors"):
                design_items.append(f"**Art Director:** {', '.join(data['art_directors'][:3])}")
            if data.get("set_decorators"):
                design_items.append(f"**Set Decorator:** {', '.join(data['set_decorators'][:3])}")
            if data.get("costume_designers"):
                design_items.append(f"**Costume Designer:** {', '.join(data['costume_designers'])}")
            if data.get("makeup_heads"):
                design_items.append(f"**Makeup:** {', '.join(data['makeup_heads'][:2])}")
            if design_items:
                for item in design_items:
                    st.markdown(item)
            else:
                st.caption("No production design crew information available.")

        with crew_tabs[2]:  # Post-Production
            post_items = []
            if data.get("editors"):
                post_items.append(f"**Editor:** {', '.join(data['editors'][:3])}")
            if data.get("sound_designers"):
                post_items.append(f"**Sound Designer:** {', '.join(data['sound_designers'][:3])}")
            if post_items:
                for item in post_items:
                    st.markdown(item)
            else:
                st.caption("No post-production crew information available.")

        with crew_tabs[3]:  # VFX & Stunts
            vfx_items = []
            if data.get("vfx_supervisors"):
                vfx_items.append(f"**VFX Supervisor:** {', '.join(data['vfx_supervisors'][:3])}")
            if data.get("stunt_coordinators"):
                vfx_items.append(f"**Stunt Coordinator:** {', '.join(data['stunt_coordinators'][:3])}")
            if vfx_items:
                for item in vfx_items:
                    st.markdown(item)
            else:
                st.caption("No VFX or stunt crew information available.")

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
            # Franchise/Collection info
            if data.get("collection"):
                collection_url = f"https://www.themoviedb.org/collection/{data['collection_id']}" if data.get("collection_id") else None
                if collection_url:
                    st.markdown(f"**Franchise:** [{data['collection']}]({collection_url})")
                else:
                    st.markdown(f"**Franchise:** {data['collection']}")

            # Spoken languages
            if data.get("spoken_languages"):
                st.markdown(f"**Languages:** {', '.join(data['spoken_languages'])}")
            elif data.get("original_language"):
                st.markdown(f"**Language:** {data['original_language'].upper()}")

            if data["production_countries"]:
                st.markdown(f"**Countries:** {', '.join(data['production_countries'])}")

            # Production companies with logos
            if data.get("production_companies_full"):
                st.markdown("**Production Companies:**")
                companies = data["production_companies_full"][:4]
                logo_cols = st.columns(len(companies))
                for i, company in enumerate(companies):
                    with logo_cols[i]:
                        if company.get("logo_url"):
                            st.image(company["logo_url"], width=80)
                        name = company["name"]
                        if company.get("origin_country"):
                            name += f" ({company['origin_country']})"
                        st.caption(name)
            elif data["production_companies"]:
                st.markdown(f"**Production:** {', '.join(data['production_companies'][:5])}")

            # Official homepage
            if data.get("homepage"):
                st.markdown(f"**Official Site:** [{data['homepage'][:40]}...]({data['homepage']})" if len(data.get("homepage", "")) > 40 else f"**Official Site:** [{data['homepage']}]({data['homepage']})")

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

# --- Title Comparison Section ---
if len(st.session_state.compare_titles) >= 2:
    st.divider()
    st.subheader("📊 Title Comparison")

    compare_titles = st.session_state.compare_titles
    num_titles = len(compare_titles)

    # Helper to safely get values
    def get_val(title, key, default="N/A"):
        val = title.get(key)
        return val if val else default

    # Build comparison table HTML with row-based layout for alignment
    col_width = 100 // num_titles

    html = f"""
    <style>
    body {{ background-color: #0e1117; color: #fafafa; margin: 0; padding: 0; font-family: 'Source Sans Pro', sans-serif; }}
    .comp-table {{ width: 100%; border-collapse: collapse; background-color: #0e1117; }}
    .comp-table td {{
        vertical-align: top;
        padding: 12px;
        border-bottom: 1px solid #333;
        width: {col_width}%;
        color: #fafafa;
    }}
    .comp-table tr.section-header td {{
        background: #1e3a5f;
        color: #d4af37;
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        padding: 8px 12px;
    }}
    .comp-poster {{ text-align: center; }}
    .comp-poster img {{ max-width: 150px; border-radius: 8px; }}
    .comp-title {{ font-weight: 600; font-size: 14px; color: #fafafa; }}
    .comp-title a {{ color: #58a6ff; text-decoration: none; }}
    .comp-title a:hover {{ text-decoration: underline; }}
    .comp-subtitle {{ color: #aaa; font-size: 12px; }}
    .comp-value {{ font-size: 13px; color: #fafafa; }}
    .profit-pos {{ color: #4ade80; }}
    .profit-neg {{ color: #f87171; }}
    </style>
    <table class="comp-table">
    """

    # Row 1: Posters + Title + Year
    html += "<tr>"
    for t in compare_titles:
        poster = t.get("poster_url", "")
        title_name = t.get("title", "Unknown")
        year = t.get("release_date", "")[:4] if t.get("release_date") else "N/A"
        runtime = t.get("runtime", "N/A")
        tmdb_url = t.get("tmdb_url", "")
        poster_img = f'<img src="{poster}">' if poster else ""
        title_link = f'<a href="{tmdb_url}" target="_blank">{title_name}</a>' if tmdb_url else title_name
        html += f'''<td class="comp-poster">
            {poster_img}
            <div class="comp-title">{title_link}</div>
            <div class="comp-subtitle">{year} | {runtime} min</div>
        </td>'''
    html += "</tr>"

    # Row 2: Genres
    html += f'<tr class="section-header">{"".join(["<td>Genres</td>"] * num_titles)}</tr>'
    html += "<tr>"
    for t in compare_titles:
        genres = ", ".join(t.get("genres", [])[:3]) or "N/A"
        html += f'<td class="comp-value">{genres}</td>'
    html += "</tr>"

    # Row 3: Reception
    html += f'<tr class="section-header">{"".join(["<td>Reception</td>"] * num_titles)}</tr>'
    html += "<tr>"
    for t in compare_titles:
        rating = t.get("vote_average")
        votes = t.get("vote_count")
        if rating:
            rating_html = f'<div>⭐ {rating:.1f}/10</div>'
            if votes:
                rating_html += f'<div style="color:#888;font-size:11px;">{votes:,} votes</div>'
        else:
            rating_html = "N/A"
        html += f'<td class="comp-value">{rating_html}</td>'
    html += "</tr>"

    # Row 4: Creative Team
    html += f'<tr class="section-header">{"".join(["<td>Creative</td>"] * num_titles)}</tr>'
    html += "<tr>"
    for t in compare_titles:
        director = ", ".join(t.get("directors", [])[:2]) or "N/A"
        composer = ", ".join(t.get("composers", [])[:1]) or "N/A"
        cinematographer = ", ".join(t.get("cinematographers", [])[:1]) or "N/A"
        html += f'''<td class="comp-value">
            <div>Director: {director}</div>
            <div>Composer: {composer}</div>
            <div>DP: {cinematographer}</div>
        </td>'''
    html += "</tr>"

    # Row 5: Financials
    html += f'<tr class="section-header">{"".join(["<td>Financials</td>"] * num_titles)}</tr>'
    html += "<tr>"
    for t in compare_titles:
        budget = t.get("budget", "N/A")
        revenue = t.get("revenue", "N/A")
        profit_html = ""
        if t.get("budget_raw") and t.get("revenue_raw") and t["budget_raw"] > 0:
            profit = t["revenue_raw"] - t["budget_raw"]
            roi = (profit / t["budget_raw"]) * 100
            profit_str = f"${profit / 1_000_000:.0f}M" if abs(profit) >= 1_000_000 else f"${profit:,}"
            css_class = "profit-pos" if profit > 0 else "profit-neg"
            profit_html = f'<div class="{css_class}">Profit: {profit_str} ({roi:.0f}%)</div>'
        html += f'''<td class="comp-value">
            <div>Budget: {budget}</div>
            <div>Revenue: {revenue}</div>
            {profit_html}
        </td>'''
    html += "</tr>"

    # Row 6: Top Cast
    html += f'<tr class="section-header">{"".join(["<td>Top Cast</td>"] * num_titles)}</tr>'
    html += "<tr>"
    for t in compare_titles:
        cast = t.get("cast", [])[:3]
        cast_html = "<br>".join([f"• {c.get('name', 'Unknown')}" for c in cast]) if cast else "N/A"
        html += f'<td class="comp-value">{cast_html}</td>'
    html += "</tr>"

    # Row 7: Attributes
    html += f'<tr class="section-header">{"".join(["<td>Attributes</td>"] * num_titles)}</tr>'
    html += "<tr>"
    for t in compare_titles:
        scale = (t.get("computed_scale") or "N/A").split(" (")[0]
        vfx = t.get("computed_vfx", "N/A")
        star = t.get("computed_star_power", "N/A")
        period = t.get("computed_period", "N/A")
        action = t.get("computed_action", "N/A")
        html += f'''<td class="comp-value">
            <div>Scale: {scale}</div>
            <div>VFX: {vfx}</div>
            <div>Star Power: {star}</div>
            <div>Period: {period}</div>
            <div>Action: {action}</div>
        </td>'''
    html += "</tr>"

    # Row 8: Production
    html += f'<tr class="section-header">{"".join(["<td>Production</td>"] * num_titles)}</tr>'
    html += "<tr>"
    for t in compare_titles:
        country = t.get("production_countries", ["N/A"])[0] if t.get("production_countries") else "N/A"
        studio = t.get("production_companies", ["N/A"])[0][:20] if t.get("production_companies") else "N/A"
        franchise = t.get("collection") or "Standalone"
        languages = ", ".join(t.get("spoken_languages", [])[:2]) or t.get("original_language", "N/A").upper()
        html += f'''<td class="comp-value">
            <div>Franchise: {franchise}</div>
            <div>Studio: {studio}</div>
            <div>Country: {country}</div>
            <div>Languages: {languages}</div>
        </td>'''
    html += "</tr>"

    html += "</table>"

    components.html(html, height=800, scrolling=True)

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
