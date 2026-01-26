import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
import base64

load_dotenv()

def svg_to_data_uri(svg_string):
    """Convert SVG string to base64 data URI for reliable rendering."""
    b64 = base64.b64encode(svg_string.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"

# SVG Icons - using data URIs to avoid Streamlit's HTML case sensitivity issues
SEARCH_ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="10" cy="10" r="7"/>
  <line x1="15" y1="15" x2="21" y2="21"/>
  <polyline points="7,13 10,10 13,13"/>
</svg>'''

DOLLAR_ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>
</svg>'''

CHECK_ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="14" height="14">
  <path d="M3 8l3 3 7-7" stroke="#38a169" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

st.set_page_config(
    page_title="Production Intelligence Tools",
    page_icon="🎬",
    layout="wide"
)

# Google Analytics
HEAD_CONTENT = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-7J88HTR1H2"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-7J88HTR1H2');
</script>
"""
components.html(HEAD_CONTENT, height=0)

# Professional Home Page Styling
HOME_STYLES = """
<style>
/* Fix Streamlit dark background - apply light background to entire page */
.stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%) !important;
}

/* Hide default Streamlit header spacing */
.block-container {
    padding-top: 1rem;
}

/* Hero Section */
.hero-section {
    text-align: center;
    padding: 2.5rem 2rem;
    background: transparent !important;
    margin-bottom: 1.5rem;
}

.hero-title {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1e3a5f !important;
    margin-bottom: 0.5rem;
}

.hero-subtitle {
    font-size: 1.15rem;
    color: #4a5568 !important;
    margin-bottom: 0.75rem;
}

.hero-author {
    font-size: 0.95rem;
    color: #718096 !important;
    margin: 0;
}

/* Product Cards Container */
.cards-container {
    display: flex;
    gap: 2rem;
    margin-bottom: 2rem;
}

/* Product Card */
.product-card {
    flex: 1;
    background: white !important;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.product-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12), 0 4px 8px rgba(0, 0, 0, 0.08);
}

.icon-container {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1.5rem;
    font-size: 2rem;
    color: white;
}

.icon-search {
    background: linear-gradient(135deg, #2d5a87 0%, #1e3a5f 100%);
}

.icon-estimate {
    background: linear-gradient(135deg, #38a169 0%, #276749 100%);
}

.card-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #2d3748 !important;
    text-align: center;
    margin-bottom: 1rem;
}

.card-description {
    color: #4a5568 !important;
    text-align: center;
    margin-bottom: 1.25rem;
    line-height: 1.6;
}

.card-section {
    margin-bottom: 1.25rem;
}

.section-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #1e3a5f !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.5rem;
}

.section-text {
    color: #4a5568 !important;
    font-size: 0.9rem;
    line-height: 1.5;
    margin: 0;
}

.features-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.features-list li {
    padding: 0.3rem 0;
    color: #4a5568 !important;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

.icon-container img {
    width: 36px;
    height: 36px;
}

.check-icon {
    width: 14px;
    height: 14px;
    flex-shrink: 0;
}

.cta-button {
    display: block;
    width: 100%;
    padding: 14px 24px;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    text-align: center;
    text-decoration: none;
    cursor: pointer;
    transition: background 0.3s ease;
}

.cta-search {
    background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%) !important;
    color: white !important;
}

.cta-search:hover {
    background: linear-gradient(90deg, #2d5a87 0%, #1e3a5f 100%) !important;
    color: white !important;
}

.cta-estimate {
    background: linear-gradient(90deg, #38a169 0%, #276749 100%) !important;
    color: white !important;
}

.cta-estimate:hover {
    background: linear-gradient(90deg, #276749 0%, #38a169 100%) !important;
    color: white !important;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
    .cards-container {
        flex-direction: column;
    }

    .hero-title {
        font-size: 2rem;
    }
}
</style>
"""

# Hero Section HTML
HERO_SECTION = """
<div class="hero-section">
    <div class="hero-title">Production Intelligence Tools</div>
    <p class="hero-subtitle">Budget research for entertainment professionals</p>
    <p class="hero-author">Built by Yunbo Cheng</p>
</div>
"""

# Product Cards HTML - using f-string to interpolate data URIs
SEARCH_ICON_URI = svg_to_data_uri(SEARCH_ICON_SVG)
DOLLAR_ICON_URI = svg_to_data_uri(DOLLAR_ICON_SVG)
CHECK_ICON_URI = svg_to_data_uri(CHECK_ICON_SVG)

# Render the home page
st.markdown(HOME_STYLES, unsafe_allow_html=True)
st.markdown(HERO_SECTION, unsafe_allow_html=True)

# Product Cards using native Streamlit components
col1, col2 = st.columns(2)

with col1:
    st.markdown(f'''
<div style="background: white; border-radius: 16px; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.07);">
<div style="width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #2d5a87, #1e3a5f); display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem;">
<img src="{SEARCH_ICON_URI}" style="width: 36px; height: 36px;">
</div>
<div style="font-size: 1.5rem; font-weight: 600; color: #2d3748; text-align: center; margin-bottom: 0.5rem;">Title Search</div>
<p style="color: #718096; text-align: center; margin-bottom: 1.25rem; font-size: 0.95rem;">Research any title in seconds — not hours.</p>
<div style="margin-bottom: 1rem;">
<div style="font-size: 0.8rem; font-weight: 600; color: #1e3a5f; text-transform: uppercase; margin-bottom: 0.5rem;">Features</div>
<div style="color: #4a5568; font-size: 0.9rem;">✓ Budget & box office data<br>✓ Revenue, profit & ROI<br>✓ Cast & crew credits<br>✓ Production attributes</div>
</div>
<div style="margin-bottom: 1rem;">
<div style="font-size: 0.8rem; font-weight: 600; color: #1e3a5f; text-transform: uppercase; margin-bottom: 0.5rem;">How It Works</div>
<div style="color: #4a5568; font-size: 0.9rem;">Search by title → Instant budget, revenue & credits.</div>
</div>
</div>
''', unsafe_allow_html=True)
    if st.button("🔍 Search Titles", key="search_btn", use_container_width=True):
        st.switch_page("pages/1_🔍_Title_Search.py")

with col2:
    st.markdown(f'''
<div style="background: white; border-radius: 16px; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.07);">
<div style="width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #38a169, #276749); display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem;">
<img src="{DOLLAR_ICON_URI}" style="width: 36px; height: 36px;">
</div>
<div style="font-size: 1.5rem; font-weight: 600; color: #2d3748; text-align: center; margin-bottom: 0.5rem;">Cost Estimator</div>
<p style="color: #718096; text-align: center; margin-bottom: 1.25rem; font-size: 0.95rem;">Find comp titles in minutes — not days.</p>
<div style="margin-bottom: 1rem;">
<div style="font-size: 0.8rem; font-weight: 600; color: #1e3a5f; text-transform: uppercase; margin-bottom: 0.5rem;">Features</div>
<div style="color: #4a5568; font-size: 0.9rem;">✓ Define 10 project attributes<br>✓ Auto-match similar productions<br>✓ Get budget range estimates<br>✓ Inflation-adjusted to 2024</div>
</div>
<div style="margin-bottom: 1rem;">
<div style="font-size: 0.8rem; font-weight: 600; color: #1e3a5f; text-transform: uppercase; margin-bottom: 0.5rem;">How It Works</div>
<div style="color: #4a5568; font-size: 0.9rem;">Set your project's genre, cast tier, VFX level → Get comparable titles with real budget data.</div>
</div>
</div>
''', unsafe_allow_html=True)
    if st.button("💰 Estimate Costs", key="estimate_btn", use_container_width=True):
        st.switch_page("pages/2_💰_Cost_Estimator.py")

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
