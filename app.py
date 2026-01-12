import streamlit as st
import requests

st.set_page_config(page_title="Movie Info", page_icon="🎬")

st.title("🎬 Movie Information Finder")

# API key input (OMDb free API)
api_key = st.sidebar.text_input("OMDb API Key", value="", type="password")
st.sidebar.markdown("[Get a free API key](http://www.omdbapi.com/apikey.aspx)")

# Initialize session state
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None
if "search_results" not in st.session_state:
    st.session_state.search_results = []

# Movie title input
title = st.text_input("Enter a movie title:", placeholder="e.g., The Matrix")

if st.button("Search", type="primary"):
    if not api_key:
        st.error("Please enter your OMDb API key in the sidebar.")
    elif not title:
        st.warning("Please enter a movie title.")
    else:
        with st.spinner("Searching..."):
            # Use search endpoint for fuzzy matching
            url = f"http://www.omdbapi.com/?s={title}&apikey={api_key}"
            response = requests.get(url)
            data = response.json()

        if data.get("Response") == "True":
            st.session_state.search_results = data.get("Search", [])
            st.session_state.selected_movie = None
        else:
            st.error(f"No results found: {data.get('Error', 'Unknown error')}")
            st.session_state.search_results = []

# Display search results as selectable options
if st.session_state.search_results:
    st.subheader("Select a movie:")

    for movie in st.session_state.search_results:
        label = f"{movie['Title']} ({movie['Year']}) - {movie['Type']}"
        if st.button(label, key=movie["imdbID"]):
            st.session_state.selected_movie = movie["imdbID"]

# Fetch and display full details for selected movie
if st.session_state.selected_movie:
    with st.spinner("Loading details..."):
        url = f"http://www.omdbapi.com/?i={st.session_state.selected_movie}&apikey={api_key}"
        response = requests.get(url)
        data = response.json()

    if data.get("Response") == "True":
        st.divider()
        col1, col2 = st.columns([1, 2])

        with col1:
            if data.get("Poster") and data["Poster"] != "N/A":
                st.image(data["Poster"], width=200)

        with col2:
            st.header(data.get("Title", "N/A"))
            st.caption(f"{data.get('Year', 'N/A')} | {data.get('Rated', 'N/A')} | {data.get('Runtime', 'N/A')}")
            st.markdown(f"**Genre:** {data.get('Genre', 'N/A')}")
            st.markdown(f"**Director:** {data.get('Director', 'N/A')}")
            st.markdown(f"**Actors:** {data.get('Actors', 'N/A')}")
            st.markdown(f"**IMDb Rating:** ⭐ {data.get('imdbRating', 'N/A')}/10")

        st.subheader("Plot")
        st.write(data.get("Plot", "N/A"))

        with st.expander("More Details"):
            st.markdown(f"**Writer:** {data.get('Writer', 'N/A')}")
            st.markdown(f"**Language:** {data.get('Language', 'N/A')}")
            st.markdown(f"**Country:** {data.get('Country', 'N/A')}")
            st.markdown(f"**Awards:** {data.get('Awards', 'N/A')}")
            st.markdown(f"**Box Office:** {data.get('BoxOffice', 'N/A')}")
