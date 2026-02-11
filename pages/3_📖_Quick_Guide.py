import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Quick Guide", page_icon="📖", layout="wide")

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

st.title("📖 Quick Guide")

st.markdown("Get budget estimates for your project in 2 simple steps.")

st.divider()

# Step 1
st.subheader("Step 1: Build Your Comp Library")
st.markdown("""
1. Go to **🔍 Title Search**
2. Search for films similar to your project
3. Click **Save to Library** on relevant titles
4. Aim for **5-10 comparable titles** for best results
""")

st.markdown("""
**What data is used?**

Each title includes metadata from **TMDb (The Movie Database)** — genre, release date, runtime, and production budget.
When you save a title, our system also analyzes its production attributes like VFX intensity, star power, and action complexity
to build a rich profile for comparison.
""")

st.info("💡 **Tip:** Save titles with known budgets that match your genre, scale, and style.")

st.divider()

# Step 2
st.subheader("Step 2: Get Your Estimate")
st.markdown("""
1. Go to **💰 Cost Estimator**
2. Select your project's 10 attributes
3. Click **Find Comparable Titles & Estimate**
4. Review your budget range based on similar productions
""")

st.markdown("""
**How does the matching work?**

Our **data science model** scans your saved library and scores each title based on how closely it matches
your project's attributes. The algorithm weighs multiple factors:

- **Genre & Format** — Primary genre match is weighted heavily
- **Production Scale** — Budget tier alignment (blockbuster vs. indie)
- **Creative Elements** — VFX, action complexity, period setting, star power
- **Recency** — Recent titles (last 1-2 years) are weighted more heavily since they reflect current market costs

The top matches are then combined into a **weighted average**, giving you a data-driven budget range
based on real production costs.
""")

st.info("💡 **Tip:** Hover over the (?) icons for guidance on each field.")

st.divider()

st.markdown("**That's it!** With a curated comp library and our similarity model, you get budget estimates grounded in real production data — not guesswork.")
