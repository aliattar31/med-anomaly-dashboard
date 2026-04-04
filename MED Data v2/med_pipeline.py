"""
Northstar Analytics -- MyEyeDr. Anomaly Detection Pipeline
==========================================================
Phase 2: Direction-Aware Alerting, KPI Weighting, Leading Indicators,
          Predictive Trajectory, Zero-Slots Handling
Author:  Northstar Analytics (SMU Cox MSBA Capstone)
Data:    MED Office KPI Data_v3.30.26.xlsx  (refreshed 2026-03-30)
Updated: 2026-04-02

Outputs:
  - med_clean.csv              -> Cleaned + merged dataset (all weeks, all sites)
  - med_features.csv           -> Feature-engineered dataset (rolling stats, deltas)
  - med_anomaly_scores.csv     -> Anomaly-scored dataset (z-scores, flags, ranked)
  - med_critical_alerts.csv    -> Critical Alert tier only
  - med_watch_list.csv         -> Watch tier only
  - med_positive_outliers.csv  -> Positive Outlier tier
  - med_profiling.csv          -> Baseline KPI ranges by cohort

Changes in v3.1 (2026-04-02):
  - Reports count of stores not in Office Master Dictionary (data gap)
  - Reports count of stores excluded for missing Region assignment
  - Added MED vintage maturity definitions as comments
  - Exclude offices without Region per MED 04/01 guidance
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
import os

warnings.filterwarnings('ignore')

# ---------------------------------------------
# CONFIG -- All thresholds in one place
# ---------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "MED Office KPI Data_v3.30.26.xlsx")
OFFICE_MASTER_FILE = os.path.join(BASE_DIR, "Data_Dictionary.xlsx")

ROLLING_WIN  = 4      # 4-week rolling window (~1 month)
Z_THRESHOLD  = 2.0    # Standard deviations to flag as anomaly
MIN_WEEKS    = 8      # Minimum history required to score a site

# Alert tier thresholds -- applied to NEGATIVE weighted score only
TIER_CRITICAL_WEIGHTED = 4.0   # weighted_negative_score >= 4.0 -> Critical Alert
TIER_WATCH_WEIGHTED    = 2.5   # weighted_negative_score >= 2.5 -> Watch
POSITIVE_OUTLIER_THRESHOLD = 3.0  # weighted_positive_score >= 3.0 -> Positive Outlier

# Backward-compatible unweighted thresholds (applied to anomaly_score)
TIER_CRITICAL = 3
TIER_WATCH    = 2

# --- KPI Weighting ---------------------------
WEIGHT_MAP = {
    'pos_sales':        2.0,   # Primary financial outcome
    'utilization':      2.0,   # Capacity and demand signal
    'asp':              1.5,   # Revenue per visit
    'eo_pct':           1.5,   # Conversion failure signal
    'epp_pct':          1.0,   # Attachment rate
    'ri_pct':           1.0,   # Refractive index upgrade
    'mas_pct':          1.0,   # Multiple pair sales
    'appts_created':    1.0,   # Leading -- appointment generation
    'patient_fallout':  1.5,   # Leading -- cancel + no-show combined signal
    'comp_exam_pct':    1.0,   # Utilization-related -- comprehensive exam share
}

# --- KPI Directionality ----------------------
# 'negative' = a DROP is bad; 'positive' = a SPIKE is bad
KPI_BAD_DIRECTION = {
    'pos_sales':        'negative',
    'utilization':      'negative',
    'asp':              'negative',
    'eo_pct':           'positive',   # Rising exam-only rate = bad
    'epp_pct':          'negative',
    'ri_pct':           'negative',
    'mas_pct':          'negative',
    'appts_created':    'negative',
    'patient_fallout':  'positive',   # Spiking fallout = bad
    'comp_exam_pct':    'negative',   # Dropping comp exam share = bad
}

# --- Scored KPIs -----------------------------
CORE_SCORE_KPIS = ['pos_sales', 'utilization', 'asp', 'eo_pct', 'epp_pct', 'ri_pct', 'mas_pct']
LEADING_INDICATOR_KPIS = ['appts_created', 'patient_fallout', 'comp_exam_pct']

# --- Regression Config -----------------------
REGRESSION_TARGET     = 'pos_sales'
REGRESSION_HORIZON    = 4
REGRESSION_TRAIN_WIN  = 13
REGRESSION_GREEN_PCT  =  0.02
REGRESSION_RED_PCT    = -0.02

# --- KPI Column Mapping (updated for v3.30.26 extract) ---
KPI_MAP = {
    'POS_Sales (Weekly)'                              : 'pos_sales',
    'EO% (Weekly)'                                    : 'eo_pct',
    'Exam Utilization %  (Weekly)'                    : 'utilization',
    'EPP% (Weekly)'                                   : 'epp_pct',
    'ExamSlotsCt (Weekly)'                            : 'exam_slots',
    'ASP (Weekly)'                                    : 'asp',
    'Appts_Created (Weekly)'                          : 'appts_created',
    'AR (Weekly)'                                     : 'ar',
    'AR% (Weekly)'                                    : 'ar_pct',
    'EO (Weekly)'                                     : 'eo',
    'EPP (Weekly)'                                    : 'epp',
    'CLExam (Weekly)'                                 : 'cl_exam',
    'CompExam (Weekly)'                               : 'comp_exam',
    'MAS (Weekly)'                                    : 'mas',
    'MAS% (Weekly)'                                   : 'mas_pct',
    'RI (Weekly)'                                     : 'ri',
    'RI% (Weekly)'                                    : 'ri_pct',
    'TotalExam (Weekly)'                              : 'total_exam',
    'CompExam% (Weekly)'                              : 'comp_exam_pct',
    'Patient Fall out (Cancelled + No Show) (Weekly)' : 'patient_fallout',
}

# Attribute columns to keep from Office Attributes sheet
ATTR_KEEP = [
    'Site ID', 'Site name', 'Region', 'District', 'State', 'City', 'Opening Date',
    'Quad', 'Square Footage', 'Goodway DMA',
    'Nearest Competitor', 'Competitor Count (1 mile ring)',
    'ACS - 2023 - Median Household Income in the Past 12 Months Estimate Median household income in the past 12 months (in 2023 inflation-adjusted dollars) - weightedAverage - 1mile',
    'ACS - 2023 - Total Population Estimate Total - 1mile',
    'Average Age At Transaction - 2024',
    'Medicaid Insurance Location',
]

ATTR_RENAME = {
    'ACS - 2023 - Median Household Income in the Past 12 Months Estimate Median household income in the past 12 months (in 2023 inflation-adjusted dollars) - weightedAverage - 1mile': 'median_hh_income_1mi',
    'ACS - 2023 - Total Population Estimate Total - 1mile': 'pop_1mi',
    'Average Age At Transaction - 2024': 'avg_customer_age',
    'Competitor Count (1 mile ring)': 'competitor_ct_1mi',
    'Medicaid Insurance Location': 'is_medicaid_kpi',
}

# Office Master fields from Data Dictionary
OFFICE_MASTER_KEEP = [
    'Office_ID', 'Medicaid_Location', 'isAcuity', 'Tele_Opt',
    'Property_Type', 'Vintage', 'of_Lanes', 'Status', 'Media_Market',
]


# ---------------------------------------------
# HELPER: Vintage Cohort Mapping
# MED definitions (per 04/01 check-in):
#   Pre-2025 stores = mature (stable performance expected)
#   2025-2026 stores = ramping (performance still developing)
# ---------------------------------------------
def map_vintage_cohort(v):
    if v is None:
        return 'Unknown'
    v = str(v)
    if 'pre2013' in v or '2013' in v or '2014' in v or '2015' in v:
        return 'Legacy (pre-2016)'
    if any(y in v for y in ['2016', '2017', '2018', '2019']):
        return 'Growth Era (2016-2019)'
    if any(y in v for y in ['2020', '2021', '2022']):
        return 'Post-COVID (2020-2022)'
    if any(y in v for y in ['2023', '2024', '2025']):
        return 'Recent (2023+)'
    return 'Acquisition'


# ---------------------------------------------
# HELPER: Resolve active SCORE_KPIS at runtime
# ---------------------------------------------
def resolve_score_kpis(df):
    """Return the list of KPIs to score, based on what columns exist in the data."""
    active = list(CORE_SCORE_KPIS)
    for kpi in LEADING_INDICATOR_KPIS:
        if kpi in df.columns and df[kpi].notna().sum() > 0:
            active.append(kpi)
            print(f"    -> Leading indicator '{kpi}' detected -- added to scoring")
        else:
            print(f"    -> Leading indicator '{kpi}' not in data -- skipped")
    return active


# ---------------------------------------------
# STEP 1: LOAD & CLEAN
# ---------------------------------------------
def load_and_clean(filepath):
    print("[ 1/6 ] Loading data...")

    # -- Load metrics --
    df = pd.read_excel(filepath, sheet_name='Office Metrics', dtype={'Site ID': str})

    # v3.30.26 structure: Date is now in "Site name" column; actual "Date" column removed
    # "Category" and "Warranty_Cnt (Weekly)" also removed in this extract
    if 'Date' in df.columns:
        # Old format (v3.6.26): Date column exists
        df['date'] = pd.to_datetime(df['Date'], format='mixed')
        df = df.drop(columns=['Date'], errors='ignore')
        df = df.rename(columns={'Site ID': 'site_id', 'Site name': 'site_name'})
    else:
        # New format (v3.30.26): Date is in "Site name", actual site names from Attributes
        df['date'] = pd.to_datetime(df['Site name'], format='mixed', errors='coerce')
        df = df.rename(columns={'Site ID': 'site_id'})
        df = df.drop(columns=['Site name'], errors='ignore')

    # Drop summary rows (1 per site -- NaN date, aggregate values, not weekly data)
    n_summary = df['date'].isna().sum()
    if n_summary > 0:
        print(f"    -> Dropping {n_summary} summary rows (NaN date)")
        df = df[df['date'].notna()].copy()

    # Drop partial trailing weeks (incomplete data at the tail of the extract)
    # If the latest week has <50% of the prior week's site count, it's partial data.
    weekly_counts = df.groupby('date')['site_id'].nunique().sort_index()
    if len(weekly_counts) >= 2:
        while len(weekly_counts) >= 2:
            latest_ct = weekly_counts.iloc[-1]
            prior_ct  = weekly_counts.iloc[-2]
            if latest_ct < prior_ct * 0.50:
                drop_date = weekly_counts.index[-1]
                n_drop = (df['date'] == drop_date).sum()
                print(f"    -> Dropping partial week {drop_date.date()} "
                      f"({latest_ct} sites vs {prior_ct} prior -- incomplete)")
                df = df[df['date'] != drop_date].copy()
                weekly_counts = weekly_counts.iloc[:-1]
            else:
                break

    # Drop Category column if present (removed in new extract)
    df = df.drop(columns=['Category', 'category'], errors='ignore')

    # Rename KPI columns
    df = df.rename(columns=KPI_MAP)
    df = df.sort_values(['site_id', 'date']).reset_index(drop=True)

    # -- Load Office Attributes --
    attrs = pd.read_excel(filepath, sheet_name='Office Attributes', dtype={'Site ID': str})
    keep = [c for c in ATTR_KEEP if c in attrs.columns]
    attrs = attrs[keep].rename(columns=ATTR_RENAME)
    attrs = attrs.rename(columns={
        'Site ID': 'site_id', 'Site name': 'site_name',
        'Opening Date': 'opening_date',
        'Square Footage': 'sq_footage', 'Goodway DMA': 'dma',
        'Nearest Competitor': 'nearest_competitor',
    })

    # -- Load Office Master from Data Dictionary --
    _om_site_ids = set()
    try:
        om = pd.read_excel(OFFICE_MASTER_FILE, sheet_name='Office Master Dictionary',
                           dtype={'Office_ID': str})
        om = om[OFFICE_MASTER_KEEP].rename(columns={'Office_ID': 'site_id'})
        _om_site_ids = set(om['site_id'].unique())
        om['vintage_cohort'] = om['Vintage'].apply(map_vintage_cohort)
        om = om.rename(columns={
            'Medicaid_Location': 'is_medicaid_dict',
            'isAcuity':          'is_acuity',
            'Tele_Opt':          'is_tele_opt',
            'Property_Type':     'property_type',
            'Vintage':           'vintage',
            'of_Lanes':          'exam_lanes',
            'Status':            'office_status',
            'Media_Market':      'media_market',
        })
        attrs = attrs.merge(om, on='site_id', how='left')
        matched = om['site_id'].isin(attrs['site_id']).sum()
        print(f"    -> Office Master merged: {matched} offices enriched")
    except Exception as e:
        print(f"    [!] Office Master error: {e}")
        for col in ['is_medicaid_dict', 'is_acuity', 'is_tele_opt', 'property_type',
                    'vintage', 'vintage_cohort', 'exam_lanes', 'office_status', 'media_market']:
            attrs[col] = None

    # -- Medicaid source resolution --
    # Primary: new "Medicaid Insurance Location" from KPI file (is_medicaid_kpi)
    # Fallback: Data Dictionary "Medicaid_Location" (is_medicaid_dict)
    # Jason's updated file is the authoritative Medicaid mapping going forward.
    if 'is_medicaid_kpi' in attrs.columns:
        attrs['is_medicaid'] = attrs['is_medicaid_kpi'].astype(float)
        # Fill gaps from Data Dictionary where new mapping is missing
        if 'is_medicaid_dict' in attrs.columns:
            mask = attrs['is_medicaid'].isna() & attrs['is_medicaid_dict'].notna()
            attrs.loc[mask, 'is_medicaid'] = attrs.loc[mask, 'is_medicaid_dict'].astype(float)
            dict_fills = mask.sum()
            if dict_fills > 0:
                print(f"    -> {dict_fills} Medicaid flags filled from Data Dictionary (not in new mapping)")
        # Report change from old mapping
        if 'is_medicaid_dict' in attrs.columns:
            both = attrs[attrs['is_medicaid_kpi'].notna() & attrs['is_medicaid_dict'].notna()]
            changed = (both['is_medicaid_kpi'].astype(float) != both['is_medicaid_dict'].astype(float)).sum()
            if changed > 0:
                print(f"    -> [!] {changed} offices changed Medicaid classification vs. Data Dictionary")
    elif 'is_medicaid_dict' in attrs.columns:
        attrs['is_medicaid'] = attrs['is_medicaid_dict'].astype(float)
    else:
        attrs['is_medicaid'] = np.nan

    # Drop intermediate Medicaid columns
    attrs = attrs.drop(columns=['is_medicaid_kpi', 'is_medicaid_dict'], errors='ignore')

    # -- Merge attributes into metrics --
    df = df.merge(attrs, on='site_id', how='left')

    # Report Data Dictionary gap (sites in metrics but not in Office Master)
    if _om_site_ids:
        metric_sites = set(df['site_id'].unique())
        not_in_om = len(metric_sites - _om_site_ids)
        if not_in_om > 0:
            print(f"    -> {not_in_om} sites in KPI data but NOT in Office Master (no Vintage)")

    # Remove closed/unassigned offices (per MED 04/01 guidance: no Region = inactive)
    if 'Region' in df.columns:
        no_region = df['Region'].isna() | df['Region'].isin(['Closed', '0'])
        n_excluded = df[no_region]['site_id'].nunique()
        if n_excluded > 0:
            print(f"    -> {n_excluded} sites excluded (no Region, Closed, or unassigned)")
        df = df[~no_region].copy()

    # -- Resolve active KPIs --
    score_kpis = resolve_score_kpis(df)

    # Flag & clip negative KPI values
    for kpi in score_kpis:
        if kpi not in df.columns:
            continue
        neg_mask = df[kpi] < 0
        if neg_mask.sum() > 0:
            df[f'{kpi}_dq_flag'] = neg_mask.astype(int)
            df[kpi] = df[kpi].clip(lower=0)
        else:
            df[f'{kpi}_dq_flag'] = 0

    # Clip comp_exam_pct > 1.0 (data quality: a few rows exceed 100%)
    if 'comp_exam_pct' in df.columns:
        df['comp_exam_pct'] = df['comp_exam_pct'].clip(lower=0, upper=1.0)

    # -- Enhancement 6: Zero-Slots Flag --
    if 'exam_slots' in df.columns:
        df['zero_slots_flag'] = (df['exam_slots'] == 0).astype(int)
        n_zero = df['zero_slots_flag'].sum()
        if n_zero > 0:
            print(f"    -> {n_zero:,} zero-slot weeks flagged (excluded from scoring)")
    else:
        df['zero_slots_flag'] = 0

    # Normalize boolean flags to float
    for col in ['is_medicaid', 'is_tele_opt', 'is_acuity']:
        if col in df.columns:
            df[col] = df[col].astype(float)

    # Derived: office age in years at each week
    if 'opening_date' in df.columns:
        df['office_age_yrs'] = ((df['date'] - pd.to_datetime(df['opening_date'], errors='coerce'))
                                 .dt.days / 365.25).round(1)

    # Derived: exams per lane
    if 'exam_lanes' in df.columns:
        df['exam_lanes'] = pd.to_numeric(df['exam_lanes'], errors='coerce')
    if 'total_exam' in df.columns and 'exam_lanes' in df.columns:
        df['exams_per_lane'] = np.where(
            (df['exam_lanes'].notna()) & (df['exam_lanes'] > 0),
            df['total_exam'] / df['exam_lanes'],
            np.nan
        )

    # -- Summary --
    print(f"    -> {df['site_id'].nunique()} sites | {df['date'].nunique()} weeks | {len(df):,} rows")
    print(f"    -> Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    if 'is_medicaid' in df.columns:
        latest_mask = df['date'] == df['date'].max()
        latest_slice = df[latest_mask]
        med_count    = (latest_slice['is_medicaid'] == 1.0).sum()
        nonmed_count = (latest_slice['is_medicaid'] == 0.0).sum()
        tele_count   = (latest_slice['is_tele_opt'] == 1.0).sum() if 'is_tele_opt' in df.columns else 0
        print(f"    -> Medicaid offices: {med_count} | Non-Medicaid: {nonmed_count}")
        print(f"    -> Tele-Opt offices: {tele_count}")

    return df, score_kpis


# ---------------------------------------------
# STEP 2: FEATURE ENGINEERING
# ---------------------------------------------
def engineer_features(df, score_kpis):
    print(f"[ 2/6 ] Engineering features (rolling={ROLLING_WIN}w)...")
    df = df.copy()

    for kpi in score_kpis:
        if kpi not in df.columns:
            continue
        grp = df.groupby('site_id')[kpi]

        # Rolling mean & std shifted by 1 -- current week vs PRIOR window
        df[f'{kpi}_roll_mean'] = grp.transform(
            lambda x: x.shift(1).rolling(ROLLING_WIN, min_periods=2).mean())
        df[f'{kpi}_roll_std'] = grp.transform(
            lambda x: x.shift(1).rolling(ROLLING_WIN, min_periods=2).std())

        # Week-over-week delta
        df[f'{kpi}_wow_delta'] = grp.transform(lambda x: x.diff())

        # % change vs prior week
        df[f'{kpi}_wow_pct_chg'] = grp.transform(
            lambda x: x.pct_change().replace([np.inf, -np.inf], np.nan))

        # 4-week trend slope
        df[f'{kpi}_4w_trend'] = grp.transform(
            lambda x: x.rolling(ROLLING_WIN, min_periods=ROLLING_WIN)
                       .apply(lambda w: (w.iloc[-1] - w.iloc[0]) / (len(w) - 1)
                              if len(w) > 1 else np.nan, raw=False))

    print(f"    -> Added {len(score_kpis) * 5} feature columns")
    return df


# ---------------------------------------------
# STEP 3: COHORT BASELINES
# ---------------------------------------------
def build_baselines(df, score_kpis):
    print("[ 3/6 ] Building cohort baselines (Medicaid x Tele-Opt x Quad x Region)...")

    cutoff = df['date'].max() - pd.Timedelta(weeks=13)
    recent = df[df['date'] >= cutoff].copy()

    cohort_cols = ['is_medicaid', 'is_tele_opt', 'Quad', 'Region']
    available = [c for c in cohort_cols if c in recent.columns and recent[c].notna().any()]

    kpis_in_data = [k for k in score_kpis if k in recent.columns]

    baseline = (
        recent.groupby(available)[kpis_in_data]
        .agg(['mean', 'std', 'median',
              lambda x: x.quantile(0.25),
              lambda x: x.quantile(0.75)])
    )
    baseline.columns = ['_'.join(map(str, c)).replace('<lambda_0>', 'p25').replace('<lambda_1>', 'p75')
                        for c in baseline.columns]
    baseline = baseline.reset_index()

    if 'is_medicaid' in recent.columns:
        med_asp   = recent[recent['is_medicaid'] == 1.0]['asp'].median()
        nomed_asp = recent[recent['is_medicaid'] == 0.0]['asp'].median()
        print(f"    -> Medicaid median ASP: ${med_asp:.0f} | Non-Medicaid: ${nomed_asp:.0f}")
        med_util   = recent[recent['is_medicaid'] == 1.0]['utilization'].median()
        nomed_util = recent[recent['is_medicaid'] == 0.0]['utilization'].median()
        print(f"    -> Medicaid median Utilization: {med_util:.1%} | Non-Medicaid: {nomed_util:.1%}")

    print(f"    -> {len(baseline)} cohort segments profiled")
    return baseline


# ---------------------------------------------
# STEP 4: ANOMALY SCORING (Direction-Aware + Weighted)
# ---------------------------------------------
def score_anomalies(df, baseline, score_kpis):
    print(f"[ 4/6 ] Scoring anomalies (z-threshold={Z_THRESHOLD}, direction-aware, weighted)...")
    df = df.copy()

    # Only score sites with sufficient history
    site_weeks = df.groupby('site_id')['date'].count()
    eligible = site_weeks[site_weeks >= MIN_WEEKS].index
    df['has_min_history'] = df['site_id'].isin(eligible)

    # -- Z-score + Flag each KPI --
    flag_cols = []
    for kpi in score_kpis:
        if kpi not in df.columns:
            continue
        z_col    = f'{kpi}_zscore'
        flag_col = f'{kpi}_flag'

        roll_mean = df[f'{kpi}_roll_mean']
        roll_std  = df[f'{kpi}_roll_std']
        safe_std  = roll_std.replace(0, np.nan)
        df[z_col] = (df[kpi] - roll_mean) / safe_std

        dq_col = f'{kpi}_dq_flag' if f'{kpi}_dq_flag' in df.columns else None
        dq_ok  = (df[dq_col] == 0) if dq_col else True

        df[flag_col] = (
            (df[z_col].abs() > Z_THRESHOLD) &
            df['has_min_history'] &
            dq_ok &
            (df['zero_slots_flag'] == 0)
        ).astype(int)

        flag_cols.append(flag_col)

    # -- Direction per KPI --
    for kpi in score_kpis:
        if kpi not in df.columns:
            continue
        df[f'{kpi}_direction'] = np.where(
            df[f'{kpi}_flag'] == 1,
            np.where(df[f'{kpi}_zscore'] < 0, 'below_normal', 'above_normal'),
            'normal'
        )

    # -- Backward-compatible unweighted score --
    df['anomaly_score'] = df[flag_cols].sum(axis=1)

    # -- Direction-Aware Scoring --
    neg_flag_cols = []
    pos_flag_cols = []
    for kpi in score_kpis:
        if kpi not in df.columns:
            continue
        flag_col = f'{kpi}_flag'
        dir_col  = f'{kpi}_direction'
        bad_dir  = KPI_BAD_DIRECTION.get(kpi, 'negative')

        neg_col = f'{kpi}_neg_flag'
        pos_col = f'{kpi}_pos_flag'

        if bad_dir == 'negative':
            df[neg_col] = ((df[flag_col] == 1) & (df[dir_col] == 'below_normal')).astype(int)
            df[pos_col] = ((df[flag_col] == 1) & (df[dir_col] == 'above_normal')).astype(int)
        else:
            df[neg_col] = ((df[flag_col] == 1) & (df[dir_col] == 'above_normal')).astype(int)
            df[pos_col] = ((df[flag_col] == 1) & (df[dir_col] == 'below_normal')).astype(int)

        neg_flag_cols.append(neg_col)
        pos_flag_cols.append(pos_col)

    df['negative_score'] = df[neg_flag_cols].sum(axis=1)
    df['positive_score'] = df[pos_flag_cols].sum(axis=1)

    # -- Weighted Scores --
    weighted_neg = pd.Series(0.0, index=df.index)
    weighted_pos = pd.Series(0.0, index=df.index)
    for kpi in score_kpis:
        if kpi not in df.columns:
            continue
        w = WEIGHT_MAP.get(kpi, 1.0)
        weighted_neg += df[f'{kpi}_neg_flag'] * w
        weighted_pos += df[f'{kpi}_pos_flag'] * w

    df['weighted_negative_score'] = weighted_neg.round(1)
    df['weighted_positive_score'] = weighted_pos.round(1)

    # -- Primary Driver --
    def get_primary_driver(row):
        flagged = {}
        for kpi in score_kpis:
            if kpi not in df.columns:
                continue
            if row.get(f'{kpi}_neg_flag', 0) == 1 and pd.notna(row.get(f'{kpi}_zscore')):
                flagged[kpi] = abs(row[f'{kpi}_zscore'])
        return max(flagged, key=flagged.get) if flagged else None

    df['primary_driver'] = df.apply(get_primary_driver, axis=1)

    # -- Anomaly Type Classification --
    def classify_anomaly(row):
        if row['negative_score'] == 0:
            return 'Normal'

        neg_drivers = [kpi for kpi in score_kpis
                       if kpi in df.columns and row.get(f'{kpi}_neg_flag', 0) == 1]
        is_tele = row.get('is_tele_opt', 0) == 1.0
        is_med  = row.get('is_medicaid', 0) == 1.0

        if 'utilization' in neg_drivers or 'pos_sales' in neg_drivers:
            if 'asp' in neg_drivers:
                if is_med:
                    return 'Medicaid Payer Mix Shift'
                return 'Pricing / Mix Issue'
            if 'eo_pct' in neg_drivers:
                return 'Low Exam Conversion'
            if is_tele:
                return 'Tele-Opt Capacity Watch'
            if any(k in neg_drivers for k in LEADING_INDICATOR_KPIS):
                return 'Demand Warning'
            return 'Operational Risk'
        if 'asp' in neg_drivers:
            if is_med:
                return 'Medicaid Payer Mix Shift'
            return 'Pricing / Mix Issue'
        if all(k in LEADING_INDICATOR_KPIS for k in neg_drivers):
            return 'Demand Warning'
        if row['negative_score'] >= 4:
            return 'Multi-KPI Alert'
        return 'Multi-KPI Watch'

    df['anomaly_type'] = df.apply(classify_anomaly, axis=1)

    # -- Alert Tier (weighted negative) --
    def assign_tier(row):
        wns = row['weighted_negative_score']
        if wns >= TIER_CRITICAL_WEIGHTED:
            return 'Critical Alert'
        elif wns >= TIER_WATCH_WEIGHTED:
            return 'Watch'
        elif row['negative_score'] >= 1:
            return 'Noise'
        else:
            return 'Clean'

    df['alert_tier'] = df.apply(assign_tier, axis=1)

    # -- Positive Outlier Tier --
    df['positive_tier'] = np.where(
        df['weighted_positive_score'] >= POSITIVE_OUTLIER_THRESHOLD,
        'Positive Outlier', 'Normal'
    )

    # -- Backward-compatible unweighted tier --
    df['alert_tier_unweighted'] = df['anomaly_score'].apply(
        lambda s: 'Critical Alert' if s >= TIER_CRITICAL
                  else ('Watch' if s >= TIER_WATCH
                        else ('Noise' if s == 1 else 'Clean'))
    )

    flagged_neg = (df['negative_score'] > 0).sum()
    flagged_pos = (df['positive_score'] > 0).sum()
    print(f"    -> {flagged_neg:,} negative-flagged observations | "
          f"{flagged_pos:,} positive-flagged observations")
    return df


# ---------------------------------------------
# STEP 5: PREDICTIVE SALES TRAJECTORY (OLS)
# ---------------------------------------------
def predict_trajectory(df, score_kpis):
    print(f"[ 5/6 ] Building sales trajectory predictions (horizon={REGRESSION_HORIZON}w)...")

    feature_kpis = [k for k in score_kpis if k in df.columns and k != REGRESSION_TARGET]
    df = df.copy()
    df['_target_future_sales'] = df.groupby('site_id')[REGRESSION_TARGET].shift(-REGRESSION_HORIZON)

    latest_date = df['date'].max()
    results = []

    for site_id, grp in df.groupby('site_id'):
        grp = grp.sort_values('date')
        if len(grp) < REGRESSION_TRAIN_WIN + REGRESSION_HORIZON:
            results.append({'site_id': site_id, 'sales_trajectory': 'insufficient_data'})
            continue

        train = grp[grp['_target_future_sales'].notna()].tail(REGRESSION_TRAIN_WIN)
        if len(train) < 8:
            results.append({'site_id': site_id, 'sales_trajectory': 'insufficient_data'})
            continue

        X_cols = [k for k in feature_kpis if train[k].notna().sum() >= 5]
        if len(X_cols) == 0:
            results.append({'site_id': site_id, 'sales_trajectory': 'insufficient_data'})
            continue

        X_train = train[X_cols].fillna(train[X_cols].median())
        y_train = train['_target_future_sales']

        valid = X_train.notna().all(axis=1) & y_train.notna()
        X_train = X_train[valid]
        y_train = y_train[valid]

        if len(y_train) < 5:
            results.append({'site_id': site_id, 'sales_trajectory': 'insufficient_data'})
            continue

        try:
            X_mat = np.column_stack([np.ones(len(X_train)), X_train.values])
            betas, _, _, _ = np.linalg.lstsq(X_mat, y_train.values, rcond=None)

            latest_row = grp[grp['date'] == latest_date]
            if len(latest_row) == 0:
                results.append({'site_id': site_id, 'sales_trajectory': 'insufficient_data'})
                continue

            X_pred = latest_row[X_cols].fillna(train[X_cols].median()).values[0]
            X_pred_full = np.concatenate([[1.0], X_pred])
            predicted = X_pred_full @ betas

            current_sales = latest_row[REGRESSION_TARGET].values[0]
            pct_change = (predicted - current_sales) / current_sales if current_sales > 0 else 0.0

            if pct_change >= REGRESSION_GREEN_PCT:
                trajectory = 'green'
            elif pct_change <= REGRESSION_RED_PCT:
                trajectory = 'red'
            else:
                trajectory = 'yellow'

            results.append({
                'site_id': site_id,
                'sales_trajectory': trajectory,
                'predicted_sales_4w': round(predicted, 2),
                'trajectory_pct_change': round(pct_change, 4),
            })
        except Exception:
            results.append({'site_id': site_id, 'sales_trajectory': 'model_error'})

    df = df.drop(columns=['_target_future_sales'])

    traj_df = pd.DataFrame(results)
    if len(traj_df) > 0:
        df = df.merge(traj_df, on='site_id', how='left')
    else:
        df['sales_trajectory'] = 'insufficient_data'

    if 'sales_trajectory' in df.columns:
        latest = df[df['date'] == latest_date]
        for color in ['green', 'yellow', 'red', 'insufficient_data', 'model_error']:
            count = (latest['sales_trajectory'] == color).sum()
            if count > 0:
                print(f"    -> {color}: {count} sites")

    return df


# ---------------------------------------------
# STEP 6: EXPORT
# ---------------------------------------------
def export(df_clean, df_features, df_scored, baseline, score_kpis):
    print("[ 6/6 ] Exporting outputs...")

    # -- Verify dashboard filter columns --
    filter_cols = ['District', 'State', 'City', 'vintage_cohort', 'is_medicaid', 'is_tele_opt']
    present = [c for c in filter_cols if c in df_scored.columns]
    missing = [c for c in filter_cols if c not in df_scored.columns]
    if missing:
        print(f"    [!] Dashboard filter columns missing from scored output: {missing}")
    else:
        print(f"    [ok] All dashboard filter columns confirmed: {present}")

    df_clean.to_csv('med_clean.csv', index=False)
    print(f"    -> med_clean.csv ({len(df_clean):,} rows)")

    df_features.to_csv('med_features.csv', index=False)
    print(f"    -> med_features.csv ({len(df_features):,} rows)")

    latest_date = df_scored['date'].max()
    latest = (df_scored[df_scored['date'] == latest_date]
              .sort_values('weighted_negative_score', ascending=False))
    latest.to_csv('med_anomaly_scores.csv', index=False)
    print(f"    -> med_anomaly_scores.csv ({len(latest):,} sites scored, week of {latest_date.date()})")

    critical = latest[latest['alert_tier'] == 'Critical Alert']
    watch    = latest[latest['alert_tier'] == 'Watch']
    positive = latest[latest['positive_tier'] == 'Positive Outlier']

    critical.to_csv('med_critical_alerts.csv', index=False)
    watch.to_csv('med_watch_list.csv', index=False)
    positive.to_csv('med_positive_outliers.csv', index=False)

    print(f"    -> med_critical_alerts.csv ({len(critical)} sites -- immediate attention)")
    print(f"    -> med_watch_list.csv ({len(watch)} sites -- monitor trend)")
    print(f"    -> med_positive_outliers.csv ({len(positive)} sites -- positive recognition)")

    baseline.to_csv('med_profiling.csv', index=False)
    print(f"    -> med_profiling.csv ({len(baseline)} cohort segments)")


# ---------------------------------------------
# MAIN
# ---------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("  Northstar Analytics -- MED Anomaly Detection Pipeline v3.1")
    print("  Data: MED Office KPI Data_v3.30.26.xlsx")
    print("=" * 60 + "\n")

    df_clean, score_kpis = load_and_clean(DATA_FILE)
    df_features = engineer_features(df_clean, score_kpis)
    baseline    = build_baselines(df_clean, score_kpis)
    df_scored   = score_anomalies(df_features, baseline, score_kpis)
    df_scored   = predict_trajectory(df_scored, score_kpis)
    export(df_clean, df_features, df_scored, baseline, score_kpis)

    # -- Summary Report --
    print("\n" + "-" * 60)
    print("  ANOMALY SUMMARY -- Most Recent Week (Direction-Aware)")
    print("-" * 60)

    latest_date = df_scored['date'].max()
    latest = df_scored[df_scored['date'] == latest_date]

    print(f"\n  Week of: {latest_date.date()}")
    print(f"  Sites scored:        {len(latest)}")
    print(f"  Active KPIs:         {len(score_kpis)} ({', '.join(score_kpis)})")
    print()

    print("  -- NEGATIVE (Underperformance) --")
    print(f"  Critical Alert:      {(latest['alert_tier'] == 'Critical Alert').sum()} sites "
          f"(weighted_neg >= {TIER_CRITICAL_WEIGHTED})")
    print(f"  Watch:               {(latest['alert_tier'] == 'Watch').sum()} sites "
          f"(weighted_neg >= {TIER_WATCH_WEIGHTED})")
    print(f"  Noise/Clean:         {(latest['alert_tier'].isin(['Noise', 'Clean'])).sum()} sites")
    print()
    print("  -- POSITIVE (Overperformance) --")
    print(f"  Positive Outlier:    {(latest['positive_tier'] == 'Positive Outlier').sum()} sites "
          f"(weighted_pos >= {POSITIVE_OUTLIER_THRESHOLD})")

    actionable = latest[latest['alert_tier'].isin(['Critical Alert', 'Watch'])]
    if 'is_medicaid' in latest.columns and len(actionable) > 0:
        print()
        for med_flag, label in [(1.0, 'Medicaid'), (0.0, 'Non-Medicaid')]:
            seg = actionable[actionable['is_medicaid'] == med_flag]
            crit = (seg['alert_tier'] == 'Critical Alert').sum()
            wtch = (seg['alert_tier'] == 'Watch').sum()
            if len(seg) > 0:
                print(f"  {label:<14} -- critical: {crit:>3} | watch: {wtch:>3} | total actionable: {len(seg):>3}")
        if 'is_tele_opt' in latest.columns:
            tele = actionable[actionable['is_tele_opt'] == 1.0]
            if len(tele) > 0:
                print(f"  {'Tele-Opt':<14} -- critical: {(tele['alert_tier'] == 'Critical Alert').sum():>3} "
                      f"| watch: {(tele['alert_tier'] == 'Watch').sum():>3} "
                      f"| total actionable: {len(tele):>3}")

    if len(actionable) > 0:
        type_counts = actionable['anomaly_type'].value_counts()
        print("\n  Actionable Flags by Type (Critical + Watch only):")
        for t, c in type_counts.items():
            print(f"    {t:<30} {c}")

    if 'sales_trajectory' in latest.columns:
        print("\n  -- SALES TRAJECTORY (4-week forecast) --")
        for color, label in [('green', 'Improving'), ('yellow', 'Stable'), ('red', 'Declining')]:
            count = (latest['sales_trajectory'] == color).sum()
            print(f"  {label:<20} {count} sites")
        insuf = (latest['sales_trajectory'] == 'insufficient_data').sum()
        if insuf > 0:
            print(f"  {'Insufficient data':<20} {insuf} sites")

    print("\n  Top 10 Sites by Weighted Negative Score (Critical Alerts):")
    top_cols = ['site_id', 'site_name', 'Region', 'Quad', 'is_medicaid',
                'is_tele_opt', 'vintage_cohort', 'weighted_negative_score',
                'negative_score', 'alert_tier', 'anomaly_type', 'primary_driver',
                'sales_trajectory']
    top_cols = [c for c in top_cols if c in latest.columns]
    critical_sites = latest[latest['alert_tier'] == 'Critical Alert']
    if len(critical_sites) > 0:
        print(critical_sites.nlargest(10, 'weighted_negative_score')[top_cols].to_string(index=False))
    else:
        print("    No Critical Alerts this week.")

    print("\n  Score Distribution (negative_score):")
    print(latest['negative_score'].value_counts().sort_index().to_string())

    print("\n  Score Distribution (weighted_negative_score):")
    wns_bins = pd.cut(latest['weighted_negative_score'],
                      bins=[-0.1, 0, 1, 2, 3, 4, 5, 10, 20],
                      labels=['0', '0.1-1', '1.1-2', '2.1-3', '3.1-4', '4.1-5', '5.1-10', '10+'])
    print(wns_bins.value_counts().sort_index().to_string())

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
