import os
import json
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Production Cost Estimator",
    page_icon="🎬",
    layout="wide"
)

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

# Load database stats
db_path = os.path.join(os.path.dirname(__file__), "data", "titles_db.json")
try:
    with open(db_path, "r") as f:
        db = json.load(f)
    title_count = len(db.get("titles", []))
except (FileNotFoundError, json.JSONDecodeError):
    title_count = 0

if title_count > 0:
    st.info(f"📊 **Database Status:** {title_count} titles saved")
else:
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
