"""
Conference attendee signal velocity tracking.

Tracks iteration-over-iteration metrics for conference scoring runs:
- New people scraped per iteration
- Total list length
- Company match rate
- Lead score distribution & signal quality

Produces a velocity report (JSON + human-readable summary) that Katz and Zeb
use to assess scraping momentum and scoring signal quality before conferences.

Usage:
    python -m engine.velocity --conference gdc_sf_26
    python -m engine.velocity --conference gdc_sf_26 --format markdown
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

_SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = _SCRIPT_DIR.parent
STORE_DIR = _REPO_ROOT / "store"
OUTPUT_DIR = _REPO_ROOT / "output"
VELOCITY_DIR = STORE_DIR / "velocity"


def _load_velocity_log(conference: str) -> List[Dict]:
    """Load the velocity log for a conference, or return empty list."""
    path = VELOCITY_DIR / f"{conference}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_velocity_log(conference: str, log: List[Dict]) -> Path:
    """Save velocity log for a conference."""
    os.makedirs(str(VELOCITY_DIR), exist_ok=True)
    path = VELOCITY_DIR / f"{conference}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    return path


def compute_iteration_stats(scored_df: pd.DataFrame, version_label: str) -> Dict:
    """Compute stats for a single scoring iteration.

    Args:
        scored_df: DataFrame with scored people (TARGET_COLUMNS format)
        version_label: Human label like "v3" or "v3 (Scrape 3 + LISN)"

    Returns:
        Dict of stats for this iteration.
    """
    lead_scores = pd.to_numeric(scored_df.get("Lead Score", pd.Series(dtype=float)), errors="coerce")
    contact_scores = pd.to_numeric(scored_df.get("Contact Score", pd.Series(dtype=float)), errors="coerce")
    company_scores = pd.to_numeric(scored_df.get("Company Score", pd.Series(dtype=float)), errors="coerce")
    match_conf = pd.to_numeric(scored_df.get("Match Confidence", pd.Series(dtype=float)), errors="coerce")

    matched = scored_df.get("Matched Company", pd.Series(dtype=str))
    has_match = matched.astype(str).str.strip().ne("").sum() if matched is not None else 0

    # Source breakdown
    source_col = scored_df.get("Source", pd.Series(dtype=str))
    source_counts = source_col.value_counts().to_dict() if source_col is not None else {}

    stats = {
        "version": version_label,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_people": len(scored_df),
        "company_matched": int(has_match),
        "company_match_rate": round(has_match / len(scored_df) * 100, 1) if len(scored_df) > 0 else 0,
        "sources": {str(k): int(v) for k, v in source_counts.items()},
        "lead_score": {
            "min": float(lead_scores.min()) if not lead_scores.dropna().empty else None,
            "max": float(lead_scores.max()) if not lead_scores.dropna().empty else None,
            "mean": round(float(lead_scores.mean()), 1) if not lead_scores.dropna().empty else None,
            "median": round(float(lead_scores.median()), 1) if not lead_scores.dropna().empty else None,
            "tier_manual_90plus": int((lead_scores >= 90).sum()),
            "tier_high_60plus": int((lead_scores >= 60).sum()),
            "tier_mid_40_59": int(((lead_scores >= 40) & (lead_scores < 60)).sum()),
            "tier_auto_20_39": int(((lead_scores >= 20) & (lead_scores < 40)).sum()),
            "tier_low_10_19": int(((lead_scores >= 10) & (lead_scores < 20)).sum()),
            "tier_noise_below_10": int((lead_scores < 10).sum()),
        },
        "contact_score": {
            "mean": round(float(contact_scores.mean()), 1) if not contact_scores.dropna().empty else None,
            "median": round(float(contact_scores.median()), 1) if not contact_scores.dropna().empty else None,
        },
        "company_score": {
            "mean": round(float(company_scores.mean()), 1) if not company_scores.dropna().empty else None,
            "median": round(float(company_scores.median()), 1) if not company_scores.dropna().empty else None,
        },
    }
    return stats


def record_iteration(conference: str, scored_df: pd.DataFrame, version_label: str) -> Dict:
    """Record a scoring iteration and compute velocity deltas.

    Args:
        conference: Conference key (e.g. "gdc_sf_26")
        scored_df: Scored people DataFrame
        version_label: e.g. "v3 (Scrape 3 + LISN)"

    Returns:
        Dict with current stats + velocity deltas vs previous iteration.
    """
    log = _load_velocity_log(conference)
    current = compute_iteration_stats(scored_df, version_label)

    # Compute deltas if we have a previous iteration
    if log:
        prev = log[-1]
        current["delta"] = {
            "new_people": current["total_people"] - prev["total_people"],
            "new_matched": current["company_matched"] - prev["company_matched"],
            "match_rate_change": round(current["company_match_rate"] - prev["company_match_rate"], 1),
            "mean_lead_score_change": round(
                (current["lead_score"]["mean"] or 0) - (prev["lead_score"]["mean"] or 0), 1
            ),
            "previous_version": prev["version"],
        }
    else:
        current["delta"] = None

    log.append(current)
    _save_velocity_log(conference, log)
    return current


def format_velocity_report(conference: str, format: str = "text") -> str:
    """Generate a human-readable velocity report.

    Args:
        conference: Conference key
        format: "text" for plain text, "markdown" for markdown

    Returns:
        Formatted report string.
    """
    log = _load_velocity_log(conference)
    if not log:
        return f"No velocity data for {conference}."

    lines = []
    conf_label = conference.upper().replace("_", " ")

    if format == "markdown":
        lines.append(f"## {conf_label} — Signal Velocity Report")
        lines.append("")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        lines.append("")

        # Summary table
        lines.append("| Version | People | Matched | Match % | Mean Lead | High (40+) | New People |")
        lines.append("|---------|--------|---------|---------|-----------|------------|------------|")

        for entry in log:
            ls = entry["lead_score"]
            high_count = ls["tier_manual_90plus"] + ls["tier_high_60plus"] + ls["tier_mid_40_59"]
            delta_people = ""
            if entry.get("delta"):
                dp = entry["delta"]["new_people"]
                delta_people = f"+{dp}" if dp > 0 else str(dp)

            mean_str = f"{ls['mean']:.1f}" if ls.get('mean') is not None else "—"
            lines.append(
                f"| {entry['version']} "
                f"| {entry['total_people']:,} "
                f"| {entry['company_matched']:,} "
                f"| {entry['company_match_rate']}% "
                f"| {mean_str} "
                f"| {high_count} "
                f"| {delta_people} |"
            )

        lines.append("")

        # Latest iteration detail
        latest = log[-1]
        ls = latest["lead_score"]
        lines.append(f"### Latest: {latest['version']} ({latest['timestamp']})")
        lines.append("")
        lines.append(f"**{latest['total_people']:,} people** scored, "
                      f"**{latest['company_matched']:,}** matched to companies "
                      f"({latest['company_match_rate']}%)")
        lines.append("")
        lines.append("**Lead Score Distribution:**")
        lines.append(f"- 🔴 Manual review (≥60): **{ls['tier_manual_90plus'] + ls['tier_high_60plus']}**")
        lines.append(f"- 🟠 High priority (40-59): **{ls['tier_mid_40_59']}**")
        lines.append(f"- 🟡 Auto outreach (20-39): **{ls['tier_auto_20_39']}**")
        lines.append(f"- ⚪ Low (10-19): **{ls['tier_low_10_19']}**")
        lines.append(f"- ⬜ Noise (<10): **{ls['tier_noise_below_10']}**")
        lines.append("")

        if latest.get("delta"):
            d = latest["delta"]
            lines.append(f"**vs {d['previous_version']}:** "
                          f"+{d['new_people']} people, "
                          f"+{d['new_matched']} matched, "
                          f"match rate {'↑' if d['match_rate_change'] >= 0 else '↓'}{abs(d['match_rate_change'])}%, "
                          f"mean lead score {'↑' if d['mean_lead_score_change'] >= 0 else '↓'}{abs(d['mean_lead_score_change'])}")

        # Source breakdown
        lines.append("")
        lines.append("**Sources:**")
        for src, count in latest.get("sources", {}).items():
            lines.append(f"- {src}: {count:,}")

    else:
        # Plain text format
        lines.append(f"{'='*60}")
        lines.append(f"  {conf_label} — SIGNAL VELOCITY REPORT")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"{'='*60}")
        lines.append("")

        for i, entry in enumerate(log):
            ls = entry["lead_score"]
            high_count = ls["tier_manual_90plus"] + ls["tier_high_60plus"] + ls["tier_mid_40_59"]
            mean_str = f"{ls['mean']:.1f}" if ls.get('mean') is not None else "—"
            lines.append(f"  {entry['version']}: {entry['total_people']:,} people | "
                          f"{entry['company_matched']:,} matched ({entry['company_match_rate']}%) | "
                          f"Mean Lead: {mean_str} | High (40+): {high_count}")
            if entry.get("delta"):
                d = entry["delta"]
                lines.append(f"    Δ vs {d['previous_version']}: "
                              f"+{d['new_people']} people, +{d['new_matched']} matched, "
                              f"mean LS {'+' if d['mean_lead_score_change'] >= 0 else ''}{d['mean_lead_score_change']}")
            lines.append("")

        lines.append(f"{'='*60}")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Conference signal velocity tracking")
    parser.add_argument("--conference", required=True, help="Conference key (e.g. gdc_sf_26)")
    parser.add_argument("--format", choices=["text", "markdown"], default="text", help="Output format")
    args = parser.parse_args()

    report = format_velocity_report(args.conference, format=args.format)
    print(report)
