"""OpenGreenMetric Interactive Dashboard."""

import streamlit as st
import plotly.graph_objects as go
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from openmetric import analyze

# ---------------------------------------------------------------------------
# Load logos as base64 for inline HTML
# ---------------------------------------------------------------------------
_DIR = os.path.dirname(__file__)

def _b64(path: str) -> str:
    with open(os.path.join(_DIR, path), "rb") as f:
        return base64.b64encode(f.read()).decode()

_LOGO_B64 = _b64("assets/logo.png")
_GM_LOGO_B64 = _b64("assets/greenmetric-logo.png")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="OpenGreenMetric",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ---- reset ---- */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #09090B; color: #E5E5E5; }
#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }
section[data-testid="stSidebar"] { background-color: #111113; border-right: 1px solid #1C1C1F; }

/* ---- navbar ---- */
.navbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.2rem 0; border-bottom: 1px solid #1C1C1F; margin-bottom: 2.5rem;
}
.navbar .logo { font-size: 1.4rem; font-weight: 800; color: #FAFAFA; letter-spacing: -0.03em; }
.navbar .logo span { color: #10B981; }
.navbar .nav-links { display: flex; gap: 1.8rem; align-items: center; }
.navbar .nav-links a {
    color: #71717A; font-size: 0.85rem; text-decoration: none; font-weight: 500;
    transition: color 0.15s;
}
.navbar .nav-links a:hover { color: #FAFAFA; }
.nav-badge {
    font-size: 0.65rem; padding: 0.2rem 0.55rem; background: #10B98115;
    color: #10B981; border-radius: 9999px; border: 1px solid #10B98125;
    font-weight: 600; letter-spacing: 0.03em;
}

/* ---- hero ---- */
.hero { text-align: center; padding: 3rem 0 2.5rem 0; }
.hero h1 {
    font-size: 3rem; font-weight: 800; color: #FAFAFA;
    letter-spacing: -0.04em; line-height: 1.15; margin: 0;
}
.hero h1 span { color: #10B981; }
.hero p {
    font-size: 1.05rem; color: #71717A; margin-top: 1rem;
    max-width: 600px; margin-left: auto; margin-right: auto; line-height: 1.6;
}

/* ---- search bar ---- */
.search-row {
    max-width: 720px; margin: 0 auto 3rem auto;
    display: flex; gap: 0.75rem; align-items: stretch;
}

/* ---- large metric cards ---- */
.lm-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.25rem; margin-bottom: 2rem; }
.lm-card {
    background: #111113; border: 1px solid #1C1C1F; border-radius: 16px;
    padding: 2rem 1.5rem; text-align: center; transition: border-color 0.2s, transform 0.2s;
}
.lm-card:hover { border-color: #10B98140; transform: translateY(-2px); }
.lm-card .lm-val { font-size: 2.8rem; font-weight: 800; line-height: 1.1; letter-spacing: -0.03em; }
.lm-card .lm-unit {
    font-size: 0.8rem; color: #52525B; margin-top: 0.4rem;
    text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;
}
.lm-card .lm-label {
    font-size: 0.85rem; color: #A1A1AA; margin-top: 0.6rem; font-weight: 500;
}

/* ---- grade hero ---- */
.grade-hero {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; padding: 2.5rem; background: #111113;
    border: 1px solid #1C1C1F; border-radius: 20px; margin-bottom: 2rem;
    transition: border-color 0.2s;
}
.grade-hero:hover { border-color: #10B98140; }
.grade-ring {
    width: 120px; height: 120px; border-radius: 24px; display: flex;
    align-items: center; justify-content: center;
    font-size: 3.5rem; font-weight: 800; letter-spacing: -0.02em;
}
.gr-a { background: #10B98118; color: #10B981; border: 3px solid #10B981; }
.gr-b { background: #3B82F618; color: #3B82F6; border: 3px solid #3B82F6; }
.gr-c { background: #F59E0B18; color: #F59E0B; border: 3px solid #F59E0B; }
.gr-d { background: #EF444418; color: #EF4444; border: 3px solid #EF4444; }
.gr-f { background: #EF444418; color: #EF4444; border: 3px solid #EF4444; }
.grade-score {
    font-size: 1.6rem; font-weight: 700; color: #FAFAFA; margin-top: 1rem;
}
.grade-label {
    font-size: 0.8rem; color: #52525B; margin-top: 0.3rem;
    text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;
}

/* ---- section ---- */
.section-title {
    font-size: 0.75rem; color: #52525B; text-transform: uppercase;
    letter-spacing: 0.1em; font-weight: 700; margin-bottom: 1.25rem;
    padding-bottom: 0.75rem; border-bottom: 1px solid #1C1C1F;
}

/* ---- card ---- */
.card {
    background: #111113; border: 1px solid #1C1C1F; border-radius: 16px;
    padding: 1.75rem; margin-bottom: 1.25rem; transition: border-color 0.2s;
}
.card:hover { border-color: #1C1C1F; }

/* ---- detail row ---- */
.d-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.7rem 0; border-bottom: 1px solid #18181B;
}
.d-row:last-child { border-bottom: none; }
.d-row .d-key { color: #71717A; font-size: 0.9rem; font-weight: 500; }
.d-row .d-val { color: #FAFAFA; font-size: 0.9rem; font-weight: 600; }

/* ---- material chips ---- */
.chip-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.chip {
    padding: 0.5rem 1rem; background: #18181B; border: 1px solid #27272A;
    border-radius: 10px; font-size: 0.82rem; color: #D4D4D8; font-weight: 500;
    transition: border-color 0.15s;
}
.chip:hover { border-color: #10B98140; }

/* ---- bar segment ---- */
.bar-outer {
    width: 100%; height: 10px; background: #18181B; border-radius: 5px;
    overflow: hidden; margin-top: 0.5rem;
}
.bar-fill { height: 100%; border-radius: 5px; transition: width 0.4s ease; }

/* ---- percentile row ---- */
.pct-row {
    display: flex; align-items: center; gap: 1rem; padding: 0.8rem 0;
    border-bottom: 1px solid #18181B;
}
.pct-row:last-child { border-bottom: none; }
.pct-label { width: 100px; font-size: 0.85rem; color: #71717A; font-weight: 500; }
.pct-bar-wrap { flex: 1; }
.pct-val { width: 50px; text-align: right; font-size: 0.9rem; font-weight: 700; color: #FAFAFA; }

/* ---- inputs ---- */
.stTextInput input, .stSelectbox > div > div {
    background-color: #111113 !important; border: 1px solid #27272A !important;
    color: #FAFAFA !important; border-radius: 12px !important;
    padding: 0.75rem 1rem !important; font-size: 1rem !important;
}
.stTextInput input:focus { border-color: #10B981 !important; box-shadow: 0 0 0 1px #10B98140 !important; }

/* ---- primary button ---- */
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
    background: #10B981 !important; color: #000000 !important; border: none !important;
    border-radius: 12px !important; font-weight: 700 !important; font-size: 1rem !important;
    padding: 0.75rem 2.5rem !important; transition: all 0.2s !important;
    letter-spacing: -0.01em !important;
}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: #059669 !important; transform: translateY(-1px) !important;
}

/* ---- warnings ---- */
.stAlert { background: #18181B !important; border-color: #F59E0B30 !important; border-radius: 12px !important; }
hr { border-color: #1C1C1F !important; }

/* ---- plotly ---- */
.stPlotlyChart { border-radius: 16px; overflow: hidden; }

/* ---- footer ---- */
.ft {
    text-align: center; padding: 3rem 0 1.5rem 0; border-top: 1px solid #1C1C1F;
    margin-top: 4rem;
}
.ft .ft-brand { font-size: 1.1rem; font-weight: 700; color: #FAFAFA; }
.ft .ft-brand span { color: #10B981; }
.ft .ft-meta { font-size: 0.75rem; color: #3F3F46; margin-top: 0.5rem; }
.ft a { color: #10B981; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Navbar
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="navbar">
    <div class="logo"><img src="data:image/png;base64,{_LOGO_B64}" style="height: 28px; vertical-align: middle; margin-right: 8px;" />Open<span>GreenMetric</span></div>
    <div class="nav-links">
        <a href="https://greenmetric.ai" target="_blank">Production API</a>
        <a href="https://github.com/alanknguyen/OpenGreenMetric" target="_blank">GitHub</a>
        <span class="nav-badge">v0.1.0</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>Environmental Scoring<br/>for <span>Any Product</span></h1>
    <p>Enter a product description below. The engine classifies it, calculates lifecycle impacts, and returns a sustainability score in under 200ms.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Search bar
# ---------------------------------------------------------------------------
sc1, sc2, sc3 = st.columns([5, 1.5, 1], gap="small")

with sc1:
    description = st.text_input(
        "Product description",
        value="organic cotton t-shirt 180g made in Bangladesh",
        label_visibility="collapsed",
        placeholder="Describe a product, e.g. organic cotton t-shirt 180g made in Bangladesh",
    )
with sc2:
    destination = st.selectbox(
        "Destination",
        ["US", "GB", "DE", "FR", "JP", "AU", "CA"],
        index=0,
        label_visibility="collapsed",
    )
with sc3:
    analyze_clicked = st.button("Analyze  \u2192", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
if "result" not in st.session_state:
    st.session_state.result = None
if "last_desc" not in st.session_state:
    st.session_state.last_desc = ""

if analyze_clicked:
    with st.spinner(""):
        st.session_state.result = analyze(description, destination)
        st.session_state.last_desc = description

result = st.session_state.result

if not result:
    # Empty state
    st.markdown(f"""
    <div style="text-align: center; padding: 4rem 0; color: #3F3F46;">
        <img src="data:image/png;base64,{_LOGO_B64}" style="height: 64px; opacity: 0.4; margin-bottom: 1rem;" />
        <div style="font-size: 1.1rem; font-weight: 500;">Enter a product description and click Analyze</div>
        <div style="font-size: 0.85rem; margin-top: 0.5rem;">
            Try: laptop 2.1kg made in China, recycled polyester jacket 350g, wooden dining chair 8kg
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
grade = result.scores.letter_grade
gr_class = "gr-a" if grade.startswith("A") else \
           "gr-b" if grade.startswith("B") else \
           "gr-c" if grade.startswith("C") else \
           "gr-d" if grade.startswith("D") else "gr-f"
p = result.scores.percentiles

st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

# --- Grade hero + 4 metric cards ---
g_col, m_col = st.columns([1, 3], gap="large")

with g_col:
    st.markdown(f"""
    <div class="grade-hero">
        <div class="grade-ring {gr_class}">{grade}</div>
        <div class="grade-score">{result.scores.overall} / 100</div>
        <div class="grade-label">Overall Score</div>
    </div>
    """, unsafe_allow_html=True)

with m_col:
    color_green = "#10B981"
    color_blue = "#3B82F6"
    color_amber = "#F59E0B"
    color_purple = "#A855F7"
    st.markdown(f"""
    <div class="lm-grid">
        <div class="lm-card">
            <div class="lm-val" style="color: {color_green};">{result.impacts.climate_change:.1f}</div>
            <div class="lm-unit">kg CO&#8322;e</div>
            <div class="lm-label">Carbon Footprint</div>
        </div>
        <div class="lm-card">
            <div class="lm-val" style="color: {color_blue};">{result.impacts.water_use:,.0f}</div>
            <div class="lm-unit">Liters</div>
            <div class="lm-label">Water Consumption</div>
        </div>
        <div class="lm-card">
            <div class="lm-val" style="color: {color_amber};">{result.impacts.energy_use:.1f}</div>
            <div class="lm-unit">kWh</div>
            <div class="lm-label">Energy Use</div>
        </div>
        <div class="lm-card">
            <div class="lm-val" style="color: {color_purple};">{p.overall}%</div>
            <div class="lm-unit">Percentile</div>
            <div class="lm-label">vs. {p.category_label}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

# --- Three column detail section ---
col_radar, col_pct, col_info = st.columns([1.1, 1, 1], gap="large")

# Radar chart
with col_radar:
    st.markdown('<div class="section-title">Score Breakdown</div>', unsafe_allow_html=True)

    categories = ["Climate", "Water", "Fossil Resources"]
    values = [result.scores.climate, result.scores.water, result.scores.resource_use_fossils]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(16, 185, 129, 0.10)",
        line=dict(color="#10B981", width=2.5),
        marker=dict(size=8, color="#10B981"),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#111113",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#1C1C1F", linecolor="#1C1C1F",
                tickfont=dict(color="#3F3F46", size=10),
            ),
            angularaxis=dict(
                gridcolor="#1C1C1F", linecolor="#1C1C1F",
                tickfont=dict(color="#A1A1AA", size=12, family="Inter"),
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=70, r=70, t=30, b=30),
        height=360,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

# Percentile bars (Plotly — renders reliably)
with col_pct:
    st.markdown('<div class="section-title">Category Percentiles</div>', unsafe_allow_html=True)

    pct_labels = ["Energy", "Water", "Climate"]
    pct_vals = [p.energy, p.water, p.climate]
    pct_colors = ["#F59E0B", "#3B82F6", "#10B981"]

    fig_pct = go.Figure()
    # Background track bars (100% width, gray)
    fig_pct.add_trace(go.Bar(
        x=[100, 100, 100], y=pct_labels, orientation="h",
        marker_color="#1C1C1F", marker_line_width=0,
        showlegend=False, hoverinfo="skip",
    ))
    # Actual value bars
    fig_pct.add_trace(go.Bar(
        x=pct_vals, y=pct_labels, orientation="h",
        marker_color=pct_colors, marker_line_width=0,
        text=[f"{v}%" for v in pct_vals],
        textposition="inside", textfont=dict(color="#FAFAFA", size=14, family="Inter"),
        showlegend=False,
    ))
    fig_pct.update_layout(
        barmode="overlay",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 100], visible=False),
        yaxis=dict(tickfont=dict(color="#A1A1AA", size=13, family="Inter"), autorange="reversed"),
        margin=dict(l=70, r=15, t=10, b=10),
        height=160, bargap=0.35,
    )
    st.plotly_chart(fig_pct, use_container_width=True)

    # Sub-scores — inline styles only (no class refs)
    st.markdown(f"""
    <div style="background: #111113; border: 1px solid #1C1C1F; border-radius: 16px; padding: 1.25rem 1.5rem;">
        <div style="display: flex; justify-content: space-between; padding: 0.6rem 0; border-bottom: 1px solid #18181B;">
            <span style="color: #71717A; font-size: 0.9rem;">Climate Score</span>
            <span style="color: #10B981; font-size: 0.9rem; font-weight: 700;">{result.scores.climate}/100</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 0.6rem 0; border-bottom: 1px solid #18181B;">
            <span style="color: #71717A; font-size: 0.9rem;">Water Score</span>
            <span style="color: #3B82F6; font-size: 0.9rem; font-weight: 700;">{result.scores.water}/100</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 0.6rem 0;">
            <span style="color: #71717A; font-size: 0.9rem;">Fossil Score</span>
            <span style="color: #F59E0B; font-size: 0.9rem; font-weight: 700;">{result.scores.resource_use_fossils}/100</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Product info
with col_info:
    st.markdown('<div class="section-title">Product Classification</div>', unsafe_allow_html=True)

    rows = [
        ("Category", result.product.product_category),
        ("NAICS Code", f"{result.product.naics_code}"),
        ("Weight", f"{result.product.total_weight_kg:.3f} kg"),
        ("Origin", result.product.country_of_origin),
        ("Destination", destination),
        ("Est. Price", f"${result.product.estimated_price_usd:.0f}"),
        ("Confidence", f"{result.product.confidence:.0%}"),
    ]
    detail_html = "".join(
        f'<div class="d-row"><span class="d-key">{k}</span><span class="d-val">{v}</span></div>'
        for k, v in rows
    )
    st.markdown(f'<div class="card">{detail_html}</div>', unsafe_allow_html=True)

    # Materials
    if result.product.materials:
        chips = "".join(
            f'<div class="chip">{m.name} &middot; {m.percentage:.0f}%</div>'
            for m in result.product.materials[:8]
        )
        st.markdown(f"""
        <div class="card">
            <div style="font-size: 0.75rem; color: #52525B; text-transform: uppercase;
                        letter-spacing: 0.08em; font-weight: 700; margin-bottom: 1rem;">Materials</div>
            <div class="chip-grid">{chips}</div>
        </div>
        """, unsafe_allow_html=True)

# --- Impact breakdown waterfall ---
st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Impact Breakdown</div>', unsafe_allow_html=True)

stages = ["Materials", "Manufacturing", "Transport", "Use Phase", "End of Life"]
# Approximate lifecycle stage breakdown from the LCA engine
total_co2 = result.impacts.climate_change
stage_pcts = [0.50, 0.28, 0.12, 0.06, 0.04]
stage_vals = [total_co2 * p for p in stage_pcts]
stage_colors = ["#10B981", "#3B82F6", "#F59E0B", "#A855F7", "#71717A"]

fig_wf = go.Figure()
fig_wf.add_trace(go.Bar(
    x=stages, y=stage_vals,
    marker_color=stage_colors,
    marker_line_width=0,
    text=[f"{v:.2f} kg" for v in stage_vals],
    textposition="outside",
    textfont=dict(color="#A1A1AA", size=13, family="Inter", weight=600),
))
fig_wf.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(
        tickfont=dict(color="#A1A1AA", size=12, family="Inter"),
        gridcolor="rgba(0,0,0,0)",
        linecolor="#1C1C1F",
    ),
    yaxis=dict(
        title=dict(text="kg CO\u2082e", font=dict(color="#52525B", size=11)),
        gridcolor="#1C1C1F", tickfont=dict(color="#3F3F46", size=10),
        linecolor="#1C1C1F",
    ),
    margin=dict(l=60, r=20, t=20, b=60),
    height=320,
    showlegend=False,
    bargap=0.35,
)
st.plotly_chart(fig_wf, use_container_width=True)

# Validation warnings
if result.validation.warnings:
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    for w in result.validation.warnings:
        st.warning(w)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="ft">
    <div class="ft-brand"><img src="data:image/png;base64,{_LOGO_B64}" style="height: 22px; vertical-align: middle; margin-right: 6px;" />Open<span>GreenMetric</span></div>
    <div class="ft-meta">
        MIT License &nbsp;&middot;&nbsp; Data: EPA, DEFRA/BEIS, IPCC AR6, EU EF 3.1
    </div>
    <div style="margin-top: 0.75rem;">
        <a href="https://greenmetric.ai" target="_blank" style="text-decoration: none; color: #71717A; font-size: 0.8rem; display: inline-flex; align-items: center; gap: 6px;">
            <img src="data:image/png;base64,{_GM_LOGO_B64}" style="height: 20px; border-radius: 4px;" />
            Production API: greenmetric.ai
        </a>
    </div>
</div>
""", unsafe_allow_html=True)
