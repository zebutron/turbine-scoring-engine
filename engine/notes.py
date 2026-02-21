"""
DK Notes Persistence — Carry Katz's per-lead annotations across scoring iterations.

Katz annotates scored people in Google Sheets with 4 columns:
  - DK: title too low (1) or too high (0)  — scoring feedback
  - DK Score (0-2)                         — manual quality rating
  - DK notes                               — free-text (scoring bugs, lead context)
  - DK status                              — BD workflow status (LIDM, Skipped, DK email, etc.)

These annotations are both:
  1. Scoring feedback (engine improvements) — should be captured in the repo
  2. BD operational state (outreach progress) — must persist across iterations

This module handles merging prior-iteration notes into new scored output so
Katz never loses track of where he is with each lead.

Usage:
    from engine.notes import merge_dk_notes

    # new_scored: DataFrame from scoring engine output
    # prior_notes: DataFrame exported from prior Scored People tab (or notes CSV)
    merged = merge_dk_notes(new_scored, prior_notes)
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

_SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = _SCRIPT_DIR.parent
NOTES_DIR = _REPO_ROOT / "store" / "notes"

# Katz's annotation columns — order matters for Sheet layout
DK_COLUMNS = [
    "DK: title too low (1) or too high (0)",
    "DK Score (0-2)",
    "DK notes",
    "DK status",
]

# Match key: how we identify the same person across iterations
# Using Full Name + Company Name — same logic as master list dedup
def _match_key(row: pd.Series) -> str:
    """Generate a stable match key for a person row."""
    name = str(row.get("Full Name", "")).strip().lower()
    company = str(row.get("Company Name", "")).strip().lower()
    return f"{name}|{company}"


def merge_dk_notes(
    new_scored: pd.DataFrame,
    prior_notes: pd.DataFrame,
    fill_missing: bool = True,
) -> pd.DataFrame:
    """Merge DK annotations from a prior iteration into new scored output.

    Args:
        new_scored: New scoring output (from scoring engine).
        prior_notes: Prior iteration's scored people WITH DK columns
                     (exported from Google Sheet or from store/notes/).
        fill_missing: If True, add empty DK columns for people without prior notes.

    Returns:
        new_scored with DK columns merged in. People who existed in prior
        iteration keep their notes. New people get empty DK columns.
    """
    result = new_scored.copy()

    # Check which DK columns exist in prior notes
    available_dk_cols = [c for c in DK_COLUMNS if c in prior_notes.columns]
    if not available_dk_cols:
        print(f"Warning: No DK columns found in prior notes. "
              f"Expected: {DK_COLUMNS}")
        if fill_missing:
            for col in DK_COLUMNS:
                result[col] = ""
        return result

    # Build lookup from prior notes: match_key -> DK values
    prior_notes["_match_key"] = prior_notes.apply(_match_key, axis=1)
    dk_lookup = {}
    for _, row in prior_notes.iterrows():
        key = row["_match_key"]
        if key and key != "|":  # skip empty rows
            dk_lookup[key] = {col: row.get(col, "") for col in available_dk_cols}

    # Apply to new scored output
    result["_match_key"] = result.apply(_match_key, axis=1)

    matched = 0
    for col in DK_COLUMNS:
        result[col] = ""  # initialize all empty

    for idx, row in result.iterrows():
        key = row["_match_key"]
        if key in dk_lookup:
            for col in available_dk_cols:
                val = dk_lookup[key].get(col, "")
                if pd.notna(val) and str(val).strip():
                    result.at[idx, col] = val
            matched += 1

    result.drop(columns=["_match_key"], inplace=True)

    # Stats
    total_with_notes = sum(1 for _, row in prior_notes.iterrows()
                           if any(str(row.get(c, "")).strip() for c in available_dk_cols))
    print(f"\n=== DK NOTES MERGE ===")
    print(f"Prior iteration: {len(prior_notes)} people, {total_with_notes} with DK notes")
    print(f"New iteration: {len(result)} people")
    print(f"Notes carried forward: {matched} people matched")
    print(f"New people (no prior notes): {len(result) - matched}")

    return result


def save_notes_snapshot(
    scored_with_notes: pd.DataFrame,
    conference: str,
    version: str,
) -> Path:
    """Save a snapshot of DK notes to store/notes/ for recovery and tracking.

    This is the safety net: even if a Google Sheet gets corrupted, we have
    the notes in git. Also enables diffing notes across iterations.

    Args:
        scored_with_notes: Scored people with DK columns populated.
        conference: Conference key (e.g. "gdc_sf_26").
        version: Version label (e.g. "v3").

    Returns:
        Path to the saved notes CSV.
    """
    os.makedirs(str(NOTES_DIR), exist_ok=True)

    # Only save rows that have at least one DK value
    dk_cols_present = [c for c in DK_COLUMNS if c in scored_with_notes.columns]
    id_cols = ["Full Name", "Job Title", "Company Name", "Lead Score"]
    save_cols = [c for c in id_cols if c in scored_with_notes.columns] + dk_cols_present

    notes_df = scored_with_notes[save_cols].copy()
    has_notes = notes_df[dk_cols_present].apply(
        lambda row: any(str(v).strip() for v in row), axis=1
    )
    notes_only = notes_df[has_notes]

    filename = f"{conference}_{version}_dk_notes.csv"
    path = NOTES_DIR / filename
    notes_only.to_csv(path, index=False)

    print(f"Saved {len(notes_only)} annotated leads to {path}")
    return path


def load_latest_notes(conference: str) -> Optional[pd.DataFrame]:
    """Load the most recent notes snapshot for a conference.

    Scans store/notes/ for the latest version file matching the conference key.

    Returns:
        DataFrame with DK columns, or None if no prior notes exist.
    """
    if not NOTES_DIR.exists():
        return None

    # Find all note files for this conference, sorted by name (version order)
    pattern = f"{conference}_*_dk_notes.csv"
    import glob
    files = sorted(glob.glob(str(NOTES_DIR / pattern)))

    if not files:
        return None

    latest = files[-1]
    print(f"Loading prior notes from: {latest}")
    return pd.read_csv(latest, dtype=str, keep_default_na=False)


def extract_scoring_feedback(notes_df: pd.DataFrame) -> pd.DataFrame:
    """Extract rows where Katz flagged scoring issues for engine improvement.

    Looks for:
    - DK: title too low/high != blank (title scoring feedback)
    - DK Score (0-2) = 0 (bad match/score)
    - DK notes containing scoring-related keywords

    Returns:
        DataFrame of feedback rows for engine review.
    """
    feedback_rows = []

    for _, row in notes_df.iterrows():
        reasons = []
        title_flag = str(row.get("DK: title too low (1) or too high (0)", "")).strip()
        dk_score = str(row.get("DK Score (0-2)", "")).strip()
        dk_notes = str(row.get("DK notes", "")).strip()

        if title_flag in ("0", "1"):
            reasons.append(f"title_flag={title_flag}")
        if dk_score == "0":
            reasons.append("dk_score=0 (bad)")
        if dk_notes:
            # Check for scoring-related keywords
            scoring_keywords = ["score", "wrong", "should be", "too high", "too low",
                                "not f2p", "not a game", "irrelevant", "bug"]
            if any(kw in dk_notes.lower() for kw in scoring_keywords):
                reasons.append(f"note: {dk_notes[:80]}")

        if reasons:
            feedback_row = row.to_dict()
            feedback_row["_feedback_reasons"] = "; ".join(reasons)
            feedback_rows.append(feedback_row)

    if feedback_rows:
        return pd.DataFrame(feedback_rows)
    return pd.DataFrame()
