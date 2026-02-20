"""
Build and maintain the master people list by aggregating all scored people files.

Migrated from build_master_people_list.py. Scans output/ and store/ for scored
people files, deduplicates by (name, title, company), keeps newest per event.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

_SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = _SCRIPT_DIR.parent
OUTPUT_DIR = _REPO_ROOT / "output"
STORE_DIR = _REPO_ROOT / "store"
SOURCES_DIR = _REPO_ROOT / "sources"

MASTER_LIST_PATH = STORE_DIR / "people.csv"
MASTER_STATS_PATH = STORE_DIR / "baselines" / "MASTER_PEOPLE_STATS.json"

TARGET_COLUMNS = [
    "First Name", "Last Name", "Full Name", "Job Title", "Company Name",
    "Lead Score", "Contact Score", "Company Score", "Seniority", "Domain", "Warmth",
    "Matched Company", "Match Confidence", "Source", "Date Created", "Date Updated",
    "Score Version", "Source List", "Master Added At", "Extra Data",
]

EXCLUDED_SOURCE_LISTS = {
    "output/Scored_People(M2M).csv",
}

NAME_ACRONYMS = ["GDC", "DICE", "PGC"]


def _clean_name_acronyms(value: str) -> str:
    if value is None:
        return ""
    text = str(value)
    pattern = r"\b(" + "|".join(NAME_ACRONYMS) + r")\b"
    text = re.sub(pattern, " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_date_from_filename(filename: str) -> Optional[datetime]:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d")
    except ValueError:
        return None


def _parse_version_from_filename(filename: str) -> int:
    match = re.search(r"v(\d+)", filename, re.IGNORECASE)
    if not match:
        return 0
    try:
        return int(match.group(1))
    except ValueError:
        return 0


def _normalize_event_key(filename: str) -> str:
    base = os.path.splitext(filename)[0]
    base = re.sub(r"people_scores", "", base, flags=re.IGNORECASE)
    base = re.sub(r"scored_people", "", base, flags=re.IGNORECASE)
    base = re.sub(r"scored people", "", base, flags=re.IGNORECASE)
    base = re.sub(r"people scores", "", base, flags=re.IGNORECASE)
    base = re.sub(r"accum output", "", base, flags=re.IGNORECASE)
    base = re.sub(r"\bscored\b", "", base, flags=re.IGNORECASE)
    base = re.sub(r"\bpeople\b", "", base, flags=re.IGNORECASE)
    base = re.sub(r"\d{4}-\d{2}-\d{2}", "", base)
    base = re.sub(r"v\d+", "", base, flags=re.IGNORECASE)
    base = re.sub(r"[_\-\(\)\[\]']+", " ", base)
    base = re.sub(r"\s+", " ", base).strip()
    base = re.sub(r"[^A-Za-z0-9 ]+", " ", base)
    base = re.sub(r"\s+", " ", base).strip()
    if not base:
        return "GENERAL"
    return base.upper().replace(" ", "_")


def _is_scored_people_file(filename: str) -> bool:
    lowered = filename.lower()
    if not (lowered.endswith(".csv") or lowered.endswith(".tsv")):
        return False
    if "company_scores" in lowered or "people_company_matches" in lowered:
        return False
    return True


def _list_candidate_files() -> List[str]:
    candidates = []
    for directory in [str(OUTPUT_DIR), str(STORE_DIR), str(SOURCES_DIR)]:
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            if _is_scored_people_file(name):
                candidates.append(os.path.join(directory, name))
    return candidates


def _select_latest_per_event(files: List[str]) -> Dict[str, str]:
    by_event: Dict[str, List[Tuple[Tuple, str]]] = {}
    for path in files:
        filename = os.path.basename(path)
        event_key = _normalize_event_key(filename)
        date = _parse_date_from_filename(filename) or datetime.min
        version = _parse_version_from_filename(filename)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
        except OSError:
            mtime = datetime.min
        sort_key = (date, version, mtime)
        by_event.setdefault(event_key, []).append((sort_key, path))

    latest = {}
    for event_key, entries in by_event.items():
        entries.sort(key=lambda item: item[0], reverse=True)
        latest[event_key] = entries[0][1]
    return latest


def _read_people_file(path: str) -> pd.DataFrame:
    sep = "\t" if path.lower().endswith(".tsv") else ","
    return pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)


def _get_col(df: pd.DataFrame, *names: str) -> Optional[str]:
    lower_map = {c.lower(): c for c in df.columns}
    for name in names:
        key = name.lower()
        if key in lower_map:
            return lower_map[key]
    return None


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _scale_if_multiplier(series: pd.Series) -> pd.Series:
    numeric = _to_number(series)
    if numeric.dropna().empty:
        return numeric
    max_value = numeric.dropna().max()
    if max_value <= 1.0:
        return numeric * 100.0
    return numeric


def _map_to_target(df: pd.DataFrame, source_path: str) -> pd.DataFrame:
    first_col = _get_col(df, "First Name", "First")
    last_col = _get_col(df, "Last Name", "Last")
    full_col = _get_col(df, "Full Name", "Name")
    title_col = _get_col(df, "Job Title", "Title")
    company_col = _get_col(df, "Company Name", "Company", "Original Company")
    extra_col = _get_col(df, "Extra Data")
    lead_col = _get_col(df, "Lead Score", "Total Score")
    contact_col = _get_col(df, "Contact Score", "Job Score", "Title Score", "Normalized Role Score")
    company_score_col = _get_col(df, "Company Score", "Normalized Company Score")
    seniority_col = _get_col(df, "Seniority", "Seniority Multiplier", "Seniority Multi")
    domain_col = _get_col(df, "Domain", "Domain Score", "Domain Multi")
    warmth_col = _get_col(df, "Warmth")
    matched_company_col = _get_col(df, "Matched Company")
    match_conf_col = _get_col(df, "Match Confidence")
    source_col = _get_col(df, "Source")
    date_created_col = _get_col(df, "Date Created", "Date Added")
    date_updated_col = _get_col(df, "Date Updated")

    mapped = pd.DataFrame()
    mapped["First Name"] = df[first_col] if first_col else ""
    mapped["Last Name"] = df[last_col] if last_col else ""
    if full_col:
        mapped["Full Name"] = df[full_col]
    else:
        mapped["Full Name"] = (mapped["First Name"].astype(str).str.strip() + " " + mapped["Last Name"].astype(str).str.strip()).str.strip()

    mapped["First Name"] = mapped["First Name"].apply(_clean_name_acronyms)
    mapped["Last Name"] = mapped["Last Name"].apply(_clean_name_acronyms)
    mapped["Full Name"] = mapped["Full Name"].apply(_clean_name_acronyms)
    mapped["Job Title"] = df[title_col] if title_col else ""
    mapped["Company Name"] = df[company_col] if company_col else ""
    mapped["Extra Data"] = df[extra_col] if extra_col else ""
    mapped["Lead Score"] = _to_number(df[lead_col]) if lead_col else pd.Series(dtype=float)
    mapped["Contact Score"] = _to_number(df[contact_col]) if contact_col else pd.Series(dtype=float)
    mapped["Company Score"] = _to_number(df[company_score_col]) if company_score_col else pd.Series(dtype=float)
    mapped["Seniority"] = _scale_if_multiplier(df[seniority_col]) if seniority_col else pd.Series(dtype=float)
    mapped["Domain"] = _scale_if_multiplier(df[domain_col]) if domain_col else pd.Series(dtype=float)
    mapped["Warmth"] = _to_number(df[warmth_col]) if warmth_col else pd.Series(dtype=float)
    mapped["Matched Company"] = df[matched_company_col] if matched_company_col else ""
    mapped["Match Confidence"] = _to_number(df[match_conf_col]) if match_conf_col else pd.Series(dtype=float)
    mapped["Source"] = df[source_col] if source_col else ""
    mapped["Date Created"] = df[date_created_col] if date_created_col else ""
    mapped["Date Updated"] = df[date_updated_col] if date_updated_col else ""

    version = _parse_version_from_filename(os.path.basename(source_path))
    mapped["Score Version"] = f"v{version}" if version > 0 else "unknown"
    mapped["Source List"] = os.path.relpath(source_path, str(_REPO_ROOT))
    mapped["Master Added At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return mapped


def _normalize_key(value: str) -> str:
    if value is None:
        return ""
    value = str(value).lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _dedupe_master(df: pd.DataFrame, file_dates: Dict[str, Optional[datetime]]) -> pd.DataFrame:
    df = df.copy()
    df["__dedupe_key"] = (
        df["Full Name"].apply(_normalize_key)
        + "|"
        + df["Job Title"].apply(_normalize_key)
        + "|"
        + df["Company Name"].apply(_normalize_key)
    )

    updated = pd.to_datetime(df["Date Updated"], errors="coerce")
    created = pd.to_datetime(df["Date Created"], errors="coerce")
    fallback_dates = df["Source List"].map(lambda path: file_dates.get(path))
    fallback_parsed = pd.to_datetime(fallback_dates, errors="coerce")
    df["__dedupe_date"] = updated.fillna(created).fillna(fallback_parsed)

    df = df.sort_values(by="__dedupe_date", ascending=False)
    df = df.drop_duplicates(subset="__dedupe_key", keep="first")
    df = df.drop(columns=["__dedupe_key", "__dedupe_date"])
    return df


def build_master_people_list() -> None:
    """Build or rebuild the master people list from all scored files."""
    candidates = _list_candidate_files()
    selected = _select_latest_per_event(candidates)

    if not selected:
        raise RuntimeError("No scored people lists found to build master list.")

    mapped_frames = []
    file_dates: Dict[str, Optional[datetime]] = {}

    for event_key, path in selected.items():
        try:
            df = _read_people_file(path)
        except Exception:
            continue

        lower_cols = [c.lower() for c in df.columns]
        if not any(col in lower_cols for col in ["lead score", "total score", "contact score", "job score"]):
            continue

        mapped = _map_to_target(df, path)
        mapped_frames.append(mapped)

        filename_date = _parse_date_from_filename(os.path.basename(path))
        file_dates[os.path.relpath(path, str(_REPO_ROOT))] = filename_date

    if not mapped_frames:
        raise RuntimeError("No scored people lists matched the required schema.")

    master_df = pd.concat(mapped_frames, ignore_index=True)
    master_df = master_df[~master_df["Source List"].isin(EXCLUDED_SOURCE_LISTS)]
    master_df = master_df.reindex(columns=TARGET_COLUMNS)
    master_df = _dedupe_master(master_df, file_dates)

    os.makedirs(str(STORE_DIR), exist_ok=True)
    master_df.to_csv(str(MASTER_LIST_PATH), index=False)

    os.makedirs(str(MASTER_STATS_PATH.parent), exist_ok=True)
    stats = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lead_score_min": float(pd.to_numeric(master_df["Lead Score"], errors="coerce").min()),
        "lead_score_max": float(pd.to_numeric(master_df["Lead Score"], errors="coerce").max()),
        "contact_score_min": float(pd.to_numeric(master_df["Contact Score"], errors="coerce").min()),
        "contact_score_max": float(pd.to_numeric(master_df["Contact Score"], errors="coerce").max()),
        "source_lists": sorted(set(master_df["Source List"].dropna().astype(str).tolist())),
    }
    with open(str(MASTER_STATS_PATH), "w", encoding="utf-8") as handle:
        json.dump(stats, handle, indent=2)

    print(f"Master list saved to {MASTER_LIST_PATH}")
    print(f"Master stats saved to {MASTER_STATS_PATH}")


if __name__ == "__main__":
    build_master_people_list()
