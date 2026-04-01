"""
Northstar Analytics — MyEyeDr Anomaly Detection Dashboard
Interactive Streamlit Dashboard for Stakeholder Presentation
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="MyEyeDr Anomaly Detection",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# NORTHSTAR ANALYTICS BRANDING
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* ═══════════════════════════════════════════════════════════════════
       MODERN PROFESSIONAL DASHBOARD DESIGN SYSTEM
       ═══════════════════════════════════════════════════════════════════ */
    
    /* ─── HIDE DEFAULT STREAMLIT ELEMENTS ─── */
    #MainMenu {display: none;}
    footer {display: none;}
    header {display: none;}
    
    /* Style the sidebar collapse/expand button as a clean blue button */
    [data-testid="collapsedControl"] {
        background: #1E7BC0 !important;
        border-radius: 0 8px 8px 0 !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(30, 123, 192, 0.3) !important;
        padding: 8px 4px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
    }

    [data-testid="collapsedControl"] span {
        font-size: 0 !important;
        display: block !important;
        width: 20px !important;
        height: 24px !important;
        position: relative !important;
        visibility: hidden !important;
    }

    [data-testid="collapsedControl"] span::after {
        content: '>' !important;
        visibility: visible !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        color: white !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ─── ROOT & GENERAL STYLING ─── */
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
    }
    
    body {
        background-color: #F7F9FC;
        color: #2C3E50;
    }
    
    .main {
        padding-top: 90px;
        background-color: #F7F9FC;
    }
    
    /* ─── HEADER STYLING ─── */
    .header-container {
        position: fixed;
        top: 0;
        left: 336px;
        right: 0;
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        padding: 1rem 2.5rem;
        border-bottom: 1px solid #E5E9F0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 999;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    
    .header-left {
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
    }
    
    .header-title {
        color: #1A365D;
        font-weight: 800;
        font-size: 24px;
        letter-spacing: 2px;
        margin: 0;
        text-transform: uppercase;
    }
    
    .header-subtitle {
        color: #667A8C;
        font-size: 12px;
        margin: 0;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    
    .header-right {
        color: #8B95A5;
        font-size: 12px;
        text-align: right;
        font-weight: 500;
    }
    
    /* ─── SIDEBAR STYLING ─── */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1A365D 0%, #2C5282 100%);
    }
    
    [data-testid="stSidebar"] > div > div:first-child {
        background: inherit;
    }
    
    [data-testid="stSidebar"] label {
        color: #E8EFF6 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    
    [data-testid="stSidebar"] .css-1d391kg,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #D1DCE8 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="selectbox"],
    [data-testid="stSidebar"] [data-testid="textinput"],
    [data-testid="stSidebar"] [data-testid="checkbox"] {
        margin-bottom: 1rem;
    }
    
    /* ─── TAB STYLING ─── */
    [data-testid="stTabs"] {
        background-color: transparent !important;
    }
    
    [data-testid="stTabs"] > div {
        background-color: transparent !important;
    }
    
    [data-testid="stTabs"] button {
        color: #667A8C !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        background-color: transparent !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.3s ease !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    [data-testid="stTabs"] button:hover {
        color: #1A365D !important;
        border-bottom: 2px solid #E5E9F0 !important;
    }
    
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #1E7BC0 !important;
        border-bottom: 2px solid #1E7BC0 !important;
        font-weight: 700 !important;
    }
    
    /* Disable Material Icons rendering */
    .material-icons, [class*="material-icon"], [class*="icon"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    /* ─── METRIC CONTAINERS ─── */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E5E9F0;
        border-radius: 8px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
    }
    
    /* ─── HEADING STYLING ─── */
    h1 {
        color: #1A365D !important;
        font-weight: 700 !important;
        margin: 1.5rem 0 0.75rem 0 !important;
        font-size: 28px !important;
    }
    
    h2 {
        color: #2C5282 !important;
        font-weight: 600 !important;
        margin: 1.25rem 0 0.75rem 0 !important;
        font-size: 20px !important;
    }
    
    h3 {
        color: #2C5282 !important;
        font-weight: 600 !important;
        margin: 1rem 0 0.5rem 0 !important;
        font-size: 16px !important;
    }
    
    /* ─── TEXT STYLING ─── */
    p {
        color: #4A5F7F !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
    }
    
    /* ─── DIVIDER ─── */
    hr {
        border: none;
        border-top: 1px solid #E5E9F0 !important;
        margin: 2rem 0 !important;
    }
    
    /* ─── BUTTONS ─── */
    button {
        background-color: #1E7BC0 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    button:hover {
        background-color: #165A96 !important;
        box-shadow: 0 4px 12px rgba(30, 123, 192, 0.3) !important;
    }
    
    /* ─── EXPANDER ─── */
    [data-testid="stExpander"] {
        border: 1px solid #E5E9F0 !important;
        border-radius: 6px !important;
    }
    
    [data-testid="stExpander"] summary {
        background-color: #F8FAFC !important;
        font-weight: 600 !important;
    }
    
    /* ─── DATAFRAME ─── */
    [data-testid="stDataFrame"] {
        border-radius: 6px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* ─── INPUT FIELDS ─── */
    input, select, textarea {
        border-radius: 6px !important;
        border: 1px solid #D1DCE8 !important;
        font-size: 14px !important;
        padding: 0.75rem !important;
    }
    
    input:focus, select:focus, textarea:focus {
        border: 1px solid #1E7BC0 !important;
        box-shadow: 0 0 0 3px rgba(30, 123, 192, 0.1) !important;
    }
    
</style>

<div class="header-container">
    <div class="header-left">
        <div class="header-title">📊 NORTHSTAR</div>
        <div class="header-subtitle">MyEyeDr Analytics Platform</div>
    </div>
    <div class="header-right">
        SMU MSBA Capstone | Spring 2026 | Data as of <span id="header-date"></span>
    </div>
</div>
<script>
    const date = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    document.getElementById('header-date').textContent = date;
    
    // Function to remove Material Icon text elements
    function removeIconText() {
        const allElements = document.querySelectorAll('*');
        allElements.forEach(el => {
            const text = el.textContent ? el.textContent.trim() : '';
            
            // Remove if it contains keyboard_double_arrow_right or similar icon names
            if (text.includes('keyboard_double_arrow_right') || 
                text.match(/^[a-z_]{1,50}$/i) && text.includes('arrow')) {
                // Remove the element from DOM completely
                if (el.parentNode) {
                    el.parentNode.removeChild(el);
                }
            }
        });
    }
    
    // Run on load
    removeIconText();
    
    // Run after a delay to catch dynamically added elements
    setTimeout(removeIconText, 100);
    setTimeout(removeIconText, 300);
    setTimeout(removeIconText, 500);
    setTimeout(removeIconText, 1000);
    
    // Watch for mutations and remove icon text as they appear
    const observer = new MutationObserver(() => {
        removeIconText();
    });
    
    // Start observing the document for changes
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
</script>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    anomaly = pd.read_csv('med_anomaly_scores.csv')
    critical = pd.read_csv('med_critical_alerts.csv')
    watch = pd.read_csv('med_watch_list.csv')
    positive_outliers = pd.read_csv('med_positive_outliers.csv')

    # Convert date column
    anomaly['date'] = pd.to_datetime(anomaly['date'])
    critical['date'] = pd.to_datetime(critical['date'])
    watch['date'] = pd.to_datetime(watch['date'])
    positive_outliers['date'] = pd.to_datetime(positive_outliers['date'])

    # Rename "Critical Alert" → "Alert" in alert_tier column
    for df in [anomaly, critical, watch, positive_outliers]:
        if 'alert_tier' in df.columns:
            df['alert_tier'] = df['alert_tier'].replace('Critical Alert', 'Alert')

    return anomaly, critical, watch, positive_outliers

anomaly, critical, watch, positive_outliers = load_data()

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
st.sidebar.markdown("### 🎯 Filter Dashboard")
st.sidebar.markdown("---")

# Geographic Filters
st.sidebar.markdown("**📍 Geographic Filters**")
regions = sorted(anomaly['Region'].dropna().unique())
region_options = ["All Regions"] + list(regions)
selected_region = st.sidebar.selectbox("Region", region_options, index=0, key="region_filter")

states = sorted(anomaly['State'].dropna().unique())
state_options = ["All States"] + list(states)
selected_state = st.sidebar.selectbox("State", state_options, index=0, key="state_filter")

city_search = st.sidebar.text_input("🔍 City Search", "", placeholder="e.g., Houston, Austin...")

st.sidebar.markdown("---")

# Performance Filters
st.sidebar.markdown("**📊 Performance Filters**")
quads = sorted(anomaly['Quad'].dropna().unique())
quad_options = ["All Quads"] + list(quads)
selected_quad = st.sidebar.selectbox("Supply/Demand Quad", quad_options, index=0, key="quad_filter")

alert_tier_options = ["All Tiers", "Alert", "Watch", "Noise", "Clean"]
selected_alert_tier = st.sidebar.selectbox("Alert Tier", alert_tier_options, index=0, key="tier_filter")

st.sidebar.markdown("---")

# Location Type Filters
st.sidebar.markdown("**🏪 Location Type**")
medicaid_options = st.sidebar.checkbox("📋 Medicaid Locations Only", value=False)
tele_opt = st.sidebar.checkbox("💻 Tele-Opt Locations Only", value=False)

st.sidebar.markdown("---")

# Apply filters
if selected_region == "All Regions":
    region_filter = anomaly['Region'].isin(regions) | anomaly['Region'].isna()
else:
    region_filter = anomaly['Region'] == selected_region

if selected_quad == "All Quads":
    quad_filter = anomaly['Quad'].isin(quads) | anomaly['Quad'].isna()
else:
    quad_filter = anomaly['Quad'] == selected_quad

if selected_alert_tier == "All Tiers":
    alert_filter = anomaly['alert_tier'].isin(["Alert", "Watch", "Noise", "Clean"]) | anomaly['alert_tier'].isna()
else:
    alert_filter = anomaly['alert_tier'] == selected_alert_tier

if selected_state == "All States":
    state_filter = anomaly['State'].isin(states) | anomaly['State'].isna()
else:
    state_filter = anomaly['State'] == selected_state

filtered_data = anomaly[region_filter & quad_filter & alert_filter & state_filter]

if city_search.strip():
    filtered_data = filtered_data[filtered_data['City'].str.contains(city_search.strip(), case=False, na=False)]

if medicaid_options:
    filtered_data = filtered_data[filtered_data['is_medicaid'] == 1.0]

if tele_opt:
    filtered_data = filtered_data[filtered_data['is_tele_opt'] == 1.0]

# ─────────────────────────────────────────────
# NAVIGATION TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Executive Summary",
    "🚨  Alerts",
    "⚠️  Watch List",
    "📈  Regional Analysis",
    "🔍  Site Explorer"
])

# ═════════════════════════════════════════════
# TAB 1: EXECUTIVE SUMMARY
# ═════════════════════════════════════════════
with tab1:
    st.header("📊 Executive Summary")
    
    # Date info
    latest_date = anomaly['date'].max()
    st.markdown(f"<p style='color: #667A8C; font-size: 13px; margin-bottom: 1.5rem;'>Report Period: <strong>{latest_date.strftime('%B %d, %Y')}</strong></p>", unsafe_allow_html=True)
    
    # Key metrics - Single row with Total Sites + Alert boxes (consistent sizing)
    col1, col2, col3, col4 = st.columns(4)

    total_sites = len(filtered_data)
    critical_count = len(filtered_data[filtered_data['alert_tier'] == 'Alert'])
    watch_count = len(filtered_data[filtered_data['alert_tier'] == 'Watch'])
    noise_clean = len(filtered_data[filtered_data['alert_tier'].isin(['Noise', 'Clean'])])

    with col1:
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #E8F0F8 0%, #F0F4F8 100%); border-radius: 12px; border: 1px solid #D0E0F0; border-left: 5px solid #1E90FF;'><p style='font-size: 14px; color: #666; margin: 0 0 0.5rem 0;'>Total Sites Scored</p><p style='font-size: 26px; font-weight: bold; color: #1E90FF; margin: 0;'>{total_sites}</p></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold; margin: 0.8rem 0 0 0; color: #0B1F3F;'>All Locations<br><span style='font-size: 12px; font-weight: normal;'>Regular monitoring</span></p>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"<div style='background: linear-gradient(135deg, #FFE8E8 0%, #FFD6D6 100%); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(255, 68, 68, 0.2); border-left: 5px solid #FF4444; text-align: center;'><div style='font-size: 24px; font-weight: bold;'>🔴</div><div style='font-weight: bold; font-size: 13px; color: #0B1F3F; margin-top: 0.3rem;'>Alert</div><div style='font-size: 26px; color: #FF4444; font-weight: bold; margin-top: 0.5rem;'>{critical_count}</div><div style='font-size: 11px; color: #666; margin-top: 0.2rem;'>{critical_count/total_sites*100:.1f}% of total</div></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold; margin: 0.8rem 0 0 0; color: #0B1F3F;'>Weighted Score &ge; 4.0<br><span style='font-size: 12px; font-weight: normal;'>Immediate action required</span></p>", unsafe_allow_html=True)

    with col3:
        st.markdown(f"<div style='background: linear-gradient(135deg, #FFF8E8 0%, #FFF0D6 100%); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2); border-left: 5px solid #FFD700; text-align: center;'><div style='font-size: 24px; font-weight: bold;'>🟡</div><div style='font-weight: bold; font-size: 13px; color: #0B1F3F; margin-top: 0.3rem;'>Watch</div><div style='font-size: 26px; color: #FFD700; font-weight: bold; margin-top: 0.5rem;'>{watch_count}</div><div style='font-size: 11px; color: #666; margin-top: 0.2rem;'>{watch_count/total_sites*100:.1f}% of total</div></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold; margin: 0.8rem 0 0 0; color: #0B1F3F;'>Weighted Score &ge; 2.5<br><span style='font-size: 12px; font-weight: normal;'>Active monitoring</span></p>", unsafe_allow_html=True)

    with col4:
        st.markdown(f"<div style='background: linear-gradient(135deg, #E8FFE8 0%, #D6FFD6 100%); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(50, 205, 50, 0.2); border-left: 5px solid #32CD32; text-align: center;'><div style='font-size: 24px; font-weight: bold;'>🟢</div><div style='font-weight: bold; font-size: 13px; color: #0B1F3F; margin-top: 0.3rem;'>Clean/Noise</div><div style='font-size: 26px; color: #32CD32; font-weight: bold; margin-top: 0.5rem;'>{noise_clean}</div><div style='font-size: 11px; color: #666; margin-top: 0.2rem;'>{noise_clean/total_sites*100:.1f}% of total</div></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold; margin: 0.8rem 0 0 0; color: #0B1F3F;'>Score 0-1<br><span style='font-size: 12px; font-weight: normal;'>Normal variation</span></p>", unsafe_allow_html=True)

    st.divider()
    
    # ── Alert Performance Context: Positive vs Negative Breakdown ──
    st.subheader("Alert Performance Context: What's Driving the Alerts?")
    st.markdown("""
    Out of all **Alert-tier stores**, understanding the performance direction is critical:
    - **🔻 Negative-Performing** - Stores underperforming vs baseline (Z-score < -2σ) → **Need immediate intervention**
    - **🔺 Positive-Performing** - Stores outperforming vs baseline (Z-score > +2σ) → **Best-practice candidates, possible data quality issues, or extreme outliers**
    """)

    critical_sites = filtered_data[filtered_data['alert_tier'] == 'Alert'].copy()

    # Classify: a critical alert is "negative-performing" if its negative score dominates,
    # "positive-performing" if its positive score dominates
    neg_critical = critical_sites[critical_sites['weighted_negative_score'] > critical_sites['weighted_positive_score']]
    pos_critical = critical_sites[critical_sites['weighted_positive_score'] >= critical_sites['weighted_negative_score']]

    neg_count = len(neg_critical)
    pos_count = len(pos_critical)
    total_alert_count = len(critical_sites)

    col_kpi_total, col_kpi_neg, col_kpi_pos = st.columns(3)

    with col_kpi_total:
        st.markdown(f"<div style='text-align: center; padding: 1.75rem; background: #FFFFFF; border-radius: 8px; border: 2px solid #1E7BC0; box-shadow: 0 2px 8px rgba(30, 123, 192, 0.1);'><p style='font-size: 12px; color: #667A8C; margin: 0 0 0.75rem 0; font-weight: 600; letter-spacing: 0.5px;'>TOTAL ALERT STORES</p><p style='font-size: 36px; font-weight: 700; color: #1E7BC0; margin: 0;'>{total_alert_count}</p><p style='font-size: 11px; color: #8B95A5; margin: 0.75rem 0 0 0;'>Weighted Score ≥ 4.0</p></div>", unsafe_allow_html=True)

    with col_kpi_neg:
        neg_pct = (neg_count / total_alert_count * 100) if total_alert_count > 0 else 0
        st.markdown(f"<div style='text-align: center; padding: 1.75rem; background: #FFFFFF; border-radius: 8px; border: 2px solid #E74C3C; box-shadow: 0 2px 8px rgba(231, 76, 60, 0.1);'><p style='font-size: 12px; color: #667A8C; margin: 0 0 0.75rem 0; font-weight: 600; letter-spacing: 0.5px;'>🔻 UNDERPERFORMING</p><p style='font-size: 36px; font-weight: 700; color: #E74C3C; margin: 0;'>{neg_count}</p><p style='font-size: 11px; color: #8B95A5; margin: 0.75rem 0 0 0;'>{neg_pct:.1f}% of alerts</p></div>", unsafe_allow_html=True)
        if len(neg_critical) > 0:
            st.markdown(f"<p style='text-align: center; font-size: 11px; color: #667A8C; margin-top: 0.5rem;'>Avg Score: <strong>{neg_critical['weighted_negative_score'].mean():.1f}</strong> | Driver: <strong>{neg_critical['primary_driver'].mode().iloc[0] if len(neg_critical) > 0 else 'N/A'}</strong></p>", unsafe_allow_html=True)

    with col_kpi_pos:
        pos_pct = (pos_count / total_alert_count * 100) if total_alert_count > 0 else 0
        st.markdown(f"<div style='text-align: center; padding: 1.75rem; background: #FFFFFF; border-radius: 8px; border: 2px solid #28A745; box-shadow: 0 2px 8px rgba(40, 167, 69, 0.1);'><p style='font-size: 12px; color: #667A8C; margin: 0 0 0.75rem 0; font-weight: 600; letter-spacing: 0.5px;'>🔺 OUTPERFORMING</p><p style='font-size: 36px; font-weight: 700; color: #28A745; margin: 0;'>{pos_count}</p><p style='font-size: 11px; color: #8B95A5; margin: 0.75rem 0 0 0;'>{pos_pct:.1f}% of alerts</p></div>", unsafe_allow_html=True)
        if len(pos_critical) > 0:
            st.markdown(f"<p style='text-align: center; font-size: 11px; color: #667A8C; margin-top: 0.5rem;'>Avg Score: <strong>{pos_critical['weighted_positive_score'].mean():.1f}</strong> | Driver: <strong>{pos_critical['primary_driver'].mode().iloc[0] if len(pos_critical) > 0 else 'N/A'}</strong></p>", unsafe_allow_html=True)

    st.divider()
    
    # Anomaly Detection Methodology - For Management Understanding
    with st.expander("📊 How Are Anomalies Calculated? (Methodology)", expanded=False):
        col_method1, col_method2 = st.columns(2)

        with col_method1:
            st.markdown("""
            **Statistical Detection Method:**

            Each location is evaluated against a baseline using **Z-Score Analysis**:

            1. **Baseline Creation** - 4-week rolling average of each KPI metric (lagged)
            2. **Deviation Calculation** - Measure how far current week deviates from baseline
            3. **Threshold** - Flag triggered when deviation exceeds ±2.0 standard deviations
            4. **Direction-Aware Scoring** - Flags split into negative (underperforming) and positive (outperforming)
            5. **Weighted Anomaly Score** - KPIs weighted by business importance (POS Sales & Utilization = 2x)

            **Alert Tiers (Weighted):**
            - 🔴 **Alert (≥4.0 weighted)** - Multiple KPIs anomalous → Immediate Action
            - 🟡 **Watch (≥2.5 weighted)** - KPIs trending anomalous → Monitor Closely
            - 🟢 **Noise/Clean (<2.5)** - Normal variation → Routine Monitoring

            **Positive vs Negative Classification:**
            - 🔻 **Negative-Performing** - Z-score < -2σ → Store underperforming vs baseline
            - 🔺 **Positive-Performing** - Z-score > +2σ → Store outperforming vs baseline
            """)

        with col_method2:
            st.markdown("""
            **10 KPIs Analyzed (7 Core + 3 Leading Indicators):**

            *Core KPIs:*
            1. **POS Sales** (weight: 2.0) - Total revenue from point-of-sale transactions
            2. **Utilization** (weight: 2.0) - Percentage of available exam chair time used
            3. **ASP** (weight: 1.5) - Average revenue per transaction
            4. **EO %** (weight: 1.5) - Exam-Only percentage
            5. **EPP %** (weight: 1.0) - Exam + Products percentage
            6. **RI %** (weight: 1.0) - Retail Item percentage
            7. **MAS %** (weight: 1.0) - Materials/Services percentage

            *Leading Indicators:*

            8. **Appts Created** (weight: 1.0) - Appointment generation
            9. **Patient Fallout** (weight: 1.5) - Cancellations + no-shows
            10. **Comp Exam %** (weight: 1.0) - Comprehensive exam share

            **Why This Matters:**
            - Direction-aware scoring separates underperformers from outperformers
            - Weighted scoring prioritizes high-impact KPIs
            - Leading indicators provide early warning before core KPIs deteriorate
            """)
    
    st.divider()
    
    # Alert tier distribution and KPI flags
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Alert Tier Distribution")
        tier_counts = filtered_data['alert_tier'].value_counts()

        # Map colors based on alert tier
        color_map = {
            'Alert': '#FF4444',  # Red
            'Watch': '#FFD700',  # Yellow
            'Noise': '#90EE90',  # Green
            'Clean': '#32CD32'  # Green
        }
        colors = [color_map.get(tier, 'gray') for tier in tier_counts.index]

        fig_tier = go.Figure(data=[go.Bar(
            x=tier_counts.index,
            y=tier_counts.values,
            text=tier_counts.values,
            textposition='inside',
            textfont=dict(size=14, color='black', family='Arial Black'),
            marker=dict(color=colors)
        )])
        fig_tier.update_layout(
            title="Sites by Alert Tier",
            xaxis_title="Alert Tier",
            yaxis_title="Count",
            height=400,
            showlegend=False,
            plot_bgcolor='#FAFAFA',
            paper_bgcolor='white',
            xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
            yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0')
        )
        st.plotly_chart(fig_tier, use_container_width=True)

    with col_chart2:
        st.subheader("Top KPI Flags (Anomalies Detected)")
        flagged_kpis = {
            'pos_sales': filtered_data['pos_sales_flag'].sum(),
            'utilization': filtered_data['utilization_flag'].sum(),
            'asp': filtered_data['asp_flag'].sum(),
            'eo_pct': filtered_data['eo_pct_flag'].sum(),
            'epp_pct': filtered_data['epp_pct_flag'].sum(),
            'ri_pct': filtered_data['ri_pct_flag'].sum(),
            'mas_pct': filtered_data['mas_pct_flag'].sum(),
            'appts_created': filtered_data['appts_created_flag'].sum() if 'appts_created_flag' in filtered_data.columns else 0,
            'patient_fallout': filtered_data['patient_fallout_flag'].sum() if 'patient_fallout_flag' in filtered_data.columns else 0,
            'comp_exam_pct': filtered_data['comp_exam_pct_flag'].sum() if 'comp_exam_pct_flag' in filtered_data.columns else 0,
        }
        driver_df = pd.DataFrame(list(flagged_kpis.items()), columns=['KPI', 'Flag Count'])
        driver_df = driver_df.sort_values('Flag Count', ascending=False)

        fig_driver = go.Figure(data=[go.Bar(
            x=driver_df['KPI'],
            y=driver_df['Flag Count'],
            text=driver_df['Flag Count'],
            textposition='inside',
            textfont=dict(size=12, color='black', family='Arial Black'),
            marker=dict(color='#FF6B6B')
        )])
        fig_driver.update_layout(
            title="KPI Flags Across All Sites",
            xaxis_title="KPI",
            yaxis_title="Flag Count",
            height=400,
            showlegend=False,
            plot_bgcolor='#FAFAFA',
            paper_bgcolor='white',
            xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
            yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0')
        )
        st.plotly_chart(fig_driver, use_container_width=True)
    
    st.divider()
    
    # Key insights
    st.subheader("Key Insights")
    col_insight1, col_insight2, col_insight3 = st.columns(3)

    with col_insight1:
        utilization_issues = filtered_data[filtered_data['utilization_flag'] == 1]['utilization'].mean()
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #FFFDE7 0%, #FFF9C4 100%); border-radius: 12px; border: 1px solid #FFE082; border-left: 5px solid #FBC02D; min-height: 120px; display: flex; flex-direction: column; justify-content: center;'><p style='font-size: 11px; color: #827000; margin: 0 0 0.5rem 0; font-weight: bold;'>Avg Utilization (Flagged Sites)</p><p style='font-size: 28px; font-weight: bold; color: #FBC02D; margin: 0;'>{utilization_issues:.1%}</p><p style='font-size: 10px; color: #555; margin: 0.5rem 0 0 0;'>Target: ~80% chair utilization</p></div>", unsafe_allow_html=True)

    with col_insight2:
        asp_flagged_mean = filtered_data[filtered_data['asp_flag'] == 1]['asp'].mean() if len(filtered_data[filtered_data['asp_flag'] == 1]) > 0 else 0
        asp_normal_mean = filtered_data[filtered_data['asp_flag'] == 0]['asp'].mean() if len(filtered_data[filtered_data['asp_flag'] == 0]) > 0 else 0
        asp_drop = (asp_flagged_mean / asp_normal_mean * 100 - 100) if asp_normal_mean > 0 else 0
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%); border-radius: 12px; border: 1px solid #EF9A9A; border-left: 5px solid #E53935; min-height: 120px; display: flex; flex-direction: column; justify-content: center;'><p style='font-size: 11px; color: #B71C1C; margin: 0 0 0.5rem 0; font-weight: bold;'>ASP Gap</p><p style='font-size: 28px; font-weight: bold; color: #E53935; margin: 0;'>{asp_drop:.1f}%</p><p style='font-size: 10px; color: #555; margin: 0.5rem 0 0 0;'>Flagged avg: ${asp_flagged_mean:.0f} vs Normal avg: ${asp_normal_mean:.0f}</p></div>", unsafe_allow_html=True)

    with col_insight3:
        pf_flag_count = int(filtered_data['patient_fallout_flag'].sum()) if 'patient_fallout_flag' in filtered_data.columns else 0
        pf_total = len(filtered_data)
        pf_pct = (pf_flag_count / pf_total * 100) if pf_total > 0 else 0
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%); border-radius: 12px; border: 1px solid #FFCC80; border-left: 5px solid #E65100; min-height: 120px; display: flex; flex-direction: column; justify-content: center;'><p style='font-size: 11px; color: #BF360C; margin: 0 0 0.5rem 0; font-weight: bold;'>Patient Fallout (Flagged Sites)</p><p style='font-size: 28px; font-weight: bold; color: #E65100; margin: 0;'>{pf_flag_count}</p><p style='font-size: 10px; color: #555; margin: 0.5rem 0 0 0;'>{pf_pct:.1f}% of all sites flagged</p></div>", unsafe_allow_html=True)

    st.markdown("""
    <p style='font-size: 12px; color: #667A8C; margin-top: 0.75rem; line-height: 1.5;'>
    <strong>ASP Gap</strong> measures the percentage difference in Average Selling Price between
    flagged sites (Z-score > ±2σ) and non-flagged sites. A negative gap means flagged stores are
    generating less revenue per transaction than their peers — indicating potential pricing, product mix,
    or upsell issues that require attention.
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <strong>Patient Fallout</strong> measures the increase in cancellations + no-shows at flagged sites
    versus non-flagged peers. A positive increase signals scheduling or patient retention issues
    that may be suppressing revenue and utilization.
    </p>
    """, unsafe_allow_html=True)

# ═════════════════════════════════════════════
# TAB 2: CRITICAL ALERTS
# ═════════════════════════════════════════════
with tab2:
    st.header("🚨 Alerts (Immediate Attention Required)")
    
    critical_filtered = filtered_data[filtered_data['alert_tier'] == 'Alert'].sort_values(
        'anomaly_score', ascending=False
    )
    
    # ── Alert Performance Context KPI Boxes ──
    st.subheader("Alert Performance Breakdown")
    st.markdown("""
    Understanding the composition of alert-tier stores:
    - **🔻 Negative-Performing** (Z-score < -2σ) → Stores underperforming vs baseline, need immediate intervention
    - **🔺 Positive-Performing** (Z-score > +2σ) → Stores outperforming vs baseline, best-practice candidates or data anomalies
    """)
    
    # Calculate positive vs negative breakdown
    neg_alerts = critical_filtered[critical_filtered['weighted_negative_score'] > critical_filtered['weighted_positive_score']]
    pos_alerts = critical_filtered[critical_filtered['weighted_positive_score'] >= critical_filtered['weighted_negative_score']]
    
    neg_alert_count = len(neg_alerts)
    pos_alert_count = len(pos_alerts)
    total_alert_count = len(critical_filtered)
    
    col_alert_total, col_alert_neg, col_alert_pos = st.columns(3)
    
    with col_alert_total:
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #E8F0F8 0%, #D6E4F0 100%); border-radius: 12px; border: 1px solid #B0C4DE; border-left: 5px solid #1E7BC0;'><p style='font-size: 14px; color: #666; margin: 0 0 0.5rem 0; font-weight: bold;'>Total Alert Stores</p><p style='font-size: 32px; font-weight: bold; color: #1E7BC0; margin: 0;'>{total_alert_count}</p><p style='font-size: 11px; color: #999; margin: 0.5rem 0 0 0;'>Weighted Score ≥ 4.0</p></div>", unsafe_allow_html=True)
    
    with col_alert_neg:
        neg_pct = (neg_alert_count / total_alert_count * 100) if total_alert_count > 0 else 0
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #FFE8E8 0%, #FFD6D6 100%); border-radius: 12px; border: 1px solid #D4737A; border-left: 5px solid #B71C1C;'><p style='font-size: 14px; color: #666; margin: 0 0 0.5rem 0; font-weight: bold;'>🔻 Negative-Performing</p><p style='font-size: 32px; font-weight: bold; color: #B71C1C; margin: 0;'>{neg_alert_count}</p><p style='font-size: 11px; color: #999; margin: 0.5rem 0 0 0;'>{neg_pct:.1f}% of alerts</p></div>", unsafe_allow_html=True)
        if len(neg_alerts) > 0:
            st.caption(f"Avg Score: **{neg_alerts['weighted_negative_score'].mean():.1f}** | Top Driver: **{neg_alerts['primary_driver'].mode().iloc[0] if len(neg_alerts) > 0 else 'N/A'}**")
    
    with col_alert_pos:
        pos_pct = (pos_alert_count / total_alert_count * 100) if total_alert_count > 0 else 0
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%); border-radius: 12px; border: 1px solid #A5D6A7; border-left: 5px solid #1B5E20;'><p style='font-size: 14px; color: #666; margin: 0 0 0.5rem 0; font-weight: bold;'>🔺 Positive-Performing</p><p style='font-size: 32px; font-weight: bold; color: #1B5E20; margin: 0;'>{pos_alert_count}</p><p style='font-size: 11px; color: #999; margin: 0.5rem 0 0 0;'>{pos_pct:.1f}% of alerts</p></div>", unsafe_allow_html=True)
        if len(pos_alerts) > 0:
            st.caption(f"Avg Score: **{pos_alerts['weighted_positive_score'].mean():.1f}** | Top Driver: **{pos_alerts['primary_driver'].mode().iloc[0] if len(pos_alerts) > 0 else 'N/A'}**")
    
    st.divider()
    
    # Distribution by anomaly type and region (CHARTS FIRST)
    col_type, col_region = st.columns(2)
    
    with col_type:
        st.subheader("Alerts by Type")
        type_dist = critical_filtered['anomaly_type'].value_counts().sort_values(ascending=True)
        fig = go.Figure(data=[go.Bar(y=type_dist.index, x=type_dist.values, orientation='h',
                                     text=type_dist.values,
                                     textposition='inside',
                                     textfont=dict(size=12, color='black', family='Arial Black'),
                                     marker=dict(color='#FF6B6B'))])
        fig.update_layout(title="", xaxis_title="Count", yaxis_title="", height=400, showlegend=False,
                         plot_bgcolor='#FAFAFA', paper_bgcolor='white',
                         xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
                         yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_region:
        st.subheader("Alerts by Region")
        region_dist = critical_filtered['Region'].value_counts().sort_values(ascending=True)
        fig = go.Figure(data=[go.Bar(y=region_dist.index, x=region_dist.values, orientation='h',
                                     text=region_dist.values,
                                     textposition='inside',
                                     textfont=dict(size=12, color='white', family='Arial Black'),
                                     marker=dict(color='#1E7BC0'))])
        fig.update_layout(title="", xaxis_title="Count", yaxis_title="", height=400, showlegend=False,
                         plot_bgcolor='#FAFAFA', paper_bgcolor='white',
                         xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
                         yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'))
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Alert sites - Split into Negative vs Positive performing
    st.subheader("Negative-Performing Alert Sites (Underperformers)")
    st.markdown("<p style='font-size: 13px; color: #DC2626;'><strong>● Red Alert:</strong> Sites underperforming vs baseline - <strong>Require immediate intervention</strong></p>", unsafe_allow_html=True)
    
    display_cols = ['site_id', 'site_name', 'Region', 'Quad', 'anomaly_score',
                   'weighted_negative_score', 'weighted_positive_score',
                   'anomaly_type', 'primary_driver', 'positive_tier', 'pos_sales', 'utilization', 'asp']

    if len(neg_alerts) > 0:
        neg_display_df = neg_alerts[[c for c in display_cols if c in neg_alerts.columns]].copy()
        neg_display_df['utilization'] = neg_display_df['utilization'].apply(lambda x: f"{x:.1%}")
        neg_display_df['asp'] = neg_display_df['asp'].apply(lambda x: f"${x:.0f}")
        rename_map = {
            'site_id': 'Site ID', 'site_name': 'Site Name', 'anomaly_score': 'Score',
            'weighted_negative_score': 'Neg Score', 'weighted_positive_score': 'Pos Score',
            'anomaly_type': 'Type', 'primary_driver': 'Driver', 'positive_tier': 'Outlier',
            'pos_sales': 'POS Sales', 'utilization': 'Util %', 'asp': 'ASP'
        }
        neg_display_df = neg_display_df.rename(columns={k: v for k, v in rename_map.items() if k in neg_display_df.columns})
        st.dataframe(neg_display_df, use_container_width=True, height=400)
    else:
        st.info("No negative-performing alert sites at this time.")
    
    st.divider()
    
    st.subheader("● Positive-Performing Alert Sites (Outperformers)")
    st.markdown("<p style='font-size: 13px; color: #059669;'><strong>● Green Alert:</strong> Sites outperforming vs baseline - <strong>Best-practice candidates or potential data quality issues</strong></p>", unsafe_allow_html=True)
    
    if len(pos_alerts) > 0:
        pos_display_df = pos_alerts[[c for c in display_cols if c in pos_alerts.columns]].copy()
        pos_display_df['utilization'] = pos_display_df['utilization'].apply(lambda x: f"{x:.1%}")
        pos_display_df['asp'] = pos_display_df['asp'].apply(lambda x: f"${x:.0f}")
        rename_map = {
            'site_id': 'Site ID', 'site_name': 'Site Name', 'anomaly_score': 'Score',
            'weighted_negative_score': 'Neg Score', 'weighted_positive_score': 'Pos Score',
            'anomaly_type': 'Type', 'primary_driver': 'Driver', 'positive_tier': 'Outlier',
            'pos_sales': 'POS Sales', 'utilization': 'Util %', 'asp': 'ASP'
        }
        pos_display_df = pos_display_df.rename(columns={k: v for k, v in rename_map.items() if k in pos_display_df.columns})
        st.dataframe(pos_display_df, use_container_width=True, height=400)
    else:
        st.info("No positive-performing alert sites at this time.")
    
    st.divider()
    st.subheader("Alerts: Medicaid vs Non-Medicaid")
    col_med1, col_med2, col_med3 = st.columns(3)
    
    medicaid_critical = len(critical_filtered[critical_filtered['is_medicaid'] == 1.0])
    non_medicaid_critical = len(critical_filtered[critical_filtered['is_medicaid'] == 0.0])
    
    with col_med1:
        st.metric("Medicaid Alert", medicaid_critical)
    with col_med2:
        st.metric("Non-Medicaid Alert", non_medicaid_critical)
    with col_med3:
        pct = medicaid_critical / (medicaid_critical + non_medicaid_critical) * 100 if (medicaid_critical + non_medicaid_critical) > 0 else 0
        st.metric("Medicaid %", f"{pct:.1f}%")

# ═════════════════════════════════════════════
# TAB 3: WATCH LIST
# ═════════════════════════════════════════════
with tab3:
    st.header("⚠️ Watch List (Monitor Trend)")
    
    watch_filtered = filtered_data[filtered_data['alert_tier'] == 'Watch'].sort_values(
        'anomaly_score', ascending=False
    )
    
    st.metric("Number of Watch Sites", len(watch_filtered))
    
    st.divider()
    
    # Charts first
    col_region, col_driver = st.columns(2)
    
    with col_region:
        st.subheader("Watch List by Region")
        region_dist = watch_filtered['Region'].value_counts().sort_values(ascending=True)
        fig = go.Figure(data=[go.Bar(y=region_dist.index, x=region_dist.values, orientation='h',
                                     text=region_dist.values,
                                     textposition='inside',
                                     textfont=dict(size=12, color='black', family='Arial Black'),
                                     marker=dict(color='#FFC107'))])
        fig.update_layout(title="", xaxis_title="Count", yaxis_title="", height=400, showlegend=False,
                         plot_bgcolor='#FAFAFA', paper_bgcolor='white',
                         xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
                         yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_driver:
        st.subheader("Primary Drivers on Watch")
        drivers = watch_filtered['primary_driver'].value_counts().head(8).sort_values(ascending=True)
        fig = go.Figure(data=[go.Bar(y=drivers.index, x=drivers.values, orientation='h',
                                     text=drivers.values,
                                     textposition='inside',
                                     textfont=dict(size=12, color='black', family='Arial Black'),
                                     marker=dict(color='#FFC107'))])
        fig.update_layout(title="", xaxis_title="Count", yaxis_title="", height=400, showlegend=False,
                         plot_bgcolor='#FAFAFA', paper_bgcolor='white',
                         xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
                         yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'))
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Watch list table
    st.subheader("Sites on Watch List")
    
    display_cols = ['site_id', 'site_name', 'Region', 'Quad', 'anomaly_score',
                   'weighted_negative_score', 'weighted_positive_score',
                   'anomaly_type', 'primary_driver', 'pos_sales', 'utilization', 'asp']

    display_df = watch_filtered[[c for c in display_cols if c in watch_filtered.columns]].copy()
    display_df['utilization'] = display_df['utilization'].apply(lambda x: f"{x:.1%}")
    display_df['asp'] = display_df['asp'].apply(lambda x: f"${x:.0f}")
    rename_map = {
        'site_id': 'Site ID', 'site_name': 'Site Name', 'anomaly_score': 'Score',
        'weighted_negative_score': 'Neg Score', 'weighted_positive_score': 'Pos Score',
        'anomaly_type': 'Type', 'primary_driver': 'Driver',
        'pos_sales': 'POS Sales', 'utilization': 'Util %', 'asp': 'ASP'
    }
    display_df = display_df.rename(columns={k: v for k, v in rename_map.items() if k in display_df.columns})

    st.dataframe(display_df, use_container_width=True, height=400)

# ═════════════════════════════════════════════
# TAB 4: REGIONAL ANALYSIS
# ═════════════════════════════════════════════
with tab4:
    st.header("📈 Regional Analysis")
    
    # Regional summary
    regional_summary = filtered_data.groupby('Region').agg({
        'site_id': 'count',
        'anomaly_score': 'mean',
        'pos_sales': 'mean',
        'utilization': 'mean',
        'asp': 'mean'
    }).round(2)
    regional_summary.columns = ['Sites', 'Avg Score', 'Avg POS Sales', 'Avg Utilization', 'Avg ASP']
    
    st.subheader("Regional Performance Summary")
    st.dataframe(regional_summary, use_container_width=True)
    
    st.divider()
    
    # ── Alerts: Negative vs Positive Breakdown by Region ──
    st.subheader("Alerts by Region: Negative vs Positive Performance")
    st.markdown("""
    Alert-tier stores split by performance direction:
    - **🔻 Negative-Performing** (Z-score < -2σ): Underperforming stores requiring immediate intervention
    - **🔺 Positive-Performing** (Z-score > +2σ): Outperforming stores — best-practice candidates
    """)

    critical_sites = filtered_data[filtered_data['alert_tier'] == 'Alert'].copy()

    # Classify: a critical alert is "negative-performing" if its negative score dominates,
    # "positive-performing" if its positive score dominates
    neg_critical = critical_sites[critical_sites['weighted_negative_score'] > critical_sites['weighted_positive_score']]
    pos_critical = critical_sites[critical_sites['weighted_positive_score'] >= critical_sites['weighted_negative_score']]

    neg_count = len(neg_critical)
    pos_count = len(pos_critical)

    col_neg, col_pos = st.columns(2)

    with col_neg:
        st.markdown(f"""<div style='background: linear-gradient(135deg, #FFE8E8 0%, #FFD6D6 100%); border-radius: 12px; padding: 1.5rem; border-left: 5px solid #FF4444; text-align: center;'>
            <div style='font-size: 20px;'>🔻</div>
            <div style='font-weight: bold; font-size: 15px; color: #B71C1C; margin-top: 0.3rem;'>Negative-Performing Alert</div>
            <div style='font-size: 32px; color: #FF4444; font-weight: bold; margin-top: 0.5rem;'>{neg_count}</div>
            <div style='font-size: 12px; color: #666; margin-top: 0.3rem;'>Z-score &lt; -2&sigma; dominant | Needs resource allocation</div>
        </div>""", unsafe_allow_html=True)

        if len(neg_critical) > 0:
            st.markdown(f"<p style='text-align:center; font-size:12px; color:#888; margin-top:0.5rem;'>Avg Weighted Neg Score: <b>{neg_critical['weighted_negative_score'].mean():.1f}</b> | Top Driver: <b>{neg_critical['primary_driver'].mode().iloc[0] if len(neg_critical) > 0 else 'N/A'}</b></p>", unsafe_allow_html=True)

    with col_pos:
        st.markdown(f"""<div style='background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%); border-radius: 12px; padding: 1.5rem; border-left: 5px solid #4CAF50; text-align: center;'>
            <div style='font-size: 20px;'>🔺</div>
            <div style='font-weight: bold; font-size: 15px; color: #1B5E20; margin-top: 0.3rem;'>Positive-Performing Alert</div>
            <div style='font-size: 32px; color: #4CAF50; font-weight: bold; margin-top: 0.5rem;'>{pos_count}</div>
            <div style='font-size: 12px; color: #666; margin-top: 0.3rem;'>Z-score &gt; +2&sigma; dominant | Best-practice candidates</div>
        </div>""", unsafe_allow_html=True)

        if len(pos_critical) > 0:
            st.markdown(f"<p style='text-align:center; font-size:12px; color:#888; margin-top:0.5rem;'>Avg Weighted Pos Score: <b>{pos_critical['weighted_positive_score'].mean():.1f}</b> | Top Driver: <b>{pos_critical['primary_driver'].mode().iloc[0] if len(pos_critical) > 0 else 'N/A'}</b></p>", unsafe_allow_html=True)

    st.divider()
    
    # ── Two-Column Layout: Alert Tier by Region | Alerts by Region: Negative vs Positive ──
    col_tier, col_perf = st.columns(2)
    
    with col_tier:
        st.subheader("Alert Tier by Region")
        region_tier = pd.crosstab(filtered_data['Region'], filtered_data['alert_tier'])
        fig_tier = go.Figure(data=[
            go.Bar(name='Alert', x=region_tier.index, y=region_tier.get('Alert', 0), 
                   text=region_tier.get('Alert', 0),
                   textposition='inside',
                   textfont=dict(size=10, color='black', family='Arial Black'),
                   marker=dict(color='#FF6B6B')),
            go.Bar(name='Watch', x=region_tier.index, y=region_tier.get('Watch', 0), 
                   text=region_tier.get('Watch', 0),
                   textposition='inside',
                   textfont=dict(size=10, color='black', family='Arial Black'),
                   marker=dict(color='#FFC107')),
        ])
        fig_tier.update_layout(
            barmode='stack', 
            height=450, 
            xaxis_title="Region", 
            yaxis_title="Count",
            plot_bgcolor='#FAFAFA', 
            paper_bgcolor='white',
            showlegend=True,
            legend=dict(orientation='v', yanchor='top', y=1, xanchor='left', x=1.02),
            xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
            yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
            margin=dict(r=100)
        )
        st.plotly_chart(fig_tier, use_container_width=True)
    
    with col_perf:
        st.subheader("Negative vs Positive by Region")
        if len(critical_sites) > 0:
            neg_by_region = neg_critical.groupby('Region').size().reindex(critical_sites['Region'].unique(), fill_value=0)
            pos_by_region = pos_critical.groupby('Region').size().reindex(critical_sites['Region'].unique(), fill_value=0)

            fig_perf = go.Figure(data=[
                go.Bar(name='Negative-Performing', x=neg_by_region.index, y=neg_by_region.values,
                       marker=dict(color='#FF4444'),
                       text=neg_by_region.values, textposition='inside',
                       textfont=dict(size=10, color='white', family='Arial Black')),
                go.Bar(name='Positive-Performing', x=pos_by_region.index, y=pos_by_region.values,
                       marker=dict(color='#4CAF50'),
                       text=pos_by_region.values, textposition='inside',
                       textfont=dict(size=10, color='white', family='Arial Black'))
            ])
            fig_perf.update_layout(
                barmode='group', 
                height=450,
                xaxis_title="Region", 
                yaxis_title="Count",
                plot_bgcolor='#FAFAFA', 
                paper_bgcolor='white',
                showlegend=True,
                legend=dict(orientation='v', yanchor='top', y=1, xanchor='left', x=1.02),
                xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
                yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
                margin=dict(r=100)
            )
            st.plotly_chart(fig_perf, use_container_width=True)
        else:
            st.info("No alert sites to display")
    
    st.divider()
    
    # Quad analysis
    st.subheader("Supply/Demand Quad Analysis")
    quad_summary = filtered_data.groupby('Quad').agg({
        'site_id': 'count',
        'anomaly_score': 'mean',
        'utilization': 'mean',
        'asp': 'mean',
        'pos_sales': 'mean'
    }).round(2)
    quad_summary.columns = ['Sites', 'Avg Score', 'Avg Util', 'Avg ASP', 'Avg POS Sales']
    
    st.dataframe(quad_summary, use_container_width=True)
    
    fig_quad = px.scatter(filtered_data, x='utilization', y='asp', color='Quad',
                         size='pos_sales', hover_name='site_name',
                         title="Utilization vs ASP by Quad (bubble size = POS Sales)")
    fig_quad.update_layout(height=500)
    st.plotly_chart(fig_quad, use_container_width=True)

# ═════════════════════════════════════════════
# TAB 5: SITE EXPLORER
# ═════════════════════════════════════════════
with tab5:
    st.header("🔍 Site Explorer")
    
    # Site selector
    site_options = sorted(filtered_data['site_id'].unique())
    selected_site = st.selectbox("Select a Site", site_options)
    
    site_data = filtered_data[filtered_data['site_id'] == selected_site].iloc[0]
    
    st.divider()
    
    # Site info
    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    
    with col_info1:
        st.write(f"**Site Name:** {site_data['site_name']}")
    with col_info2:
        st.write(f"**Region:** {site_data['Region']}")
    with col_info3:
        st.write(f"**Quad:** {site_data['Quad']}")
    with col_info4:
        alert_color = "🔴" if site_data['alert_tier'] == 'Alert' else "🟡" if site_data['alert_tier'] == 'Watch' else "🟢"
        st.write(f"**Alert Status:** {alert_color} {site_data['alert_tier']}")
    
    st.divider()
    
    # Anomaly details
    col_anomaly1, col_anomaly2, col_anomaly3 = st.columns(3)
    
    with col_anomaly1:
        st.markdown(f"<div style='text-align: center;'><p style='font-size: 12px; color: #888; margin: 0;'>Anomaly Score</p><p style='font-size: 20px; font-weight: bold; color: #1E7BC0; margin: 0.25rem 0;'>{site_data['anomaly_score']:.1f}/10</p></div>", unsafe_allow_html=True)
    with col_anomaly2:
        st.markdown(f"<div style='text-align: center;'><p style='font-size: 12px; color: #888; margin: 0;'>Anomaly Type</p><p style='font-size: 20px; font-weight: bold; color: #1E7BC0; margin: 0.25rem 0;'>{site_data['anomaly_type']}</p></div>", unsafe_allow_html=True)
    with col_anomaly3:
        st.markdown(f"<div style='text-align: center;'><p style='font-size: 12px; color: #888; margin: 0;'>Primary Driver</p><p style='font-size: 20px; font-weight: bold; color: #1E7BC0; margin: 0.25rem 0;'>{site_data['primary_driver']}</p></div>", unsafe_allow_html=True)
    
    st.divider()
    
    # KPI details
    st.subheader("KPI Performance & Flags")
    
    kpi_names = ['POS Sales', 'Utilization', 'ASP', 'EO %', 'EPP %', 'RI %', 'MAS %',
                  'Appts Created', 'Patient Fallout', 'Comp Exam %']
    kpi_keys = ['pos_sales', 'utilization', 'asp', 'eo_pct', 'epp_pct', 'ri_pct', 'mas_pct',
                'appts_created', 'patient_fallout', 'comp_exam_pct']
    kpi_fmt = [
        lambda v: f"${v:.0f}", lambda v: f"{v:.1%}", lambda v: f"${v:.0f}",
        lambda v: f"{v:.1%}", lambda v: f"{v:.1%}", lambda v: f"{v:.1%}", lambda v: f"{v:.1%}",
        lambda v: f"{v:.0f}", lambda v: f"{v:.0f}", lambda v: f"{v:.1%}",
    ]

    kpi_values, kpi_zscores, kpi_flags, kpi_directions = [], [], [], []
    valid_kpi_names = []
    for i, key in enumerate(kpi_keys):
        if key in site_data.index and pd.notna(site_data.get(f'{key}_zscore', np.nan)):
            valid_kpi_names.append(kpi_names[i])
            kpi_values.append(kpi_fmt[i](site_data[key]))
            kpi_zscores.append(f"{site_data[f'{key}_zscore']:.2f}")
            flag_val = site_data.get(f'{key}_flag', 0)
            direction = site_data.get(f'{key}_direction', 'normal')
            if flag_val == 1:
                kpi_flags.append("🔻 Below" if direction == 'below_normal' else "🔺 Above" if direction == 'above_normal' else "🚩")
            else:
                kpi_flags.append("✓")
            kpi_directions.append(str(direction).replace('_', ' ').title())

    kpi_data = {
        'KPI': valid_kpi_names,
        'Value': kpi_values,
        'Z-Score': kpi_zscores,
        'Flagged': kpi_flags,
        'Direction': kpi_directions,
    }
    
    kpi_df = pd.DataFrame(kpi_data)
    st.dataframe(kpi_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Trend indicators
    st.subheader("Week-over-Week Trends")
    
    col_trend1, col_trend2, col_trend3 = st.columns(3)
    
    with col_trend1:
        st.metric("POS Sales WoW Change", f"{site_data['pos_sales_wow_pct_chg']:.1%}",
                 delta="Primary Driver" if site_data['primary_driver'] == 'pos_sales' else "")
    
    with col_trend2:
        st.metric("Utilization WoW Change", f"{site_data['utilization_wow_pct_chg']:.1%}",
                 delta="Primary Driver" if site_data['primary_driver'] == 'utilization' else "")
    
    with col_trend3:
        st.metric("ASP WoW Change", f"{site_data['asp_wow_pct_chg']:.1%}",
                 delta="Primary Driver" if site_data['primary_driver'] == 'asp' else "")
    
    st.divider()
    
    # Site attributes
    st.subheader("Site Attributes")
    
    attr_col1, attr_col2, attr_col3 = st.columns(3)
    
    with attr_col1:
        st.write(f"**City:** {site_data['City']}")
        st.write(f"**Opening Date:** {site_data['opening_date']}")
        st.write(f"**Office Age:** {site_data['office_age_yrs']:.1f} years")
    
    with attr_col2:
        st.write(f"**Medicaid:** {'Yes' if site_data['is_medicaid'] == 1.0 else 'No'}")
        st.write(f"**Tele-Opt:** {'Yes' if site_data['is_tele_opt'] == 1.0 else 'No'}")
        st.write(f"**Acuity:** {'Yes' if site_data['is_acuity'] == 1.0 else 'No'}")
    
    with attr_col3:
        st.write(f"**Property Type:** {site_data['property_type']}")
        st.write(f"**Sq Footage:** {site_data['sq_footage']:.0f}" if pd.notna(site_data['sq_footage']) else "")
        st.write(f"**Exam Lanes:** {site_data['exam_lanes']:.0f}" if pd.notna(site_data['exam_lanes']) else "")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.markdown(
    """
    ---
    **Northstar Analytics — MyEyeDr Anomaly Detection Dashboard**
    
    Data as of: """ + latest_date.strftime("%B %d, %Y") + """
    
    Z-Score Threshold: 2.0σ | Anomaly Score: 0-10 scale (weighted) | Direction-aware scoring separates negative & positive performers
    """
)
