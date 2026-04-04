"""
Northstar Analytics — MED Diagnostic Toolkit
=============================================
Callable diagnostic suite for kurtosis, regression, seasonality,
structural breaks, Mann-Whitney U, Levene's, and predictive models.

Usage:
  python med_diagnostics.py                  → Run all diagnostics
  python med_diagnostics.py kurtosis         → Run kurtosis only
  python med_diagnostics.py regression       → Run regression only
  python med_diagnostics.py seasonality      → Run seasonality only
  python med_diagnostics.py breaks           → Run structural break detection
  python med_diagnostics.py mannwhitney      → Run Mann-Whitney U tests
  python med_diagnostics.py levene           → Run Levene's variance tests
  python med_diagnostics.py predict          → Run 5-year predictive models
  python med_diagnostics.py offenders        → Run tail offender identification

All outputs are Excel files with numeric formatting (not text).
Reads from the same data files as med_pipeline.py.

Author: Northstar Analytics (SMU Cox MSBA Capstone)
Date:   2026-03-31
"""

import pandas as pd
import numpy as np
from scipy import stats as sp_stats
import warnings
import os
import sys

warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "MED Office KPI Data_v3.30.26.xlsx")
OFFICE_MASTER_FILE = os.path.join(BASE_DIR, "Data_Dictionary.xlsx")

SCORE_KPIS = ['pos_sales', 'utilization', 'asp', 'eo_pct', 'epp_pct', 'mas_pct', 'ri_pct']

KPI_MAP = {
    'POS_Sales (Weekly)': 'pos_sales', 'EO% (Weekly)': 'eo_pct',
    'Exam Utilization %  (Weekly)': 'utilization', 'EPP% (Weekly)': 'epp_pct',
    'ASP (Weekly)': 'asp', 'TotalExam (Weekly)': 'total_exam',
    'MAS% (Weekly)': 'mas_pct', 'RI% (Weekly)': 'ri_pct',
    'Appts_Created (Weekly)': 'appts_created',
    'Patient Fall out (Cancelled + No Show) (Weekly)': 'patient_fallout',
    'CompExam% (Weekly)': 'comp_exam_pct', 'ExamSlotsCt (Weekly)': 'exam_slots',
}

KPI_LABELS = {
    'pos_sales': 'POS Sales ($)', 'utilization': 'Exam Utilization (%)',
    'asp': 'Avg Sales Price ($)', 'eo_pct': 'Exam-Only Rate (%)',
    'epp_pct': 'EPP Attach Rate (%)', 'mas_pct': 'Multi-Pair Rate (%)',
    'ri_pct': 'RI Upgrade Rate (%)',
}

# Kurtosis interpretation thresholds
# Excess kurtosis (Fisher): 0 = normal, positive = fat tails, negative = thin tails
#   0 to 1   → Normal range — distribution behaves like a bell curve
#   1 to 3   → Mild fat tails — some outlier stores but not alarming
#   3 to 10  → Fat tails — meaningful cluster of extreme stores
#   10+      → Very fat tails — a few stores dominate the distribution shape
#   50+      → Extreme — data quality issue or structural bimodality


# ─────────────────────────────────────────────
# DATA LOADING (shared across all diagnostics)
# ─────────────────────────────────────────────
def load_data():
    """Load and prep the full merged dataset. Returns (df, offender_ids)."""
    print("  Loading data...")
    df = pd.read_excel(DATA_FILE, sheet_name='Office Metrics', dtype={'Site ID': str})

    # Handle date in Site name column (v3.30.26 format)
    if 'Date' in df.columns:
        df['date'] = pd.to_datetime(df['Date'], format='mixed')
        df = df.drop(columns=['Date'], errors='ignore')
        df = df.rename(columns={'Site ID': 'site_id', 'Site name': 'site_name'})
    else:
        df['date'] = pd.to_datetime(df['Site name'], format='mixed', errors='coerce')
        df = df.rename(columns={'Site ID': 'site_id'})
        df = df.drop(columns=['Site name'], errors='ignore')

    df = df[df['date'].notna()].copy()
    df = df.drop(columns=['Category', 'category'], errors='ignore')
    df = df.rename(columns=KPI_MAP)
    df = df.sort_values(['site_id', 'date']).reset_index(drop=True)

    # Drop partial trailing weeks
    wc = df.groupby('date')['site_id'].nunique().sort_index()
    while len(wc) >= 2 and wc.iloc[-1] < wc.iloc[-2] * 0.5:
        drop_date = wc.index[-1]
        df = df[df['date'] != drop_date].copy()
        wc = wc.iloc[:-1]

    # Merge attributes
    attrs = pd.read_excel(DATA_FILE, sheet_name='Office Attributes', dtype={'Site ID': str})
    attr_cols = ['Site ID', 'Site name', 'Region', 'District', 'State', 'City',
                 'Opening Date', 'Quad']
    if 'Medicaid Insurance Location' in attrs.columns:
        attr_cols.append('Medicaid Insurance Location')
    attr_cols = [c for c in attr_cols if c in attrs.columns]
    attrs = attrs[attr_cols].copy()
    rename_map = {'Site ID': 'site_id', 'Site name': 'site_name', 'Opening Date': 'opening_date'}
    if 'Medicaid Insurance Location' in attrs.columns:
        rename_map['Medicaid Insurance Location'] = 'is_medicaid'
    attrs = attrs.rename(columns=rename_map)
    df = df.merge(attrs, on='site_id', how='left')

    # Merge Office Master
    try:
        om = pd.read_excel(OFFICE_MASTER_FILE, sheet_name='Office Master Dictionary',
                           dtype={'Office_ID': str})
        om = om[['Office_ID', 'Vintage', 'Tele_Opt']].rename(
            columns={'Office_ID': 'site_id', 'Vintage': 'vintage', 'Tele_Opt': 'is_tele_opt'})
        df = df.merge(om, on='site_id', how='left')
    except Exception:
        df['vintage'] = None
        df['is_tele_opt'] = None

    df = df[~df['Region'].isin(['Closed', '0'])].copy()

    # Vintage cohort
    def map_vc(v):
        if pd.isna(v): return 'Unknown'
        v = str(v)
        if 'pre2013' in v or '2013' in v or '2014' in v or '2015' in v: return 'Legacy (pre-2016)'
        if any(y in v for y in ['2016', '2017', '2018', '2019']): return 'Growth Era (2016-2019)'
        if any(y in v for y in ['2020', '2021', '2022']): return 'Post-COVID (2020-2022)'
        if any(y in v for y in ['2023', '2024', '2025']): return 'Recent (2023+)'
        return 'Acquisition'
    df['vintage_cohort'] = df['vintage'].apply(map_vc)
    if 'is_medicaid' in df.columns:
        df['is_medicaid'] = df['is_medicaid'].astype(float)

    df['quarter'] = df['date'].dt.to_period('Q').astype(str)
    df['cal_quarter'] = df['date'].dt.quarter

    # Identify offender stores
    latest = df[df['date'] == df['date'].max()].copy()
    med_util = latest['utilization'].median()
    med_sales = latest['pos_sales'].median()
    liability_ids = set(latest[(latest['utilization'] > med_util) & (latest['pos_sales'] < med_sales)]['site_id'])

    # Also identify persistent bottom-5% stores
    persistent = set()
    for kpi in SCORE_KPIS:
        site_avgs = df.groupby('site_id')[kpi].mean()
        bad_dir = 'high' if kpi == 'eo_pct' else 'low'
        thresh = site_avgs.quantile(0.95) if bad_dir == 'high' else site_avgs.quantile(0.05)
        if bad_dir == 'high':
            persistent.update(site_avgs[site_avgs >= thresh].index)
        else:
            persistent.update(site_avgs[site_avgs <= thresh].index)

    all_offenders = liability_ids | persistent
    df['is_offender'] = df['site_id'].isin(all_offenders).astype(int)

    print(f"  → {df['site_id'].nunique()} sites | {df['date'].nunique()} weeks | "
          f"{len(all_offenders)} offender sites identified")

    return df, all_offenders


# ─────────────────────────────────────────────
# KURTOSIS
# ─────────────────────────────────────────────
def run_kurtosis(df):
    """
    WHAT IS KURTOSIS?
    -----------------
    Kurtosis measures how heavy the TAILS of a distribution are compared to
    a normal (bell curve) distribution.

    PROCESS:
      1. Take all values for a KPI within a group (e.g., ASP for Region 1 in Q1)
      2. Compute the mean and standard deviation
      3. For each value, calculate: ((value - mean) / std) ^ 4
      4. Average all those 4th-power values
      5. Subtract 3 (this is "excess kurtosis" — 3 is the normal baseline)

    INTERPRETATION (excess kurtosis):
       0     → Normal bell curve. Tails are expected size.
      0-3    → Slightly fat tails. Minor outlier presence. Generally fine.
      3-10   → Fat tails. Meaningful outlier cluster hiding in the average.
      10-50  → Very fat tails. Extreme stores are distorting the picture.
      50+    → Distribution is broken. Investigate data quality or bimodality.

    WHY IT MATTERS:
    When kurtosis is HIGH, the average is a LIE. A few extreme stores are
    pulling/pushing the average while being invisible in it. You need to look
    at the percentiles (p5, p25, p50, p75, p95) to see the real picture.

    OUTPUT COLUMNS:
      - kpi:       Which KPI was measured
      - group:     'Region 1', 'Region 2', etc., or 'Offender'/'Healthy'
      - quarter:   Time period
      - n:         How many data points went into the calculation
      - kurtosis:  Excess kurtosis (0 = normal, higher = fatter tails)
      - skew:      Skewness (0 = symmetric, positive = right tail longer)
      - interpret:  Plain-English label for the kurtosis value
      - mean, std, p5, p25, p50, p75, p95: Distribution stats
    """
    print("\n[ KURTOSIS ] Computing distributional shape by Region and Offender status...")

    results = []

    def compute_group(group_data, kpi, group_label, quarter):
        vals = group_data[kpi].dropna()
        if len(vals) < 10:
            return None
        k = float(sp_stats.kurtosis(vals, fisher=True))
        s = float(sp_stats.skew(vals))

        # Interpretation
        abs_k = abs(k)
        if abs_k < 1:
            interp = "Normal"
        elif abs_k < 3:
            interp = "Mild fat tails"
        elif abs_k < 10:
            interp = "Fat tails — outlier cluster"
        elif abs_k < 50:
            interp = "Very fat tails — extreme outliers"
        else:
            interp = "EXTREME — investigate data quality"

        return {
            'kpi': kpi, 'kpi_label': KPI_LABELS.get(kpi, kpi),
            'group': group_label, 'quarter': quarter,
            'n': len(vals),
            'kurtosis': round(k, 2), 'skew': round(s, 2),
            'interpret': interp,
            'mean': round(vals.mean(), 4), 'std': round(vals.std(), 4),
            'p5': round(np.percentile(vals, 5), 4),
            'p25': round(np.percentile(vals, 25), 4),
            'p50': round(np.percentile(vals, 50), 4),
            'p75': round(np.percentile(vals, 75), 4),
            'p95': round(np.percentile(vals, 95), 4),
        }

    # By Region × Quarter
    for (q, r), grp in df.groupby(['quarter', 'Region']):
        for kpi in SCORE_KPIS:
            row = compute_group(grp, kpi, r, q)
            if row:
                results.append(row)

    # By Offender status × Quarter
    for (q, off), grp in df.groupby(['quarter', 'is_offender']):
        label = 'Offender Stores' if off == 1 else 'Healthy Stores'
        for kpi in SCORE_KPIS:
            row = compute_group(grp, kpi, label, q)
            if row:
                results.append(row)

    result_df = pd.DataFrame(results)

    # Export to Excel with proper numeric types
    outfile = os.path.join(BASE_DIR, 'diagnostic_kurtosis.xlsx')
    with pd.ExcelWriter(outfile, engine='openpyxl') as writer:
        result_df.to_excel(writer, sheet_name='All Results', index=False)

        # Summary sheet: latest quarter only, pivoted for easy reading
        latest_q = result_df['quarter'].max()
        summary = result_df[result_df['quarter'] == latest_q].pivot_table(
            index=['kpi', 'kpi_label'],
            columns='group',
            values=['kurtosis', 'p50'],
            aggfunc='first'
        )
        summary.columns = [f'{col[0]}_{col[1]}' for col in summary.columns]
        summary = summary.reset_index()
        summary.to_excel(writer, sheet_name='Summary (Latest Q)', index=False)

    print(f"  → {len(result_df)} rows → diagnostic_kurtosis.xlsx")
    print(f"  → Latest quarter: {latest_q}")

    # Print quick summary
    latest_net = result_df[(result_df['quarter'] == latest_q) &
                           (result_df['group'].isin(['Offender Stores', 'Healthy Stores']))]
    for kpi in SCORE_KPIS:
        kdf = latest_net[latest_net['kpi'] == kpi]
        for _, row in kdf.iterrows():
            flag = "⚠️" if abs(row['kurtosis']) >= 3 else "  "
            print(f"  {flag} {row['kpi_label']:<25} | {row['group']:<16} | "
                  f"kurtosis={row['kurtosis']:>8.2f} | {row['interpret']}")

    return result_df


# ─────────────────────────────────────────────
# REGRESSION
# ─────────────────────────────────────────────
def run_regression(df):
    """OLS regression: pos_sales ~ utilization + asp + eo_pct + ... + is_offender + interactions"""
    print("\n[ REGRESSION ] Fitting sales driver model with offender interactions...")

    panel = df.groupby(['site_id', 'quarter']).agg(
        pos_sales=('pos_sales', 'mean'), utilization=('utilization', 'mean'),
        asp=('asp', 'mean'), eo_pct=('eo_pct', 'mean'), epp_pct=('epp_pct', 'mean'),
        mas_pct=('mas_pct', 'mean'), ri_pct=('ri_pct', 'mean'),
        is_offender=('is_offender', 'first'), Region=('Region', 'first'),
    ).reset_index()

    panel = panel.dropna(subset=['pos_sales', 'utilization', 'asp', 'eo_pct'])

    features = ['utilization', 'asp', 'eo_pct', 'epp_pct', 'mas_pct', 'ri_pct', 'is_offender']
    X = panel[features].copy()
    X['offender_x_eo'] = X['is_offender'] * X['eo_pct']
    X['offender_x_asp'] = X['is_offender'] * X['asp']
    y = panel['pos_sales']

    # Drop any remaining NaN rows
    valid_mask = X.notna().all(axis=1) & y.notna()
    X = X[valid_mask]
    y = y[valid_mask]

    # Standardize — but drop zero-variance columns that would produce NaN
    stds = X.std()
    zero_var = stds[stds == 0].index.tolist()
    if zero_var:
        print(f"    Dropping zero-variance columns: {zero_var}")
        X = X.drop(columns=zero_var)

    X_std = (X - X.mean()) / X.std()
    X_std = X_std.fillna(0)  # Safety net for any remaining edge cases
    X_mat = np.column_stack([np.ones(len(X_std)), X_std.values])

    try:
        betas, _, _, _ = np.linalg.lstsq(X_mat, y.values, rcond=None)
    except np.linalg.LinAlgError:
        # Fallback: use pseudoinverse if SVD fails
        print("    SVD did not converge — using pseudoinverse fallback")
        pinv = np.linalg.pinv(X_mat)
        betas = pinv @ y.values

    y_pred = X_mat @ betas
    ss_res = np.sum((y.values - y_pred) ** 2)
    ss_tot = np.sum((y.values - y.values.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    n, p = X_mat.shape
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1)

    mse = ss_res / (n - p)
    try:
        var_b = mse * np.linalg.inv(X_mat.T @ X_mat).diagonal()
    except np.linalg.LinAlgError:
        var_b = mse * np.linalg.pinv(X_mat.T @ X_mat).diagonal()
    se_b = np.sqrt(np.abs(var_b))
    t_stats = betas / se_b
    p_vals = 2 * (1 - sp_stats.t.cdf(np.abs(t_stats), df=n - p))

    feature_names = ['intercept'] + list(X.columns)
    reg_results = []
    for i, feat in enumerate(feature_names):
        reg_results.append({
            'feature': feat,
            'beta_standardized': round(betas[i], 2),
            'std_error': round(se_b[i], 2),
            't_statistic': round(t_stats[i], 2),
            'p_value': round(p_vals[i], 6),
            'significant_at_05': 'Yes' if p_vals[i] < 0.05 else 'No',
        })

    reg_df = pd.DataFrame(reg_results)

    # By region
    region_results = []
    for region in sorted(panel['Region'].dropna().unique()):
        rp = panel[panel['Region'] == region]
        if len(rp) < 50:
            continue
        X_r = rp[['utilization', 'asp', 'eo_pct', 'epp_pct', 'mas_pct', 'ri_pct']].copy()
        X_r = X_r.dropna()
        y_r = rp.loc[X_r.index, 'pos_sales'].values
        stds_r = X_r.std()
        X_r = X_r.loc[:, stds_r > 0]
        X_r_std = (X_r - X_r.mean()) / X_r.std()
        X_r_std = X_r_std.fillna(0)
        X_r_mat = np.column_stack([np.ones(len(X_r_std)), X_r_std.values])
        try:
            b, _, _, _ = np.linalg.lstsq(X_r_mat, y_r, rcond=None)
        except np.linalg.LinAlgError:
            b = np.linalg.pinv(X_r_mat) @ y_r
        yp = X_r_mat @ b
        r2_r = 1 - np.sum((y_r - yp) ** 2) / np.sum((y_r - y_r.mean()) ** 2)
        region_results.append({'Region': region, 'R_squared': round(r2_r, 4), 'n': len(rp)})

    region_df = pd.DataFrame(region_results)

    outfile = os.path.join(BASE_DIR, 'diagnostic_regression.xlsx')
    with pd.ExcelWriter(outfile, engine='openpyxl') as writer:
        reg_df.to_excel(writer, sheet_name='Full Model', index=False)
        region_df.to_excel(writer, sheet_name='By Region', index=False)

    print(f"  → R² = {r2:.4f}, Adj R² = {adj_r2:.4f}, n = {n}")
    for _, row in reg_df.iterrows():
        sig = "***" if row['p_value'] < 0.001 else ("**" if row['p_value'] < 0.01 else ("*" if row['p_value'] < 0.05 else "   "))
        print(f"    {row['feature']:<20} β={row['beta_standardized']:>8.2f}  t={row['t_statistic']:>7.2f}  p={row['p_value']:.4f} {sig}")
    print(f"  → diagnostic_regression.xlsx")

    return reg_df


# ─────────────────────────────────────────────
# SEASONALITY
# ─────────────────────────────────────────────
def run_seasonality(df):
    """Kruskal-Wallis H-test for seasonal differences by calendar quarter."""
    print("\n[ SEASONALITY ] Testing KPI differences across Q1-Q2-Q3-Q4...")

    results = []

    def kw_test(data, kpi, label):
        groups = [grp[kpi].dropna().values for _, grp in data.groupby('cal_quarter')]
        if all(len(g) >= 20 for g in groups):
            stat, pval = sp_stats.kruskal(*groups)
            medians = {f'Q{i+1}_median': round(data[data['cal_quarter'] == i + 1][kpi].median(), 4)
                       for i in range(4)}
            results.append({
                'kpi': kpi, 'kpi_label': KPI_LABELS.get(kpi, kpi),
                'group': label,
                'H_statistic': round(stat, 2), 'p_value': round(pval, 6),
                'significant_at_05': 'Yes' if pval < 0.05 else 'No',
                **medians,
            })

    # Network level
    for kpi in SCORE_KPIS:
        kw_test(df, kpi, 'Network')

    # By region
    for region in sorted(df['Region'].dropna().unique()):
        for kpi in ['pos_sales', 'utilization', 'eo_pct']:
            kw_test(df[df['Region'] == region], kpi, region)

    # Offender vs healthy
    for off_val, label in [(1, 'Offender'), (0, 'Healthy')]:
        for kpi in ['pos_sales', 'utilization', 'eo_pct']:
            kw_test(df[df['is_offender'] == off_val], kpi, label)

    result_df = pd.DataFrame(results)
    outfile = os.path.join(BASE_DIR, 'diagnostic_seasonality.xlsx')
    result_df.to_excel(outfile, index=False)
    print(f"  → {len(result_df)} tests → diagnostic_seasonality.xlsx")
    for _, row in result_df[result_df['group'] == 'Network'].iterrows():
        sig = "✓" if row['significant_at_05'] == 'Yes' else " "
        print(f"    {sig} {row['kpi_label']:<25} H={row['H_statistic']:>8.2f}  p={row['p_value']:.6f}")

    return result_df


# ─────────────────────────────────────────────
# STRUCTURAL BREAKS
# ─────────────────────────────────────────────
def run_structural_breaks(df):
    """Rolling 13-week OLS to detect instability periods."""
    print("\n[ STRUCTURAL BREAKS ] Running rolling regression to find instability periods...")

    network = df.groupby('date')[SCORE_KPIS].mean().sort_index().reset_index()
    network['t'] = range(len(network))

    results = []
    for kpi in SCORE_KPIS:
        vals = network[kpi].values
        t = network['t'].values
        dates = network['date'].values

        for i in range(13, len(vals)):
            y = vals[i - 13:i]
            x = t[i - 13:i]
            if np.isnan(y).any():
                continue
            slope, intercept, r, p, se = sp_stats.linregress(x, y)
            resid = y - (slope * x + intercept)
            results.append({
                'date': pd.Timestamp(dates[i]).date(),
                'kpi': kpi, 'kpi_label': KPI_LABELS.get(kpi, kpi),
                'slope': round(slope, 6), 'r_squared': round(r ** 2, 4),
                'p_value': round(p, 6),
                'residual_variance': round(np.var(resid), 6),
            })

    result_df = pd.DataFrame(results)
    outfile = os.path.join(BASE_DIR, 'diagnostic_structural_breaks.xlsx')
    result_df.to_excel(outfile, index=False)
    print(f"  → {len(result_df)} rows → diagnostic_structural_breaks.xlsx")

    for kpi in SCORE_KPIS:
        kdf = result_df[result_df['kpi'] == kpi]
        if len(kdf) > 0:
            peak = kdf.loc[kdf['residual_variance'].idxmax()]
            print(f"    {KPI_LABELS.get(kpi, kpi):<25} peak instability: {peak['date']} "
                  f"(R²={peak['r_squared']:.4f})")

    return result_df


# ─────────────────────────────────────────────
# MANN-WHITNEY U
# ─────────────────────────────────────────────
def run_mannwhitney(df):
    """Non-parametric test: are offender and healthy store KPIs from different distributions?"""
    print("\n[ MANN-WHITNEY U ] Testing offender vs. healthy store distributions...")

    results = []
    for kpi in SCORE_KPIS:
        off = df[df['is_offender'] == 1][kpi].dropna()
        hlth = df[df['is_offender'] == 0][kpi].dropna()
        if len(off) >= 30 and len(hlth) >= 30:
            stat, pval = sp_stats.mannwhitneyu(off, hlth, alternative='two-sided')
            effect = stat / (len(off) * len(hlth))
            results.append({
                'kpi': kpi, 'kpi_label': KPI_LABELS.get(kpi, kpi),
                'offender_median': round(off.median(), 4),
                'healthy_median': round(hlth.median(), 4),
                'difference': round(off.median() - hlth.median(), 4),
                'U_statistic': round(stat, 0),
                'p_value': pval,
                'effect_size_r': round(effect, 4),
                'significant_at_001': 'Yes' if pval < 0.001 else 'No',
            })
            sig = "***" if pval < 0.001 else ""
            print(f"    {KPI_LABELS.get(kpi, kpi):<25} offender={off.median():.4f} "
                  f"vs healthy={hlth.median():.4f}  p={pval:.2e} {sig}")

    result_df = pd.DataFrame(results)
    outfile = os.path.join(BASE_DIR, 'diagnostic_mannwhitney.xlsx')
    result_df.to_excel(outfile, index=False)
    print(f"  → diagnostic_mannwhitney.xlsx")
    return result_df


# ─────────────────────────────────────────────
# LEVENE'S TEST
# ─────────────────────────────────────────────
def run_levene(df):
    """Test whether offender stores have significantly different VARIANCE than healthy stores."""
    print("\n[ LEVENE'S TEST ] Testing variance equality (offender vs. healthy)...")

    results = []
    for kpi in SCORE_KPIS:
        off = df[df['is_offender'] == 1][kpi].dropna()
        hlth = df[df['is_offender'] == 0][kpi].dropna()
        if len(off) >= 30 and len(hlth) >= 30:
            stat, pval = sp_stats.levene(off, hlth)
            results.append({
                'kpi': kpi, 'kpi_label': KPI_LABELS.get(kpi, kpi),
                'offender_variance': round(off.var(), 6),
                'healthy_variance': round(hlth.var(), 6),
                'variance_ratio': round(off.var() / hlth.var(), 2),
                'levene_statistic': round(stat, 2),
                'p_value': round(pval, 8),
                'significant_at_05': 'Yes' if pval < 0.05 else 'No',
            })
            ratio = off.var() / hlth.var()
            print(f"    {KPI_LABELS.get(kpi, kpi):<25} var_ratio={ratio:.2f}x  p={pval:.2e}")

    result_df = pd.DataFrame(results)
    outfile = os.path.join(BASE_DIR, 'diagnostic_levene.xlsx')
    result_df.to_excel(outfile, index=False)
    print(f"  → diagnostic_levene.xlsx")
    return result_df


# ─────────────────────────────────────────────
# PREDICTIVE MODELS
# ─────────────────────────────────────────────
def run_predict(df):
    """5-year projections: network, healthy, offender, and degradation scenario."""
    print("\n[ PREDICTIVE MODELS ] Projecting 5-year sales trajectories...")

    def fit_and_project(data, label):
        t = np.arange(len(data))
        y = data['pos_sales'].values
        valid = ~np.isnan(y)
        t, y = t[valid], y[valid]

        slope, intercept, r, p, se = sp_stats.linregress(t, y)
        base_q = pd.Period(data['quarter'].iloc[-1])

        projections = []
        for i in range(1, 21):
            future_t = len(data) - 1 + i
            projections.append({
                'quarter': str(base_q + i), 'group': label, 'type': 'projection',
                'pos_sales': round(slope * future_t + intercept, 2),
            })

        print(f"    {label:<20} slope={slope:>8.2f}/Q  R²={r**2:.4f}  current=${y[-1]:,.0f}")
        return projections, slope

    # Build quarterly aggregates
    net_q = df.groupby('quarter').agg(pos_sales=('pos_sales', 'mean')).reset_index()
    off_q = df[df['is_offender'] == 1].groupby('quarter').agg(pos_sales=('pos_sales', 'mean')).reset_index()
    hlth_q = df[df['is_offender'] == 0].groupby('quarter').agg(pos_sales=('pos_sales', 'mean')).reset_index()

    net_proj, net_slope = fit_and_project(net_q, 'Network')
    off_proj, off_slope = fit_and_project(off_q, 'Offenders')
    hlth_proj, hlth_slope = fit_and_project(hlth_q, 'Healthy')

    # Degradation scenario: offenders decline at 2x rate
    base_q = pd.Period(off_q['quarter'].iloc[-1])
    current_off = off_q['pos_sales'].iloc[-1]
    deg_proj = []
    for i in range(1, 21):
        deg_proj.append({
            'quarter': str(base_q + i), 'group': 'Offender Degradation (2x)',
            'type': 'projection',
            'pos_sales': round(current_off + (off_slope * 2) * i, 2),
        })

    # Historical
    hist = []
    for _, row in net_q.iterrows():
        hist.append({'quarter': row['quarter'], 'group': 'Network', 'type': 'historical', 'pos_sales': round(row['pos_sales'], 2)})
    for _, row in off_q.iterrows():
        hist.append({'quarter': row['quarter'], 'group': 'Offenders', 'type': 'historical', 'pos_sales': round(row['pos_sales'], 2)})
    for _, row in hlth_q.iterrows():
        hist.append({'quarter': row['quarter'], 'group': 'Healthy', 'type': 'historical', 'pos_sales': round(row['pos_sales'], 2)})

    all_data = hist + net_proj + off_proj + hlth_proj + deg_proj
    result_df = pd.DataFrame(all_data)

    outfile = os.path.join(BASE_DIR, 'diagnostic_projections.xlsx')
    result_df.to_excel(outfile, index=False)
    print(f"  → diagnostic_projections.xlsx")
    return result_df


# ─────────────────────────────────────────────
# OFFENDER IDENTIFICATION
# ─────────────────────────────────────────────
def run_offenders(df, offender_ids):
    """Identify and profile tail offender stores."""
    print("\n[ OFFENDERS ] Profiling persistent tail offender stores...")

    details = []
    for site_id in offender_ids:
        site_data = df[df['site_id'] == site_id]
        if len(site_data) == 0:
            continue
        first = site_data.iloc[0]

        # Which KPIs is this site in the bottom/top 5%?
        flagged = []
        for kpi in SCORE_KPIS:
            site_avg = site_data[kpi].mean()
            network_avg = df.groupby('site_id')[kpi].mean()
            bad_dir = 'high' if kpi == 'eo_pct' else 'low'
            thresh = network_avg.quantile(0.95) if bad_dir == 'high' else network_avg.quantile(0.05)
            if (bad_dir == 'high' and site_avg >= thresh) or (bad_dir == 'low' and site_avg <= thresh):
                flagged.append(kpi)

        details.append({
            'site_id': site_id, 'site_name': first.get('site_name', ''),
            'Region': first.get('Region', ''), 'District': first.get('District', ''),
            'State': first.get('State', ''), 'Quad': first.get('Quad', ''),
            'vintage_cohort': first.get('vintage_cohort', ''),
            'is_medicaid': first.get('is_medicaid', ''),
            'kpis_flagged': ', '.join(flagged), 'flag_count': len(flagged),
            'avg_pos_sales': round(site_data['pos_sales'].mean(), 0),
            'avg_utilization': round(site_data['utilization'].mean(), 4),
            'avg_asp': round(site_data['asp'].mean(), 0),
            'avg_eo_pct': round(site_data['eo_pct'].mean(), 4),
        })

    result_df = pd.DataFrame(details).sort_values('flag_count', ascending=False)
    outfile = os.path.join(BASE_DIR, 'diagnostic_offenders.xlsx')
    result_df.to_excel(outfile, index=False)

    multi = (result_df['flag_count'] >= 3).sum()
    print(f"  → {len(result_df)} offender sites, {multi} flagged on 3+ KPIs")
    print(f"  → diagnostic_offenders.xlsx")
    return result_df


# ─────────────────────────────────────────────
# MAIN — Run selected or all diagnostics
# ─────────────────────────────────────────────
def main():
    print("\n" + "=" * 60)
    print("  Northstar Analytics — MED Diagnostic Toolkit")
    print("=" * 60)

    # Parse command line argument
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
    else:
        target = 'all'

    valid = ['all', 'kurtosis', 'regression', 'seasonality', 'breaks',
             'mannwhitney', 'levene', 'predict', 'offenders']

    if target not in valid:
        print(f"\n  Usage: python med_diagnostics.py [{' | '.join(valid)}]")
        print(f"  Unknown target: '{target}'")
        return

    # Load data once
    df, offender_ids = load_data()

    # Run requested diagnostics
    if target in ('all', 'kurtosis'):
        run_kurtosis(df)
    if target in ('all', 'regression'):
        run_regression(df)
    if target in ('all', 'seasonality'):
        run_seasonality(df)
    if target in ('all', 'breaks'):
        run_structural_breaks(df)
    if target in ('all', 'mannwhitney'):
        run_mannwhitney(df)
    if target in ('all', 'levene'):
        run_levene(df)
    if target in ('all', 'predict'):
        run_predict(df)
    if target in ('all', 'offenders'):
        run_offenders(df, offender_ids)

    print("\n" + "=" * 60)
    print("  Diagnostics complete.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
