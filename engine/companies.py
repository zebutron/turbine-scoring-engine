"""
Company scoring: Budget x Alignment x Demand -> Company Score (0-100).

Migrated from score_companies_improved_2025-09-09.py. All scoring logic preserved.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from engine.config import load_config as _load_config
from engine.normalize import normalize_scores_0_100

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = _SCRIPT_DIR.parent


def load_config():
    """Load scoring configuration from latest JSON file in configs/."""
    config_dir = _REPO_ROOT / 'configs'
    config_files = sorted(config_dir.glob('SCORE_TUNING_CONFIG_*.json'), reverse=True)
    if not config_files:
        return _load_config()
    import json
    config_path = config_files[0]
    logging.info(f"Loading config: {config_path.name}")
    with open(config_path, 'r') as f:
        return json.load(f)


def safe_float(value):
    """Safely convert value to float."""
    if pd.isna(value) or value == '' or value is None:
        return np.nan
    try:
        if isinstance(value, str):
            clean_val = value.replace('$', '').replace(',', '').replace('%', '').strip()
            return float(clean_val)
        return float(value)
    except (ValueError, TypeError):
        return np.nan


def calculate_percentile_score(value, series, invert=False):
    """Calculate percentile score (0-100) for value within series."""
    if pd.isna(value):
        return 0.0

    clean_series = pd.Series([safe_float(v) for v in series]).dropna()
    if clean_series.empty:
        return 0.0

    clean_value = safe_float(value)
    if pd.isna(clean_value):
        return 0.0

    percentile = stats.percentileofscore(clean_series, clean_value, kind='rank')
    if invert:
        percentile = 100 - percentile
    return percentile


def score_binary_flag(value, max_points):
    """Score binary flags (X = max points, else 0)."""
    return max_points if str(value).strip().upper() == 'X' else 0


def calculate_status_score(status_value, change_date, config):
    """Calculate sales funnel status score with time decay."""
    if pd.isna(status_value) or not status_value:
        return 0.0

    status_str = str(status_value).lower().strip()

    status_mapping = {
        '6 - previous customer': {'points': 10, 'half_life_days': 730},
        '7 - previous customer': {'points': 10, 'half_life_days': 730},
        '8 - stand down': {'points': 10, 'half_life_days': 730},
        '5 - customer': {'points': 8, 'half_life_days': 365},
        '4 - contract out': {'points': 8, 'half_life_days': 365},
        'met with matt': {'points': 6, 'half_life_days': 180},
        'lt (quarterly) followup': {'points': 6, 'half_life_days': 180},
        'qualified': {'points': 5, 'half_life_days': 90},
        'disco incoming': {'points': 2, 'half_life_days': 30},
    }

    match_info = None
    for status_key, info in status_mapping.items():
        if status_key in status_str:
            match_info = info
            break

    if not match_info:
        return 0.0

    base_points = match_info['points']

    if pd.isna(change_date) or not change_date:
        return base_points

    try:
        change_dt = pd.to_datetime(change_date, errors='coerce')
        if pd.isna(change_dt):
            return base_points

        now = datetime.now(timezone.utc)
        if change_dt.tz is None:
            change_dt = change_dt.tz_localize('UTC')

        days_old = max(0, (now - change_dt).days)
        decay_factor = 0.5 ** (days_old / match_info['half_life_days'])

        return base_points * decay_factor
    except Exception:
        return base_points


def calculate_volatility_components(df: pd.DataFrame):
    """Calculate volatility sub-components per spec."""
    logging.info("   Calculating volatility sub-components...")

    # Revenue Change (weight 5)
    rev_change_scores = []
    if 'Rev Change % (ST)' in df.columns:
        rev_change_series = df['Rev Change % (ST)'].apply(safe_float)
        for value in rev_change_series:
            if pd.isna(value):
                rev_change_scores.append(0.0)
            else:
                percentile = calculate_percentile_score(value, rev_change_series, invert=True)
                rev_change_scores.append(percentile)
    else:
        rev_change_scores = [0.0] * len(df)

    # Runway Change (weight 4)
    runway_scores = []
    if 'Latest Funding Amount' in df.columns and 'Latest Funding Date' in df.columns:
        logging.info("   Processing runway calculations...")
        all_adjusted = []
        now = datetime.now()

        for _, row in df.iterrows():
            funding_amount = safe_float(row.get('Latest Funding Amount'))
            funding_date = row.get('Latest Funding Date')
            if not pd.isna(funding_amount) and not pd.isna(funding_date):
                try:
                    funding_dt = pd.to_datetime(funding_date, errors='coerce')
                    if not pd.isna(funding_dt):
                        days_old = max(0, (now - funding_dt.to_pydatetime()).days)
                        decay_factor = 0.5 ** (days_old / 365)
                        all_adjusted.append(funding_amount * decay_factor)
                except Exception:
                    pass

        for _, row in df.iterrows():
            funding_amount = safe_float(row.get('Latest Funding Amount'))
            funding_date = row.get('Latest Funding Date')
            if pd.isna(funding_amount) or pd.isna(funding_date):
                runway_scores.append(0.0)
                continue
            try:
                funding_dt = pd.to_datetime(funding_date, errors='coerce')
                if pd.isna(funding_dt):
                    runway_scores.append(0.0)
                    continue
                days_old = max(0, (now - funding_dt.to_pydatetime()).days)
                decay_factor = 0.5 ** (days_old / 365)
                adjusted_amount = funding_amount * decay_factor
                if all_adjusted:
                    percentile = stats.percentileofscore(all_adjusted, adjusted_amount, kind='rank')
                    runway_scores.append(percentile)
                else:
                    runway_scores.append(0.0)
            except Exception:
                runway_scores.append(0.0)
    else:
        runway_scores = [0.0] * len(df)

    # Headcount Change (weight 3)
    headcount_change_scores = []
    if 'Employee Change % (GJ)' in df.columns:
        headcount_series = df['Employee Change % (GJ)'].apply(safe_float)
        for value in headcount_series:
            if pd.isna(value):
                headcount_change_scores.append(0.0)
            else:
                percentile = calculate_percentile_score(value, headcount_series, invert=True)
                headcount_change_scores.append(percentile)
    else:
        headcount_change_scores = [0.0] * len(df)

    return {
        'revenue_change_scores': rev_change_scores,
        'runway_scores': runway_scores,
        'headcount_change_scores': headcount_change_scores
    }


def get_company_url(row):
    """Get best available URL for company."""
    website_url = row.get('Website URL', '')
    linkedin_url = row.get('Company Linkedin URL', '')

    if website_url and not pd.isna(website_url) and str(website_url).strip():
        return str(website_url).strip()
    elif linkedin_url and not pd.isna(linkedin_url) and str(linkedin_url).strip():
        return str(linkedin_url).strip()
    else:
        return ''


def normalize_pillar(raw_scores):
    """Min-max normalize pillar scores to 0-100."""
    if not raw_scores or all(pd.isna(s) for s in raw_scores):
        return [0] * len(raw_scores)

    min_val = min(s for s in raw_scores if not pd.isna(s))
    max_val = max(s for s in raw_scores if not pd.isna(s))

    if max_val == min_val:
        return [50] * len(raw_scores)

    normalized = []
    for score in raw_scores:
        if pd.isna(score):
            normalized.append(0)
        else:
            norm_score = ((score - min_val) / (max_val - min_val)) * 100
            normalized.append(round(norm_score, 1))

    return normalized


def score_companies(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Score companies with all improvements per 2025-07-27 specification."""
    logging.info(f"Scoring {len(df):,} companies...")

    result_df = df.copy()

    alignment_weight = config['companyScore']['pillars']['Alignment']['weight']
    budget_weight = config['companyScore']['pillars']['Budget']['weight']
    demand_weight = config['companyScore']['pillars']['Demand']['weight']

    # ALIGNMENT PILLAR
    logging.info("Calculating Alignment pillar components...")
    dev_scores = []
    for _, row in df.iterrows():
        if str(row.get('Type', '')).strip().lower() == 'co-developer':
            dev_scores.append(0)
        else:
            dev_scores.append(score_binary_flag(row.get('Makes Games'), 10))

    f2p_scores = [score_binary_flag(row.get('F2P'), 8) for _, row in df.iterrows()]
    mobile_scores = [score_binary_flag(row.get('Mobile'), 7) for _, row in df.iterrows()]

    fresh_scores = []
    current_year = datetime.now().year
    for _, row in df.iterrows():
        founded_year = safe_float(row.get('Founded Year'))
        if pd.isna(founded_year):
            fresh_scores.append(0)
        else:
            years_since_founded = current_year - founded_year
            fresh_scores.append(5 if years_since_founded <= 3 else 0)

    # BUDGET PILLAR
    logging.info("Calculating Budget pillar components...")
    revenue_series = df['Rev <30D (ST)'].fillna(df.get('Annual Revenue (Growjo)', pd.Series(dtype=float)))
    revenue_scores = []
    for value in revenue_series:
        percentile = calculate_percentile_score(value, revenue_series)
        revenue_scores.append((percentile / 100) * 10)

    funding_series = df.get('Total Funding Amount', pd.Series(dtype=float))
    funding_scores = []
    for value in funding_series:
        percentile = calculate_percentile_score(value, funding_series)
        funding_scores.append((percentile / 100) * 8)

    headcount_series = df.get('Current Employee Count (GJ)', pd.Series(dtype=float))
    headcount_scores = []
    for value in headcount_series:
        percentile = calculate_percentile_score(value, headcount_series)
        headcount_scores.append((percentile / 100) * 5)

    # DEMAND PILLAR
    logging.info("Calculating Demand pillar components...")
    status_scores = []
    for _, row in df.iterrows():
        score = calculate_status_score(
            row.get('Close Status'),
            row.get('Close Status Change Dt'),
            config
        )
        status_scores.append(score)

    volatility_data = calculate_volatility_components(df)
    volatility_scores = []
    for i in range(len(df)):
        weighted_score = (
            volatility_data['revenue_change_scores'][i] * 5 +
            volatility_data['runway_scores'][i] * 4 +
            volatility_data['headcount_change_scores'][i] * 3
        ) / 12
        volatility_scores.append((weighted_score / 100) * 7)

    hiring_scores = [0] * len(df)

    # NORMALIZE SUBCOMPONENTS
    logging.info("Normalizing subcomponent scores to 0-100...")
    dev_normalized = normalize_scores_0_100(dev_scores)
    f2p_normalized = normalize_scores_0_100(f2p_scores)
    mobile_normalized = normalize_scores_0_100(mobile_scores)
    fresh_normalized = normalize_scores_0_100(fresh_scores)
    revenue_normalized = normalize_scores_0_100(revenue_scores)
    funding_normalized = normalize_scores_0_100(funding_scores)
    headcount_normalized = normalize_scores_0_100(headcount_scores)
    status_normalized = normalize_scores_0_100(status_scores)
    volatility_normalized = normalize_scores_0_100(volatility_scores)
    revenue_delta_normalized = normalize_scores_0_100(volatility_data['revenue_change_scores'])
    runway_delta_normalized = normalize_scores_0_100(volatility_data['runway_scores'])
    headcount_delta_normalized = normalize_scores_0_100(volatility_data['headcount_change_scores'])
    hiring_normalized = normalize_scores_0_100(hiring_scores)

    # RAW PILLAR SCORES
    logging.info("Calculating pillar scores...")
    alignment_raw = [dev + f2p + mobile + fresh for dev, f2p, mobile, fresh in
                     zip(dev_scores, f2p_scores, mobile_scores, fresh_scores)]
    budget_raw = [rev + fund + head for rev, fund, head in
                  zip(revenue_scores, funding_scores, headcount_scores)]
    demand_raw = [status + vol + hiring for status, vol, hiring in
                  zip(status_scores, volatility_scores, hiring_scores)]

    alignment_pillar = normalize_pillar(alignment_raw)
    budget_pillar = normalize_pillar(budget_raw)
    demand_pillar = normalize_pillar(demand_raw)

    # FINAL COMPANY SCORE
    logging.info("Calculating final Company Scores...")
    total_weight = alignment_weight + budget_weight + demand_weight
    company_scores_raw = [
        (align * alignment_weight + budget * budget_weight + demand * demand_weight) / total_weight
        for align, budget, demand in zip(alignment_pillar, budget_pillar, demand_pillar)
    ]
    final_company_scores = normalize_pillar(company_scores_raw)

    # BUILD OUTPUT
    logging.info("Building output dataset...")
    output_df = pd.DataFrame()
    output_df['Company Name'] = result_df['Company Name']
    output_df['Company Score'] = final_company_scores
    output_df['Alignment'] = alignment_pillar
    output_df['Budget'] = budget_pillar
    output_df['Demand'] = demand_pillar
    output_df['Data Quality'] = np.nan
    output_df['Dev'] = dev_normalized
    output_df['F2P'] = f2p_normalized
    output_df['Mobile'] = mobile_normalized
    output_df['Fresh'] = fresh_normalized
    output_df['Revenue'] = revenue_normalized
    output_df['Funding'] = funding_normalized
    output_df['Headcount'] = headcount_normalized
    output_df['Status'] = status_normalized
    output_df['Volatility'] = volatility_normalized
    output_df['Revenue ∆'] = revenue_delta_normalized
    output_df['Runway ∆'] = runway_delta_normalized
    output_df['Headcount ∆'] = headcount_delta_normalized
    output_df['Hiring'] = hiring_normalized
    output_df['URL'] = [get_company_url(row) for _, row in result_df.iterrows()]
    output_df['Country'] = result_df.get('Country', '')
    output_df['FLAG'] = result_df.get('FLAG', '')
    output_df['Notes'] = result_df.get('Notes', '')
    output_df['Discover Source'] = result_df.get('Discover Source', '')
    output_df['Created Date'] = result_df.get('Created Date', '')
    output_df['Updated Date'] = datetime.now().strftime('%Y-%m-%d')
    output_df['Normalized Name'] = result_df.get('Normalized Name', '')

    logging.info("Output dataset complete!")
    return output_df


def main():
    """Main company scoring workflow."""
    start_time = datetime.now()

    logging.info("=" * 70)
    logging.info("COMPANY SCORING")
    logging.info("=" * 70)

    input_file = _REPO_ROOT / 'sources' / 'COMPANY_STAGING.tsv'
    output_file = _REPO_ROOT / 'output' / 'COMPANY_SCORES.csv'

    logging.info("Loading configuration and data...")
    config = load_config()
    df = pd.read_csv(input_file, sep='\t', low_memory=False)

    logging.info(f"Loaded {len(df):,} companies for scoring")

    scored_df = score_companies(df, config)
    scored_df = scored_df.sort_values('Company Score', ascending=False)

    logging.info("Saving scored companies...")
    scored_df.to_csv(output_file, index=False)

    end_time = datetime.now()
    duration = end_time - start_time

    print(f"\nCOMPANY SCORING COMPLETE")
    print(f"Processing time: {duration}")
    print(f"Companies scored: {len(scored_df):,}")
    print(f"Highest score: {scored_df['Company Score'].max():.1f}")
    print(f"Average score: {scored_df['Company Score'].mean():.1f}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()
