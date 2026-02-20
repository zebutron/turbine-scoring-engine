"""
Contact scoring: Seniority x Domain x Warmth -> Contact Score (0-100).

Migrated from score_people_2025-07-27.py. All scoring logic preserved exactly.
"""

import re
import os
import json
import logging
from typing import Dict, List, Tuple
from pathlib import Path

import pandas as pd
import numpy as np

from engine.config import load_config
from engine.normalize import (
    normalize_company_name,
    calculate_match_score_normalized,
    normalize_scores,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = _SCRIPT_DIR.parent


def parse_keywords_to_regex(keywords_string: str) -> str:
    """Convert a comma-separated keywords string to a regex pattern."""
    if not keywords_string or pd.isna(keywords_string):
        return None
    keywords = [k.strip() for k in keywords_string.split(',') if k.strip()]
    if not keywords:
        return None
    escaped_keywords = [re.escape(k) for k in keywords]
    pattern = r'(?i)(^|[^a-z])(' + '|'.join(escaped_keywords) + r')($|[^a-z])'
    return pattern


def get_pillar_components(config: dict, pillar_name: str) -> dict:
    """Extract components for a specific pillar from config."""
    try:
        return config['peopleScore']['pillars'][pillar_name]['components']
    except KeyError:
        logging.warning(f"Pillar '{pillar_name}' not found in config")
        return {}


def find_matching_components(title: str, components: dict, include_modifiers: bool = False) -> List[Tuple[str, int, str]]:
    """Find all matching components for a given title."""
    if not isinstance(title, str) or pd.isna(title) or not title.strip():
        return []

    matches = []
    title_lower = title.lower()

    for component_name, component_data in components.items():
        keywords = component_data.get('Keywords to Match', '')
        score = component_data.get('Score', 0)
        if not keywords or not score:
            continue

        is_modifier = isinstance(score, str) and (score.startswith('+') or score.startswith('-'))

        if is_modifier:
            if not include_modifiers:
                continue
            try:
                modifier_value = int(score)
            except ValueError:
                continue
            pattern = parse_keywords_to_regex(keywords)
            if pattern and re.search(pattern, title_lower):
                matches.append((component_name, modifier_value, keywords))
        else:
            if include_modifiers:
                continue
            pattern = parse_keywords_to_regex(keywords)
            if pattern and re.search(pattern, title_lower):
                matches.append((component_name, int(score), keywords))

    return matches


def find_modifiers(title: str, components: dict) -> List[Tuple[str, int, str]]:
    """Find all modifier components (like +10 for Senior, -15 for Junior)."""
    if not isinstance(title, str) or pd.isna(title) or not title.strip():
        return []

    modifiers = []
    title_lower = title.lower()

    for component_name, component_data in components.items():
        keywords = component_data.get('Keywords to Match', '')
        score = component_data.get('Score', 0)
        if isinstance(score, str) and (score.startswith('+') or score.startswith('-')):
            try:
                modifier_value = int(score)
            except ValueError:
                continue
            pattern = parse_keywords_to_regex(keywords)
            if pattern and re.search(pattern, title_lower):
                modifiers.append((component_name, modifier_value, keywords))

    return modifiers


def calculate_seniority_score(title: str, config: dict) -> float:
    """Calculate seniority score based on job title using config data."""
    if not isinstance(title, str) or pd.isna(title) or not title.strip():
        return 0.0

    seniority_components = get_pillar_components(config, 'Seniority')
    matches = find_matching_components(title, seniority_components, include_modifiers=False)

    best_score = 0
    if matches:
        best_score = max(score for _, score, _ in matches)

    modifiers = find_modifiers(title, seniority_components)
    for _, modifier_value, _ in modifiers:
        best_score = min(100, best_score + modifier_value)

    return best_score


def calculate_domain_score(title: str, config: dict) -> float:
    """Calculate domain relevance score. Uses 'longest match wins' logic."""
    if not isinstance(title, str) or pd.isna(title) or not title.strip():
        return 0.0

    domain_components = get_pillar_components(config, 'Domain')
    matches_with_keywords = []
    title_lower = title.lower()

    for component_name, component_data in domain_components.items():
        keywords_string = component_data.get('Keywords to Match', '')
        score = component_data.get('Score', 0)
        if not keywords_string or not score or isinstance(score, str):
            continue

        keywords = [k.strip() for k in keywords_string.split(',') if k.strip()]
        for keyword in keywords:
            keyword_lower = keyword.lower()
            pattern = r'(?i)(^|[^a-z])(' + re.escape(keyword_lower) + r')($|[^a-z])'
            if re.search(pattern, title_lower):
                matches_with_keywords.append((component_name, int(score), keyword, len(keyword)))

    if not matches_with_keywords:
        return 0.0

    matches_with_keywords.sort(key=lambda x: x[3], reverse=True)
    best_match = matches_with_keywords[0]
    best_score = best_match[1]

    if len(matches_with_keywords) > 1:
        highest_score_match = max(matches_with_keywords, key=lambda x: x[1])
        if highest_score_match[1] > best_score:
            logging.info(f"Longest match rule: '{title}' - using '{best_match[2]}' ({best_score}) over '{highest_score_match[2]}' ({highest_score_match[1]})")

    return best_score


def calculate_warmth_score(person_data: dict, config: dict) -> float:
    """Calculate warmth score based on engagement data."""
    return 0.0


def check_one_offs(title: str, config: dict) -> Tuple[float, float]:
    """Check for one-off title overrides that set both seniority and domain scores."""
    if not isinstance(title, str) or pd.isna(title) or not title.strip():
        return None, None

    oneoff_components = get_pillar_components(config, 'One-Offs')
    matches = find_matching_components(title, oneoff_components)

    if matches:
        best_score = max(score for _, score, _ in matches)
        return best_score, best_score

    return None, None


def apply_seniority_modifiers(title: str, base_score: float, config: dict) -> float:
    """Apply seniority modifiers (Sr +10, Jr -15, etc.) to a base score."""
    if not isinstance(title, str) or pd.isna(title) or not title.strip():
        return base_score

    seniority_components = get_pillar_components(config, 'Seniority')
    modifiers = find_modifiers(title, seniority_components)
    modified_score = base_score
    for _, modifier_value, _ in modifiers:
        modified_score += modifier_value

    return max(0, min(100, modified_score))


def calculate_contact_score(seniority: float, domain: float, warmth: float, config: dict) -> float:
    """Calculate Contact Score using weighted average of pillars."""
    seniority_weight = float(config['peopleScore']['pillars']['Seniority']['description'])
    domain_weight = float(config['peopleScore']['pillars']['Domain']['description'])
    warmth_weight = float(config['peopleScore']['pillars']['Warmth']['description'])

    total_weight = seniority_weight + domain_weight + warmth_weight
    contact_score = (
        (seniority * seniority_weight) +
        (domain * domain_weight) +
        (warmth * warmth_weight)
    ) / total_weight

    return contact_score


def match_person_to_company(person_normal_company: str, companies_df: pd.DataFrame) -> Tuple[str, float, float]:
    """Match a person's normalized company to the scored companies list."""
    if not isinstance(person_normal_company, str) or pd.isna(person_normal_company) or not person_normal_company.strip():
        return "", 0.0, 0.0

    best_match = ""
    best_score = 0.0
    best_company_score = 0.0
    min_confidence = 90.0

    for _, company_row in companies_df.iterrows():
        company_name = company_row['Company Name']
        company_score = company_row['Company Score']
        company_normal = company_row['Normal Company']

        if not isinstance(company_normal, str) or not company_normal.strip():
            continue

        match_score = calculate_match_score_normalized(person_normal_company, company_normal)

        if match_score >= min_confidence and match_score > best_score:
            best_match = company_name
            best_score = match_score
            best_company_score = company_score

    return best_match, best_score, best_company_score


def load_master_stats() -> dict:
    """Load master list stats for normalization if available."""
    stats_path = _REPO_ROOT / "store" / "baselines" / "MASTER_PEOPLE_STATS.json"
    if not stats_path.exists():
        logging.warning("Master stats not found; falling back to list normalization.")
        return {}
    try:
        with open(stats_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:
        logging.warning(f"Failed to load master stats: {exc}")
        return {}


def process_people_scoring(input_file: str, companies_file: str, config: dict) -> pd.DataFrame:
    """Main function to process people scoring. Returns scored DataFrame."""

    people_sep = '\t' if input_file.lower().endswith('.tsv') else ','
    people_df = pd.read_csv(input_file, sep=people_sep)
    companies_df = pd.read_csv(companies_file)

    if 'Company Name' not in people_df.columns and 'Company' in people_df.columns:
        people_df['Company Name'] = people_df['Company']

    if 'Normal Company' not in people_df.columns:
        people_df['Normal Company'] = people_df['Company Name'].apply(
            lambda x: normalize_company_name(x) if pd.notna(x) else ''
        )
    else:
        people_df['Normal Company'] = people_df['Normal Company'].fillna('')
        if 'Company Name' in people_df.columns:
            missing_mask = people_df['Normal Company'].astype(str).str.strip() == ''
            people_df.loc[missing_mask, 'Normal Company'] = people_df.loc[missing_mask, 'Company Name'].apply(
                lambda x: normalize_company_name(x) if pd.notna(x) else ''
            )

    print(f"Loaded {len(people_df)} people from staging")
    print(f"Loaded {len(companies_df)} companies for matching")

    results = []
    total_people = len(people_df)

    print(f"\nProcessing {total_people} people...")
    print("Progress (0.0%): [" + "░" * 50 + "]", end="", flush=True)

    raw_contact_scores = []
    raw_lead_scores = []

    for idx, person in people_df.iterrows():
        progress = (idx + 1) / total_people
        filled_length = int(50 * progress)
        bar = "█" * filled_length + "░" * (50 - filled_length)
        percent = progress * 100
        print(f"\rProgress ({percent:.1f}%): [{bar}]", end="", flush=True)

        first_name = person.get('First Name', '') if pd.notna(person.get('First Name', '')) else ''
        last_name = person.get('Last Name', '') if pd.notna(person.get('Last Name', '')) else ''
        job_title = person.get('Job Title', '') if pd.notna(person.get('Job Title', '')) else ''
        company_name = person.get('Company Name', '') if pd.notna(person.get('Company Name', '')) else ''
        normal_company = person.get('Normal Company', '') if pd.notna(person.get('Normal Company', '')) else ''
        source = person.get('Source', '') if pd.notna(person.get('Source', '')) else ''
        date_created = person.get('Date Created', '') if pd.notna(person.get('Date Created', '')) else ''
        date_updated = person.get('Date Updated', '') if pd.notna(person.get('Date Updated', '')) else ''

        one_off_seniority, one_off_domain = check_one_offs(job_title, config)

        if one_off_seniority is not None and one_off_domain is not None:
            seniority_score = apply_seniority_modifiers(job_title, one_off_seniority, config)
            domain_score = one_off_domain
        else:
            seniority_score = calculate_seniority_score(job_title, config)
            domain_score = calculate_domain_score(job_title, config)

        warmth_score = calculate_warmth_score(person.to_dict(), config)

        raw_contact_score = calculate_contact_score(seniority_score, domain_score, warmth_score, config)

        matched_company, match_confidence, company_score = match_person_to_company(normal_company, companies_df)

        has_company_match = match_confidence >= 90.0
        has_job_title = bool(job_title and isinstance(job_title, str) and job_title.strip())

        # Import lead score calculation
        from engine.lead import calculate_lead_score
        raw_lead_score = calculate_lead_score(raw_contact_score, company_score, has_company_match, has_job_title)

        raw_contact_scores.append(raw_contact_score)
        raw_lead_scores.append(raw_lead_score)

        extra_data = person.get('Extra Data', '')

        result = {
            'First Name': first_name,
            'Last Name': last_name,
            'Full Name': f"{first_name} {last_name}".strip(),
            'Job Title': job_title,
            'Company Name': company_name,
            'Extra Data': extra_data,
            'Raw Contact Score': raw_contact_score,
            'Raw Lead Score': raw_lead_score,
            'Company Score': round(company_score) if company_score > 0 else '',
            'Seniority': round(seniority_score),
            'Domain': round(domain_score),
            'Warmth': round(warmth_score),
            'Matched Company': matched_company,
            'Match Confidence': round(match_confidence) if match_confidence > 0 else '',
            'Source': source,
            'Date Created': date_created,
            'Date Updated': date_updated
        }

        results.append(result)

    print(f"\rProgress (100.0%): [{'█' * 50}] - Complete!", flush=True)
    print()

    # Apply min-max normalization
    print("Applying min-max normalization...")
    stats = load_master_stats()
    contact_min = stats.get("contact_score_min")
    contact_max = stats.get("contact_score_max")
    lead_min = stats.get("lead_score_min")
    lead_max = stats.get("lead_score_max")
    normalized_contact_scores = normalize_scores(raw_contact_scores, contact_min, contact_max)
    normalized_lead_scores = normalize_scores(raw_lead_scores, lead_min, lead_max)

    for i, result in enumerate(results):
        result['Contact Score'] = round(normalized_contact_scores[i])
        result['Lead Score'] = round(normalized_lead_scores[i])
        del result['Raw Contact Score']
        del result['Raw Lead Score']

    results_df = pd.DataFrame(results)

    column_order = [
        'First Name', 'Last Name', 'Full Name', 'Job Title', 'Company Name',
        'Lead Score', 'Contact Score', 'Company Score', 'Seniority', 'Domain', 'Warmth',
        'Matched Company', 'Match Confidence', 'Source', 'Date Created', 'Date Updated',
        'Extra Data'
    ]

    results_df = results_df[column_order]
    results_df = results_df.sort_values('Lead Score', ascending=False).reset_index(drop=True)

    raw_contact_range = f"{min(raw_contact_scores):.1f}-{max(raw_contact_scores):.1f}"
    norm_contact_range = f"{min(normalized_contact_scores):.1f}-{max(normalized_contact_scores):.1f}"
    raw_lead_range = f"{min(raw_lead_scores):.1f}-{max(raw_lead_scores):.1f}"
    norm_lead_range = f"{min(normalized_lead_scores):.1f}-{max(normalized_lead_scores):.1f}"

    print(f"Normalization applied:")
    print(f"   Contact Scores: {raw_contact_range} -> {norm_contact_range}")
    print(f"   Lead Scores: {raw_lead_range} -> {norm_lead_range}")

    return results_df
