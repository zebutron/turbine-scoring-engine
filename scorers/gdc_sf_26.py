"""
GDC San Francisco '26 — Conference People Scorer

Reads from the accumulated attendee list (sources/accum/gdc_sf_26_accum.tsv),
scores against company store, outputs prioritized lead list.

Workflow:
    1. Human provides source files (LISN export, MTM scrape) into sources/
    2. Run: python -m engine.accumulate to add them to the accum
       (or they're added programmatically)
    3. Run: python -m scorers.gdc_sf_26 to score the full accum
    4. Output lands in output/ as a TSV sorted by Lead Score

Usage:
    python -m scorers.gdc_sf_26
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Ensure repo root is on path for engine imports
_SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_REPO_ROOT))

from engine.people import process_people_scoring, load_config


# ===== CONFERENCE CONFIG =====
CONFERENCE_KEY = "gdc_sf_26"
VERSION_LABEL = "v3 (accumulated)"  # UPDATE THIS each scoring run
# =============================


def main():
    """Score GDC San Francisco '26 attendees from accumulated list."""

    # Input: the accumulated attendee list (built by engine.accumulate)
    input_file = _REPO_ROOT / 'sources' / 'accum' / f'{CONFERENCE_KEY}_accum.tsv'
    companies_file = _REPO_ROOT / 'store' / 'companies.csv'
    current_date = datetime.now().strftime('%Y-%m-%d')
    output_file = _REPO_ROOT / 'output' / f'GDC_SAN_FRANCISCO_26_Scored_People_{current_date}.tsv'

    if not input_file.exists():
        print(f"ERROR: No accumulated input found at {input_file}")
        print(f"Run accumulation first: add source files, then save the accum.")
        print(f"See engine/accumulate.py for usage.")
        sys.exit(1)

    print("Processing GDC San Francisco '26 people scoring...")
    print(f"Input (accum): {input_file}")
    print(f"Companies: {companies_file}")
    print(f"Output: {output_file}")

    # Read the accumulated input
    print("\nPreprocessing input file...")
    people_df = pd.read_csv(input_file, sep='\t', dtype=str, keep_default_na=False)

    print(f"Loaded {len(people_df)} people from accumulated list")
    print(f"Columns: {list(people_df.columns)}")

    # Create staging format with required columns
    staging_df = pd.DataFrame({
        'First Name': people_df['First Name'],
        'Last Name': people_df['Last Name'],
        'Job Title': people_df['Job Title'],
        'Company Name': people_df['Company'],
        'Source': people_df['Source'],
        'Extra Data': people_df['Extra Data'] if 'Extra Data' in people_df.columns else ''
    })

    # Save staging file temporarily
    temp_dir = _REPO_ROOT / 'output'
    os.makedirs(temp_dir, exist_ok=True)
    temp_staging_file = temp_dir / 'PEOPLE_STAGING_GDC_SF_26_temp.tsv'
    staging_df.to_csv(temp_staging_file, sep='\t', index=False)
    print(f"Created staging file with {len(staging_df)} people")

    # Preprocess companies file — map 'Normalized Name' -> 'Normal Company'
    print("Preprocessing companies file...")
    companies_df = pd.read_csv(companies_file)

    if 'Normalized Name' in companies_df.columns and 'Normal Company' not in companies_df.columns:
        companies_df['Normal Company'] = companies_df['Normalized Name']
        print("Mapped 'Normalized Name' -> 'Normal Company'")

    temp_companies_file = temp_dir / 'COMPANY_SCORES_temp.csv'
    companies_df.to_csv(temp_companies_file, index=False)

    # Load config and score
    print("\nLoading latest scoring configuration...")
    config = load_config()

    results_df = process_people_scoring(str(temp_staging_file), str(temp_companies_file), config)

    # Reorder columns
    column_order = [
        'First Name', 'Last Name', 'Full Name', 'Job Title', 'Company Name',
        'Lead Score', 'Contact Score', 'Company Score', 'Seniority', 'Domain', 'Warmth',
        'Matched Company', 'Match Confidence', 'Source', 'Date Created', 'Date Updated',
        'Extra Data'
    ]
    results_df = results_df[column_order]

    # Save results as TSV
    os.makedirs(output_file.parent, exist_ok=True)
    results_df.to_csv(output_file, sep='\t', index=False)

    # Clean up temp files
    os.remove(temp_staging_file)
    os.remove(temp_companies_file)
    print("Cleaned up temporary files")

    # Summary
    total_people = len(results_df)
    matched_people = len(results_df[results_df['Match Confidence'] != ''])
    avg_lead_score = results_df['Lead Score'].mean()

    print("\n=== SCORING SUMMARY ===")
    print(f"Total people processed: {total_people}")
    print(f"Successfully matched to companies: {matched_people} ({matched_people/total_people*100:.1f}%)")
    print(f"Average Lead Score: {avg_lead_score:.1f} (normalized)")

    if matched_people > 0:
        avg_match_confidence = results_df[results_df['Match Confidence'] != '']['Match Confidence'].astype(float).mean()
        print(f"Average match confidence: {avg_match_confidence:.1f}%")

    contact_score_range = f"{results_df['Contact Score'].min()}-{results_df['Contact Score'].max()}"
    lead_score_range = f"{results_df['Lead Score'].min()}-{results_df['Lead Score'].max()}"
    print(f"Contact Score range: {contact_score_range}")
    print(f"Lead Score range: {lead_score_range}")

    print(f"\nResults saved to: {output_file}")

    # Record velocity tracking
    from engine.velocity import record_iteration, format_velocity_report

    record_iteration(CONFERENCE_KEY, results_df, VERSION_LABEL)
    print("\n" + format_velocity_report(CONFERENCE_KEY, format="text"))


if __name__ == "__main__":
    main()
