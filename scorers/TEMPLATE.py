"""
[CONFERENCE NAME] — Conference People Scorer

Copy this file for each new conference. Change the 4 config lines below.

Usage:
    python -m scorers.[filename]
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

_SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_REPO_ROOT))

from engine.people import process_people_scoring, load_config


def main():
    """Score [CONFERENCE NAME] attendees."""

    # ===== CONFIGURE THESE 4 THINGS =====
    input_file = _REPO_ROOT / 'sources' / "YOUR_CONFERENCE_INPUT.tsv"         # Input attendee file
    companies_file = _REPO_ROOT / 'store' / 'companies.csv'                    # Company store (usually don't change)
    current_date = datetime.now().strftime('%Y-%m-%d')
    output_file = _REPO_ROOT / 'output' / f'YOUR_CONFERENCE_Scored_People_{current_date}.tsv'
    # ===== END CONFIG =====

    # Column mapping — adjust if your input has different column names
    INPUT_FIRST_NAME = 'First Name'
    INPUT_LAST_NAME = 'Last Name'
    INPUT_JOB_TITLE = 'Job Title'
    INPUT_COMPANY = 'Company'        # Some inputs use 'Company Name' instead
    INPUT_SOURCE = 'Source'
    INPUT_EXTRA = 'Extra Data'       # Optional — set to None if not present

    print(f"Processing conference scoring...")
    print(f"Input: {input_file}")
    print(f"Companies: {companies_file}")
    print(f"Output: {output_file}")

    # Read input
    input_sep = '\t' if str(input_file).endswith('.tsv') else ','
    people_df = pd.read_csv(input_file, sep=input_sep)
    print(f"Loaded {len(people_df)} people from input file")

    # Create staging format
    staging_df = pd.DataFrame({
        'First Name': people_df[INPUT_FIRST_NAME],
        'Last Name': people_df[INPUT_LAST_NAME],
        'Job Title': people_df[INPUT_JOB_TITLE],
        'Company Name': people_df[INPUT_COMPANY],
        'Source': people_df[INPUT_SOURCE] if INPUT_SOURCE in people_df.columns else '',
        'Extra Data': people_df[INPUT_EXTRA] if INPUT_EXTRA and INPUT_EXTRA in people_df.columns else ''
    })

    # Save temp staging
    temp_dir = _REPO_ROOT / 'output'
    os.makedirs(temp_dir, exist_ok=True)
    temp_staging = temp_dir / 'STAGING_temp.tsv'
    staging_df.to_csv(temp_staging, sep='\t', index=False)

    # Preprocess companies
    companies_df = pd.read_csv(companies_file)
    if 'Normalized Name' in companies_df.columns and 'Normal Company' not in companies_df.columns:
        companies_df['Normal Company'] = companies_df['Normalized Name']
    temp_companies = temp_dir / 'COMPANIES_temp.csv'
    companies_df.to_csv(temp_companies, index=False)

    # Score
    config = load_config()
    results_df = process_people_scoring(str(temp_staging), str(temp_companies), config)

    column_order = [
        'First Name', 'Last Name', 'Full Name', 'Job Title', 'Company Name',
        'Lead Score', 'Contact Score', 'Company Score', 'Seniority', 'Domain', 'Warmth',
        'Matched Company', 'Match Confidence', 'Source', 'Date Created', 'Date Updated',
        'Extra Data'
    ]
    results_df = results_df[column_order]

    # Save
    os.makedirs(output_file.parent, exist_ok=True)
    results_df.to_csv(output_file, sep='\t', index=False)

    # Cleanup
    os.remove(temp_staging)
    os.remove(temp_companies)

    # Summary
    total = len(results_df)
    matched = len(results_df[results_df['Match Confidence'] != ''])
    print(f"\n=== SCORING SUMMARY ===")
    print(f"Total: {total} | Matched: {matched} ({matched/total*100:.1f}%)")
    print(f"Avg Lead Score: {results_df['Lead Score'].mean():.1f}")
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
