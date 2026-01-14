import os
import streamlit as st
from dotenv import load_dotenv
from api import TMDbClient, get_merged_details

load_dotenv()

st.set_page_config(page_title="Movie Info", page_icon="🎬", layout="wide")

st.title("🎬 Movie Information Finder")

# Sidebar - API Configuration
with st.sidebar:
    st.header("API Key")
    tmdb_key = st.text_input(
        "TMDb API Key",
        value=os.getenv("TMDB_API_KEY", ""),
        type="password"
    )
    st.markdown("[Get free API key](https://www.themoviedb.org/settings/api)")
    st.divider()
    st.caption("Data from [TMDb](https://www.themoviedb.org)")

# Initialize session state
if "selected_item" not in st.session_state:
    st.session_state.selected_item = None
if "search_results" not in st.session_state:
    st.session_state.search_results = []

# Search input
title = st.text_input("Enter a movie or TV show title:", value="The Dark Knight")

if st.button("Search", type="primary"):
    if not tmdb_key:
        st.error("Please enter your TMDb API key in the sidebar.")
    elif not title:
        st.warning("Please enter a title to search.")
    else:
        with st.spinner("Searching..."):
            try:
                tmdb = TMDbClient(tmdb_key)
                results = tmdb.search_multi(title)
                st.session_state.search_results = results
                st.session_state.selected_item = None
            except Exception as e:
                st.error(f"Search failed: {str(e)}")
                st.session_state.search_results = []

# Display search results
if st.session_state.search_results:
    st.subheader("Select a title:")

    for item in st.session_state.search_results:
        media_type = item.get("media_type", "movie")
        title_text = item.get("title") or item.get("name", "Unknown")
        year = (item.get("release_date") or item.get("first_air_date") or "")[:4]
        type_badge = "🎬 Movie" if media_type == "movie" else "📺 TV"

        label = f"{type_badge} | {title_text} ({year})" if year else f"{type_badge} | {title_text}"

        if st.button(label, key=f"{media_type}_{item['id']}"):
            st.session_state.selected_item = {
                "tmdb_id": item["id"],
                "media_type": media_type
            }

# Display selected item details
if st.session_state.selected_item:
    tmdb_id = st.session_state.selected_item["tmdb_id"]
    media_type = st.session_state.selected_item["media_type"]

    with st.spinner("Loading details..."):
        tmdb = TMDbClient(tmdb_key)
        data, errors = get_merged_details(tmdb, tmdb_id, media_type)

    if errors:
        for error in errors:
            st.warning(error)

    if data:
        st.divider()

        # Header section
        col1, col2 = st.columns([1, 3])

        with col1:
            if data["poster_url"]:
                st.image(data["poster_url"], width=250)

        with col2:
            st.header(data["title"])
            if data["original_title"] and data["original_title"] != data["title"]:
                st.caption(f"Original: {data['original_title']}")

            # Basic info line
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

            # Rating
            if data["vote_average"]:
                st.markdown(f"**Rating:** ⭐ {data['vote_average']:.1f}/10 ({data['vote_count']:,} votes)")

            # Directors/Creators
            if data["media_type"] == "movie" and data["directors"]:
                st.markdown(f"**Director:** {', '.join(data['directors'])}")
            elif data["created_by"]:
                st.markdown(f"**Created by:** {', '.join(data['created_by'])}")

            # TV specific info
            if data["media_type"] == "tv":
                tv_info = []
                if data["number_of_seasons"]:
                    tv_info.append(f"{data['number_of_seasons']} seasons")
                if data["number_of_episodes"]:
                    tv_info.append(f"{data['number_of_episodes']} episodes")
                if tv_info:
                    st.markdown(f"**Episodes:** {', '.join(tv_info)}")
                if data["networks"]:
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

                # Show data sources
                sources = []
                if data.get("budget_source"):
                    sources.append(f"Budget: {data['budget_source']}")
                if data.get("revenue"):
                    sources.append("Revenue: TMDb")
                if sources:
                    st.caption(f"📊 Data sources: {' | '.join(sources)}")
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
