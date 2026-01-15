import os
import json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Production Cost Estimator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Production Cost Estimator")

st.markdown("""
Welcome to the Production Cost Estimator! This tool helps you:

1. **🔍 Search Titles** - Look up movies and TV shows to see their budget, revenue, cast, and crew
2. **💰 Estimate Costs** - Get production cost estimates based on comparable titles

---

### Getting Started

Use the sidebar to navigate between pages:
- **Title Search** - Search for movies/TV shows and save them to build your comparison database
- **Cost Estimator** - Enter show attributes to find comparables and estimate production costs

""")

# Show database stats
db_path = os.path.join(os.path.dirname(__file__), "data", "titles_db.json")
try:
    with open(db_path, "r") as f:
        db = json.load(f)
    title_count = len(db.get("titles", []))
    st.info(f"📊 **Database Status:** {title_count} titles saved")
except (FileNotFoundError, json.JSONDecodeError):
    st.warning("📊 **Database Status:** No titles saved yet. Use Title Search to build your database!")

st.markdown("""
---

### How It Works

1. **Search** for movies/TV shows using the Title Search page
2. **Save** interesting titles to your local database
3. **Estimate** costs by selecting attributes in the Cost Estimator
4. **Compare** your project to similar titles with known budgets

""")

# Sidebar
with st.sidebar:
    st.header("API Key")
    tmdb_key = st.text_input(
        "TMDb API Key",
        value=os.getenv("TMDB_API_KEY", ""),
        type="password",
        key="tmdb_key_home"
    )
    st.markdown("[Get free API key](https://www.themoviedb.org/settings/api)")
    st.divider()
    st.caption("Data from [TMDb](https://www.themoviedb.org)")
