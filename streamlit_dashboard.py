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
    /* Hide Streamlit default elements */
    #MainMenu {display: none;}
    footer {display: none;}
    header {display: none;}
    
    /* Main content padding to avoid overlap with fixed header */
    .main {
        padding-top: 80px;
    }
    
    /* Fixed branded header bar */
    .header-container {
        position: fixed;
        top: 0;
        left: 336px;
        right: 0;
        background-color: #0B1F3F;
        padding: 1.2rem 2rem;
        border-bottom: 3px solid #1E90FF;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 999;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Left side branding */
    .header-left {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    
    .header-title {
        color: white;
        font-weight: 700;
        font-size: 26px;
        letter-spacing: 3px;
        margin: 0;
        text-transform: uppercase;
    }
    
    .header-subtitle {
        color: #8CABD9;
        font-size: 14px;
        margin: 0;
        font-weight: 500;
    }
    
    /* Right side metadata */
    .header-right {
        color: #A0AEC0;
        font-size: 13px;
        text-align: right;
        font-weight: 500;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0F2847;
    }
    
    [data-testid="stSidebar"] > div > div:first-child {
        background-color: #0F2847;
    }
    
    /* Sidebar text color */
    [data-testid="stSidebar"] .css-1d391kg,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: white !important;
    }
    
    /* Metric container styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #F8FAFC 0%, #E8F0F8 100%);
        border-left: 4px solid #1E90FF;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(30, 144, 255, 0.15);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: 0 6px 16px rgba(30, 144, 255, 0.25);
        transform: translateY(-2px);
    }
    
    /* Custom metric card styling */
    .metric-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F0F4F8 100%);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        border: 1px solid #E0E7FF;
        transition: all 0.3s ease;
        text-align: center;
    }
    
    .metric-card:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        transform: translateY(-4px);
    }
    
    .metric-card-critical {
        background: linear-gradient(135deg, #FFE8E8 0%, #FFD6D6 100%);
        border-left: 5px solid #FF4444;
    }
    
    .metric-card-watch {
        background: linear-gradient(135deg, #FFF8E8 0%, #FFF0D6 100%);
        border-left: 5px solid #FFD700;
    }
    
    .metric-card-clean {
        background: linear-gradient(135deg, #E8FFE8 0%, #D6FFD6 100%);
        border-left: 5px solid #32CD32;
    }
    
    /* Tab styling */
    [data-testid="stTabs"] {
        background-color: transparent !important;
    }
    
    [data-testid="stTabs"] > div {
        background-color: transparent !important;
    }
    
    [data-testid="stTabs"] button {
        color: #0B1F3F;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        background-color: transparent !important;
    }
    
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #1E90FF;
        border-bottom: 2px solid #1E90FF;
        font-size: 16px !important;
        font-weight: 600 !important;
    }
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    }
    
</style>

<div class="header-container">
    <div class="header-left">
        <div class="header-title">NORTHSTAR ANALYTICS</div>
        <div class="header-subtitle">MyEyeDr. Performance & Anomaly Detection Dashboard</div>
    </div>
    <div class="header-right">
        SMU MSBA Capstone | Spring 2026
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    anomaly = pd.read_csv('med_anomaly_scores.csv')
    critical = pd.read_csv('med_critical_alerts.csv')
    watch = pd.read_csv('med_watch_list.csv')
    profiling = pd.read_csv('med_profiling.csv')
    
    # Convert date column
    anomaly['date'] = pd.to_datetime(anomaly['date'])
    critical['date'] = pd.to_datetime(critical['date'])
    watch['date'] = pd.to_datetime(watch['date'])
    
    return anomaly, critical, watch, profiling

anomaly, critical, watch, profiling = load_data()

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
st.sidebar.title("🎛️ Filters")

# Filter by region
regions = sorted(anomaly['Region'].dropna().unique())
region_options = ["All"] + list(regions)
selected_region = st.sidebar.selectbox("Region", region_options, index=0)

# Filter by Quad
quads = sorted(anomaly['Quad'].dropna().unique())
quad_options = ["All"] + list(quads)
selected_quad = st.sidebar.selectbox("Supply/Demand Quad", quad_options, index=0)

# Filter by alert tier
alert_tier_options = ["All", "Critical Alert", "Watch", "Noise", "Clean"]
selected_alert_tier = st.sidebar.selectbox("Alert Tier", alert_tier_options, index=0)

# Filter by Medicaid status
medicaid_options = st.sidebar.checkbox("Medicaid Locations Only", value=False)
tele_opt = st.sidebar.checkbox("Tele-Opt Locations Only", value=False)

# Apply filters
if selected_region == "All":
    region_filter = anomaly['Region'].isin(regions)
else:
    region_filter = anomaly['Region'] == selected_region

if selected_quad == "All":
    quad_filter = anomaly['Quad'].isin(quads)
else:
    quad_filter = anomaly['Quad'] == selected_quad

if selected_alert_tier == "All":
    alert_filter = anomaly['alert_tier'].isin(["Critical Alert", "Watch", "Noise", "Clean"])
else:
    alert_filter = anomaly['alert_tier'] == selected_alert_tier

filtered_data = anomaly[region_filter & quad_filter & alert_filter]

if medicaid_options:
    filtered_data = filtered_data[filtered_data['is_medicaid'] == 1.0]

if tele_opt:
    filtered_data = filtered_data[filtered_data['is_tele_opt'] == 1.0]

# ─────────────────────────────────────────────
# NAVIGATION TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Executive Summary",
    "🚨 Critical Alerts",
    "⚠️ Watch List",
    "📈 Regional Analysis",
    "🔍 Site Explorer",
    "📋 Cohort Baselines"
])

# ═════════════════════════════════════════════
# TAB 1: EXECUTIVE SUMMARY
# ═════════════════════════════════════════════
with tab1:
    # Team name display
    st.markdown("<h1 style='text-align: center; color: #1E90FF; font-weight: bold; margin-top: 0; margin-bottom: 10px;'>🎯 NORTHSTAR ANALYTICS</h1>", unsafe_allow_html=True)
    
    st.header("📊 Executive Summary")
    
    # Date info
    latest_date = anomaly['date'].max()
    st.markdown(f"**Report Period:** Week of {latest_date.strftime('%B %d, %Y')}")
    
    # Key metrics - Single row with Total Sites + Alert boxes (consistent sizing)
    col1, col2, col3, col4 = st.columns(4)
    
    total_sites = len(filtered_data)
    critical_count = len(filtered_data[filtered_data['alert_tier'] == 'Critical Alert'])
    watch_count = len(filtered_data[filtered_data['alert_tier'] == 'Watch'])
    noise_clean = len(filtered_data[filtered_data['alert_tier'].isin(['Noise', 'Clean'])])
    
    with col1:
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #E8F0F8 0%, #F0F4F8 100%); border-radius: 12px; border: 1px solid #D0E0F0; border-left: 5px solid #1E90FF;'><p style='font-size: 14px; color: #666; margin: 0 0 0.5rem 0;'>Total Sites Scored</p><p style='font-size: 26px; font-weight: bold; color: #1E90FF; margin: 0;'>{total_sites}</p></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold; margin: 0.8rem 0 0 0; color: #0B1F3F;'>All Locations<br><span style='font-size: 12px; font-weight: normal;'>Regular monitoring</span></p>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"<div style='background: linear-gradient(135deg, #FFE8E8 0%, #FFD6D6 100%); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(255, 68, 68, 0.2); border-left: 5px solid #FF4444; text-align: center;'><div style='font-size: 24px; font-weight: bold;'>🔴</div><div style='font-weight: bold; font-size: 13px; color: #0B1F3F; margin-top: 0.3rem;'>Critical Alert</div><div style='font-size: 26px; color: #FF4444; font-weight: bold; margin-top: 0.5rem;'>{critical_count}</div><div style='font-size: 11px; color: #666; margin-top: 0.2rem;'>{critical_count/total_sites*100:.1f}% of total</div></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold; margin: 0.8rem 0 0 0; color: #0B1F3F;'>Score ≥ 3<br><span style='font-size: 12px; font-weight: normal;'>Immediate action required</span></p>", unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"<div style='background: linear-gradient(135deg, #FFF8E8 0%, #FFF0D6 100%); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2); border-left: 5px solid #FFD700; text-align: center;'><div style='font-size: 24px; font-weight: bold;'>🟡</div><div style='font-weight: bold; font-size: 13px; color: #0B1F3F; margin-top: 0.3rem;'>Watch</div><div style='font-size: 26px; color: #FFD700; font-weight: bold; margin-top: 0.5rem;'>{watch_count}</div><div style='font-size: 11px; color: #666; margin-top: 0.2rem;'>{watch_count/total_sites*100:.1f}% of total</div></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold; margin: 0.8rem 0 0 0; color: #0B1F3F;'>Score = 2<br><span style='font-size: 12px; font-weight: normal;'>Active monitoring</span></p>", unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"<div style='background: linear-gradient(135deg, #E8FFE8 0%, #D6FFD6 100%); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(50, 205, 50, 0.2); border-left: 5px solid #32CD32; text-align: center;'><div style='font-size: 24px; font-weight: bold;'>🟢</div><div style='font-weight: bold; font-size: 13px; color: #0B1F3F; margin-top: 0.3rem;'>Clean/Noise</div><div style='font-size: 26px; color: #32CD32; font-weight: bold; margin-top: 0.5rem;'>{noise_clean}</div><div style='font-size: 11px; color: #666; margin-top: 0.2rem;'>{noise_clean/total_sites*100:.1f}% of total</div></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold; margin: 0.8rem 0 0 0; color: #0B1F3F;'>Score 0-1<br><span style='font-size: 12px; font-weight: normal;'>Normal variation</span></p>", unsafe_allow_html=True)
    
    st.divider()
    
    # Anomaly Detection Methodology - For Management Understanding
    with st.expander("📊 How Are Anomalies Calculated? (Methodology)", expanded=False):
        col_method1, col_method2 = st.columns(2)
        
        with col_method1:
            st.markdown("""
            **Statistical Detection Method:**
            
            Each location is evaluated against a baseline using **Z-Score Analysis**:
            
            1. **Baseline Creation** - 13-week rolling average of each KPI metric
            2. **Deviation Calculation** - Measure how far current week deviates from baseline
            3. **Threshold** - Flag triggered when deviation exceeds ±2.0 standard deviations
            4. **Anomaly Score** - Sum of flagged KPIs (0-7 scale)
            
            **Alert Tiers:**
            - 🔴 **Critical Alert (≥3)** - Multiple KPIs anomalous → Immediate Action
            - 🟡 **Watch (=2)** - Two KPIs anomalous → Monitor Closely  
            - 🟢 **Noise/Clean (≤1)** - Normal variation → Routine Monitoring
            """)
        
        with col_method2:
            st.markdown("""
            **7 KPIs Analyzed:**
            
            1. **POS Sales** - Total revenue from point-of-sale transactions
            2. **Utilization** - Percentage of available exam chair time used
            3. **ASP (Avg Service Price)** - Average revenue per transaction
            4. **EO %** - Exam-Only percentage of revenue
            5. **EPP %** - Exam + Products percentage of revenue
            6. **RI %** - Retail Item percentage of revenue
            7. **MAS %** - Materials/Services percentage of revenue
            
            **Why This Matters:**
            - Detects performance shifts early
            - Distinguishes true issues from random variation
            - Enables targeted corrective action
            - Accounts for seasonal patterns & location differences
            """)
    
    st.divider()
    
    # Alert tier distribution
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Alert Tier Distribution")
        tier_counts = filtered_data['alert_tier'].value_counts()
        
        # Map colors based on alert tier
        color_map = {
            'Critical Alert': '#FF4444',  # Red
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
        st.subheader("Anomaly Type Distribution")
        type_counts = filtered_data['anomaly_type'].value_counts().head(10).sort_values(ascending=True)
        fig_type = go.Figure(data=[go.Bar(
            y=type_counts.index,
            x=type_counts.values,
            orientation='h',
            text=type_counts.values,
            textposition='inside',
            textfont=dict(size=12, color='black', family='Arial Black'),
            marker=dict(color='steelblue')
        )])
        fig_type.update_layout(
            title="Top 10 Anomaly Types",
            xaxis_title="Count",
            yaxis_title="Anomaly Type",
            height=400,
            showlegend=False,
            plot_bgcolor='#FAFAFA',
            paper_bgcolor='white',
            xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
            yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0')
        )
        st.plotly_chart(fig_type, use_container_width=True)
    
    st.divider()
    
    # Primary drivers
    col_driver1, col_driver2 = st.columns(2)
    
    with col_driver1:
        st.subheader("Top Primary Drivers (KPI Flags)")
        flagged_kpis = {
            'pos_sales': filtered_data['pos_sales_flag'].sum(),
            'utilization': filtered_data['utilization_flag'].sum(),
            'asp': filtered_data['asp_flag'].sum(),
            'eo_pct': filtered_data['eo_pct_flag'].sum(),
            'epp_pct': filtered_data['epp_pct_flag'].sum(),
            'ri_pct': filtered_data['ri_pct_flag'].sum(),
            'mas_pct': filtered_data['mas_pct_flag'].sum(),
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
            title="KPI Flags (Anomalies Detected)",
            xaxis_title="KPI",
            yaxis_title="Count",
            height=350,
            showlegend=False,
            plot_bgcolor='#FAFAFA',
            paper_bgcolor='white',
            xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
            yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0')
        )
        st.plotly_chart(fig_driver, use_container_width=True)
    
    with col_driver2:
        st.subheader("Anomaly Direction Summary")
        below_normal = len(filtered_data[filtered_data['primary_driver'].notna() & 
                                        (filtered_data['pos_sales_direction'] == 'below_normal')])
        above_normal = len(filtered_data[filtered_data['primary_driver'].notna() & 
                                        (filtered_data['pos_sales_direction'] == 'above_normal')])
        
        fig_direction = go.Figure(data=[go.Pie(
            labels=['Below Normal', 'Above Normal'],
            values=[below_normal, above_normal],
            marker=dict(colors=['#FF6B6B', '#4ECDC4']),
            hole=0.4
        )])
        fig_direction.update_layout(
            title="Direction of Primary Driver",
            height=350
        )
        st.plotly_chart(fig_direction, use_container_width=True)
    
    st.divider()
    
    # Key insights - All boxes with consistent sizing
    st.subheader("🔑 Key Insights")
    col_insight1, col_insight2, col_insight3, col_insight4 = st.columns(4)
    
    with col_insight1:
        avg_score = filtered_data['anomaly_score'].mean()
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #E8F0F8 0%, #F0F4F8 100%); border-radius: 12px; border: 1px solid #D0E0F0; border-left: 5px solid #1E90FF; min-height: 120px; display: flex; flex-direction: column; justify-content: center;'><p style='font-size: 11px; color: #666; margin: 0 0 0.5rem 0;'>Avg Anomaly Score</p><p style='font-size: 28px; font-weight: bold; color: #1E90FF; margin: 0;'>{avg_score:.2f}</p><p style='font-size: 10px; color: #999; margin: 0.5rem 0 0 0;'>(0-7 scale)</p></div>", unsafe_allow_html=True)
    
    with col_insight2:
        medicaid_critical = len(filtered_data[(filtered_data['alert_tier'] == 'Critical Alert') & 
                                             (filtered_data['is_medicaid'] == 1.0)])
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); border-radius: 12px; border: 1px solid #64B5F6; border-left: 5px solid #1976D2; min-height: 120px; display: flex; flex-direction: column; justify-content: center;'><p style='font-size: 11px; color: #0D47A1; margin: 0 0 0.5rem 0; font-weight: bold;'>Medicaid Critical</p><p style='font-size: 22px; font-weight: bold; color: #1976D2; margin: 0;'>{medicaid_critical}</p><p style='font-size: 10px; color: #555; margin: 0.5rem 0 0 0;'>flagged locations</p></div>", unsafe_allow_html=True)
    
    with col_insight3:
        utilization_issues = filtered_data[filtered_data['utilization_flag'] == 1]['utilization'].mean()
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #FFFDE7 0%, #FFF9C4 100%); border-radius: 12px; border: 1px solid #FFE082; border-left: 5px solid #FBC02D; min-height: 120px; display: flex; flex-direction: column; justify-content: center;'><p style='font-size: 11px; color: #827000; margin: 0 0 0.5rem 0; font-weight: bold;'>Avg Utilization</p><p style='font-size: 22px; font-weight: bold; color: #FBC02D; margin: 0;'>{utilization_issues:.1%}</p><p style='font-size: 10px; color: #555; margin: 0.5rem 0 0 0;'>vs ~80% target</p></div>", unsafe_allow_html=True)
    
    with col_insight4:
        asp_drop = (filtered_data[filtered_data['asp_flag'] == 1]['asp'].mean() / 
                   filtered_data[filtered_data['asp_flag'] == 0]['asp'].mean() * 100 - 100) if len(filtered_data[filtered_data['asp_flag'] == 0]) > 0 else 0
        st.markdown(f"<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%); border-radius: 12px; border: 1px solid #EF9A9A; border-left: 5px solid #E53935; min-height: 120px; display: flex; flex-direction: column; justify-content: center;'><p style='font-size: 11px; color: #B71C1C; margin: 0 0 0.5rem 0; font-weight: bold;'>ASP Gap</p><p style='font-size: 22px; font-weight: bold; color: #E53935; margin: 0;'>{asp_drop:.1f}%</p><p style='font-size: 10px; color: #555; margin: 0.5rem 0 0 0;'>below average</p></div>", unsafe_allow_html=True)

# ═════════════════════════════════════════════
# TAB 2: CRITICAL ALERTS
# ═════════════════════════════════════════════
with tab2:
    st.header("🚨 Critical Alerts (Immediate Attention Required)")
    
    critical_filtered = filtered_data[filtered_data['alert_tier'] == 'Critical Alert'].sort_values(
        'anomaly_score', ascending=False
    )
    
    st.metric("Number of Critical Sites", len(critical_filtered))
    
    st.divider()
    
    # Distribution by anomaly type and region (CHARTS FIRST)
    col_type, col_region = st.columns(2)
    
    with col_type:
        st.subheader("Critical Alerts by Type")
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
        st.subheader("Critical Alerts by Region")
        region_dist = critical_filtered['Region'].value_counts().sort_values(ascending=True)
        fig = go.Figure(data=[go.Bar(y=region_dist.index, x=region_dist.values, orientation='h',
                                     text=region_dist.values,
                                     textposition='inside',
                                     textfont=dict(size=12, color='black', family='Arial Black'),
                                     marker=dict(color='#FF6B6B'))])
        fig.update_layout(title="", xaxis_title="Count", yaxis_title="", height=400, showlegend=False,
                         plot_bgcolor='#FAFAFA', paper_bgcolor='white',
                         xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
                         yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'))
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Critical sites table
    st.subheader("Critical Alert Sites")
    
    display_cols = ['site_id', 'site_name', 'Region', 'Quad', 'anomaly_score', 
                   'anomaly_type', 'primary_driver', 'pos_sales', 'utilization', 'asp']
    
    display_df = critical_filtered[display_cols].copy()
    display_df['utilization'] = display_df['utilization'].apply(lambda x: f"{x:.1%}")
    display_df['asp'] = display_df['asp'].apply(lambda x: f"${x:.0f}")
    display_df = display_df.rename(columns={
        'site_id': 'Site ID',
        'site_name': 'Site Name',
        'anomaly_score': 'Score',
        'anomaly_type': 'Type',
        'primary_driver': 'Driver',
        'pos_sales': 'POS Sales',
        'utilization': 'Util %',
        'asp': 'ASP'
    })
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # Medicaid vs Non-Medicaid breakdown
    st.subheader("Critical Alerts: Medicaid vs Non-Medicaid")
    col_med1, col_med2, col_med3 = st.columns(3)
    
    medicaid_critical = len(critical_filtered[critical_filtered['is_medicaid'] == 1.0])
    non_medicaid_critical = len(critical_filtered[critical_filtered['is_medicaid'] == 0.0])
    
    with col_med1:
        st.metric("Medicaid Critical", medicaid_critical)
    with col_med2:
        st.metric("Non-Medicaid Critical", non_medicaid_critical)
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
                   'anomaly_type', 'primary_driver', 'pos_sales', 'utilization', 'asp']
    
    display_df = watch_filtered[display_cols].copy()
    display_df['utilization'] = display_df['utilization'].apply(lambda x: f"{x:.1%}")
    display_df['asp'] = display_df['asp'].apply(lambda x: f"${x:.0f}")
    display_df = display_df.rename(columns={
        'site_id': 'Site ID',
        'site_name': 'Site Name',
        'anomaly_score': 'Score',
        'anomaly_type': 'Type',
        'primary_driver': 'Driver',
        'pos_sales': 'POS Sales',
        'utilization': 'Util %',
        'asp': 'ASP'
    })
    
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
    
    # Regional anomaly distribution
    col_regional1, col_regional2 = st.columns(2)
    
    with col_regional1:
        st.subheader("Anomaly Score by Region")
        fig = px.box(filtered_data, x='Region', y='anomaly_score',
                    color='alert_tier',
                    color_discrete_map={'Critical Alert': '#FF6B6B', 'Watch': '#FFC107', 
                                       'Noise': '#FFD700', 'Clean': '#90EE90'})
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_regional2:
        st.subheader("Alert Tier by Region")
        region_tier = pd.crosstab(filtered_data['Region'], filtered_data['alert_tier'])
        fig = go.Figure(data=[
            go.Bar(name='Critical Alert', x=region_tier.index, y=region_tier.get('Critical Alert', 0), 
                   text=region_tier.get('Critical Alert', 0),
                   textposition='inside',
                   textfont=dict(size=10, color='black', family='Arial Black'),
                   marker=dict(color='#FF6B6B')),
            go.Bar(name='Watch', x=region_tier.index, y=region_tier.get('Watch', 0), 
                   text=region_tier.get('Watch', 0),
                   textposition='inside',
                   textfont=dict(size=10, color='black', family='Arial Black'),
                   marker=dict(color='#FFC107')),
        ])
        fig.update_layout(barmode='stack', height=400, xaxis_title="Region", yaxis_title="Count",
                         plot_bgcolor='#FAFAFA', paper_bgcolor='white',
                         xaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'),
                         yaxis=dict(showline=True, linewidth=1, linecolor='#D0D0D0'))
        st.plotly_chart(fig, use_container_width=True)
    
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
        alert_color = "🔴" if site_data['alert_tier'] == 'Critical Alert' else "🟡" if site_data['alert_tier'] == 'Watch' else "🟢"
        st.write(f"**Alert Status:** {alert_color} {site_data['alert_tier']}")
    
    st.divider()
    
    # Anomaly details
    col_anomaly1, col_anomaly2, col_anomaly3 = st.columns(3)
    
    with col_anomaly1:
        st.metric("Anomaly Score", f"{site_data['anomaly_score']:.1f}/7")
    with col_anomaly2:
        st.metric("Anomaly Type", site_data['anomaly_type'])
    with col_anomaly3:
        st.metric("Primary Driver", site_data['primary_driver'])
    
    st.divider()
    
    # KPI details
    st.subheader("KPI Performance & Flags")
    
    kpi_data = {
        'KPI': ['POS Sales', 'Utilization', 'ASP', 'EO %', 'EPP %', 'RI %', 'MAS %'],
        'Value': [
            f"${site_data['pos_sales']:.0f}",
            f"{site_data['utilization']:.1%}",
            f"${site_data['asp']:.0f}",
            f"{site_data['eo_pct']:.1%}",
            f"{site_data['epp_pct']:.1%}",
            f"{site_data['ri_pct']:.1%}",
            f"{site_data['mas_pct']:.1%}",
        ],
        'Z-Score': [
            f"{site_data['pos_sales_zscore']:.2f}",
            f"{site_data['utilization_zscore']:.2f}",
            f"{site_data['asp_zscore']:.2f}",
            f"{site_data['eo_pct_zscore']:.2f}",
            f"{site_data['epp_pct_zscore']:.2f}",
            f"{site_data['ri_pct_zscore']:.2f}",
            f"{site_data['mas_pct_zscore']:.2f}",
        ],
        'Flagged': [
            "🚩" if site_data['pos_sales_flag'] == 1 else "✓",
            "🚩" if site_data['utilization_flag'] == 1 else "✓",
            "🚩" if site_data['asp_flag'] == 1 else "✓",
            "🚩" if site_data['eo_pct_flag'] == 1 else "✓",
            "🚩" if site_data['epp_pct_flag'] == 1 else "✓",
            "🚩" if site_data['ri_pct_flag'] == 1 else "✓",
            "🚩" if site_data['mas_pct_flag'] == 1 else "✓",
        ]
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

# ═════════════════════════════════════════════
# TAB 6: COHORT BASELINES
# ═════════════════════════════════════════════
with tab6:
    st.header("📋 Cohort Baselines")
    
    st.info("Baseline KPI ranges by Medicaid status, Tele-Opt status, Supply/Demand Quad, and Region (13-week average)")
    
    # Filter profiling data based on selected filters
    if not medicaid_options and not tele_opt:
        # Show all cohorts
        profiling_filtered = profiling.copy()
    else:
        profiling_filtered = profiling.copy()
        if medicaid_options:
            profiling_filtered = profiling_filtered[profiling_filtered['is_medicaid'] == 1.0]
        if tele_opt:
            profiling_filtered = profiling_filtered[profiling_filtered['is_tele_opt'] == 1.0]
    
    st.subheader("Baseline Summary by Cohort")
    
    # Display profiling data
    display_profiling = profiling_filtered[[
        'is_medicaid', 'is_tele_opt', 'Quad', 'Region',
        'pos_sales_median', 'utilization_median', 'asp_median', 
        'eo_pct_median', 'ri_pct_median', 'mas_pct_median'
    ]].copy()
    
    display_profiling.columns = ['Medicaid', 'Tele-Opt', 'Quad', 'Region',
                                'POS Sales', 'Utilization', 'ASP',
                                'EO %', 'RI %', 'MAS %']
    
    display_profiling['Medicaid'] = display_profiling['Medicaid'].map({0.0: 'Non-Med', 1.0: 'Med'})
    display_profiling['Tele-Opt'] = display_profiling['Tele-Opt'].map({0.0: 'No', 1.0: 'Yes'})
    display_profiling['Utilization'] = display_profiling['Utilization'].apply(lambda x: f"{x:.1%}")
    display_profiling['EO %'] = display_profiling['EO %'].apply(lambda x: f"{x:.1%}")
    display_profiling['RI %'] = display_profiling['RI %'].apply(lambda x: f"{x:.1%}")
    display_profiling['MAS %'] = display_profiling['MAS %'].apply(lambda x: f"{x:.1%}")
    display_profiling['POS Sales'] = display_profiling['POS Sales'].apply(lambda x: f"${x:.0f}")
    display_profiling['ASP'] = display_profiling['ASP'].apply(lambda x: f"${x:.0f}")
    
    st.dataframe(display_profiling, use_container_width=True)
    
    st.divider()
    
    # KPI comparison by Medicaid status
    st.subheader("KPI Medians: Medicaid vs Non-Medicaid")
    
    med_cohort = profiling[(profiling['is_medicaid'] == 1.0) & 
                           (profiling['is_tele_opt'] == 0.0)].groupby('Region')[
        ['utilization_median', 'asp_median', 'pos_sales_median']
    ].mean()
    
    nonmed_cohort = profiling[(profiling['is_medicaid'] == 0.0) & 
                              (profiling['is_tele_opt'] == 0.0)].groupby('Region')[
        ['utilization_median', 'asp_median', 'pos_sales_median']
    ].mean()
    
    col_med_vs1, col_med_vs2, col_med_vs3 = st.columns(3)
    
    with col_med_vs1:
        st.metric("Medicaid Avg ASP", f"${med_cohort['asp_median'].mean():.0f}",
                 delta=f"${nonmed_cohort['asp_median'].mean() - med_cohort['asp_median'].mean():.0f} vs Non-Med")
    
    with col_med_vs2:
        st.metric("Medicaid Avg Util", f"{med_cohort['utilization_median'].mean():.1%}",
                 delta=f"{nonmed_cohort['utilization_median'].mean() - med_cohort['utilization_median'].mean():.1%} vs Non-Med")
    
    with col_med_vs3:
        st.metric("Medicaid Avg POS", f"${med_cohort['pos_sales_median'].mean():.0f}",
                 delta=f"${nonmed_cohort['pos_sales_median'].mean() - med_cohort['pos_sales_median'].mean():.0f} vs Non-Med")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.markdown(
    """
    ---
    **Northstar Analytics — MyEyeDr Anomaly Detection Dashboard**
    
    Data as of: """ + latest_date.strftime("%B %d, %Y") + """
    
    Z-Score Threshold: 2.0σ | Anomaly Score: 0-7 scale | Composite anomaly identifies sites with 2+ KPI deviations
    """
)
