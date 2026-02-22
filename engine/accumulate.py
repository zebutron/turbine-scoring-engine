"""
Accumulate conference attendee sources across scrape iterations.

The conference attendee pipeline works iteratively:
  - LISN export v1  → Accum
  - MTM Scrape 1    → Accum
  - MTM Scrape 2    → Accum (new people added, existing updated)
  - MTM Scrape 3    → Accum (new people added, existing updated)
  - LISN export v2  → Accum (new people added, existing updated)

"Accum Output" is the accumulated, deduplicated list of ALL people seen
across ALL scrapes for a conference. It's the input to the scorer.

Key rules:
  1. ACCUMULATE, don't replace. Every prior person stays unless manually removed.
  2. Dedup by First Name + Last Name + Company (normalized).
  3. When a person appears in multiple scrapes, keep the NEWEST version
     (freshest title, freshest Extra Data).
  4. Source tracking: preserve which scrape(s) each person came from.

Usage:
    from engine.accumulate import accumulate_sources

    # Start fresh or load prior accum
    accum = load_accum("gdc_sf_26")

    # Add a new scrape
    accum = add_source(accum, new_scrape_df, source_label="MTM Scrape 3")

    # Save
    save_accum(accum, "gdc_sf_26")

    # The accum file is what the scorer reads as input
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

_SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = _SCRIPT_DIR.parent
SOURCES_DIR = _REPO_ROOT / "sources"
ACCUM_DIR = _REPO_ROOT / "sources" / "accum"

# Standard columns for accumulated people
ACCUM_COLUMNS = [
    "First Name",
    "Last Name",
    "Job Title",
    "Company",
    "Source",
    "Extra Data",
    "First Seen",     # date first added to accum
    "Last Updated",   # date of most recent scrape containing this person
]


def _person_key(row: pd.Series) -> str:
    """Dedup key: first + last + company, normalized."""
    first = str(row.get("First Name", "")).strip().lower()
    last = str(row.get("Last Name", "")).strip().lower()
    company = str(row.get("Company", row.get("Company Name", ""))).strip().lower()
    return f"{first}|{last}|{company}"


def load_accum(conference: str) -> pd.DataFrame:
    """Load the accumulated people list for a conference.

    Returns empty DataFrame with correct columns if no accum exists yet.
    """
    os.makedirs(str(ACCUM_DIR), exist_ok=True)
    path = ACCUM_DIR / f"{conference}_accum.tsv"
    if path.exists():
        df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
        print(f"Loaded accum: {len(df)} people from {path.name}")
        return df
    else:
        print(f"No existing accum for {conference}. Starting fresh.")
        return pd.DataFrame(columns=ACCUM_COLUMNS)


def add_source(
    accum: pd.DataFrame,
    new_data: pd.DataFrame,
    source_label: str,
    date: Optional[str] = None,
) -> pd.DataFrame:
    """Add a new scrape/export to the accumulated list.

    Args:
        accum: Current accumulated DataFrame.
        new_data: New scrape data. Must have at minimum: First Name, Last Name.
                  Optional: Job Title, Company (or Company Name), Source, Extra Data.
        source_label: Human label for this source (e.g. "MTM Scrape 3", "LISN v1").
        date: Date string for this addition. Defaults to today.

    Returns:
        Updated accumulated DataFrame with new people added and existing updated.
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Normalize new_data columns
    new = new_data.copy()
    if "Company Name" in new.columns and "Company" not in new.columns:
        new["Company"] = new["Company Name"]

    # Ensure required columns exist
    for col in ["First Name", "Last Name"]:
        if col not in new.columns:
            raise ValueError(f"New data missing required column: {col}")
    for col in ["Job Title", "Company", "Source", "Extra Data"]:
        if col not in new.columns:
            new[col] = ""

    # Override Source with the provided label if Source column is empty or generic
    if source_label:
        new["Source"] = source_label

    # Build lookup of existing accum by person key
    existing_keys = {}
    if len(accum) > 0:
        accum = accum.copy()
        if "_key" not in accum.columns:
            accum["_key"] = accum.apply(_person_key, axis=1)
        for idx, row in accum.iterrows():
            existing_keys[row["_key"]] = idx

    # Process new rows
    new["_key"] = new.apply(_person_key, axis=1)
    added = 0
    updated = 0
    skipped_empty = 0

    for _, new_row in new.iterrows():
        key = new_row["_key"]

        # Skip rows with no name
        if not str(new_row.get("First Name", "")).strip() and not str(new_row.get("Last Name", "")).strip():
            skipped_empty += 1
            continue

        if key in existing_keys:
            # Person exists — update with newer data (keep richer version)
            idx = existing_keys[key]
            old_row = accum.loc[idx]

            # Update fields if new version has data
            for field in ["Job Title", "Company", "Extra Data"]:
                new_val = str(new_row.get(field, "")).strip()
                old_val = str(old_row.get(field, "")).strip()
                if new_val and (not old_val or len(new_val) > len(old_val)):
                    accum.at[idx, field] = new_val

            # Append source if not already tracked
            old_source = str(old_row.get("Source", ""))
            if source_label and source_label not in old_source:
                accum.at[idx, "Source"] = f"{old_source} + {source_label}" if old_source else source_label

            accum.at[idx, "Last Updated"] = date
            updated += 1
        else:
            # New person — add to accum
            new_entry = {
                "First Name": new_row.get("First Name", ""),
                "Last Name": new_row.get("Last Name", ""),
                "Job Title": new_row.get("Job Title", ""),
                "Company": new_row.get("Company", ""),
                "Source": source_label,
                "Extra Data": new_row.get("Extra Data", ""),
                "First Seen": date,
                "Last Updated": date,
                "_key": key,
            }
            accum = pd.concat([accum, pd.DataFrame([new_entry])], ignore_index=True)
            existing_keys[key] = len(accum) - 1
            added += 1

    print(f"\n  Source: {source_label}")
    print(f"  Input rows: {len(new)}")
    print(f"  New people added: {added}")
    print(f"  Existing people updated: {updated}")
    print(f"  Skipped (empty name): {skipped_empty}")
    print(f"  Accum total: {len(accum)}")

    return accum


def save_accum(accum: pd.DataFrame, conference: str) -> Path:
    """Save the accumulated list. This becomes the scorer's input."""
    os.makedirs(str(ACCUM_DIR), exist_ok=True)

    # Drop internal key column before saving
    save_df = accum.drop(columns=["_key"], errors="ignore")

    path = ACCUM_DIR / f"{conference}_accum.tsv"
    save_df.to_csv(path, sep="\t", index=False)
    print(f"\nSaved accum: {len(save_df)} people → {path}")
    return path


def accum_summary(accum: pd.DataFrame) -> str:
    """Print a summary of what's in the accumulated list."""
    lines = []
    lines.append(f"Total people: {len(accum)}")

    # Source breakdown
    if "Source" in accum.columns:
        # Sources can be compound ("LISN v1 + MTM Scrape 3")
        all_sources = []
        for s in accum["Source"]:
            for part in str(s).split(" + "):
                part = part.strip()
                if part:
                    all_sources.append(part)
        from collections import Counter
        source_counts = Counter(all_sources)
        lines.append("Sources contributing:")
        for src, count in source_counts.most_common():
            lines.append(f"  {src}: {count} people")

    # Data quality
    has_title = (accum["Job Title"].astype(str).str.strip() != "").sum()
    has_company = (accum["Company"].astype(str).str.strip() != "").sum()
    lines.append(f"With Job Title: {has_title} ({has_title/len(accum)*100:.0f}%)")
    lines.append(f"With Company: {has_company} ({has_company/len(accum)*100:.0f}%)")

    return "\n".join(lines)


def ingest_sheet_export(
    filepath: str,
    conference: str,
    source_label: str = "Sheet export",
    date: Optional[str] = None,
) -> pd.DataFrame:
    """Ingest a TSV/CSV exported from a Google Sheet tab into the accum.

    This handles re-ingesting Katz's annotated Scored People tab back into
    the pipeline. It extracts the people data (ignoring score columns that
    will be recomputed) and the DK annotation columns.

    Args:
        filepath: Path to exported TSV or CSV.
        conference: Conference key.
        source_label: Label for this data source.
        date: Date of ingest.

    Returns:
        Updated accumulated DataFrame.
    """
    # Detect format
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath, dtype=str, keep_default_na=False)
    else:
        df = pd.read_csv(filepath, sep="\t", dtype=str, keep_default_na=False)

    print(f"Ingesting sheet export: {filepath}")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {list(df.columns)}")

    # Map common column name variants
    col_map = {
        "Company Name": "Company",
        "Full Name": None,  # skip — we have First/Last
    }
    for old, new in col_map.items():
        if old in df.columns:
            if new:
                df[new] = df[old]

    # Load existing accum and add
    accum = load_accum(conference)
    accum = add_source(accum, df, source_label=source_label, date=date)
    save_accum(accum, conference)

    return accum
