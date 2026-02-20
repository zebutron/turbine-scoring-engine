"""
Name normalization, fuzzy matching, and min-max score normalization.

Extracted from the monolithic score_people_2025-07-27.py into a shared module.
"""

import re
from difflib import SequenceMatcher
from typing import List, Optional

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Company name normalization
# ---------------------------------------------------------------------------

CORPORATE_SUFFIXES = {
    'llc', 'inc', 'ltd', 'gmbh', 'limited', 'corporation', 'corp', 'plc', 'sa', 'srl',
    'ag', 'ab', 'oy', 'as', 'bv', 'sas', 'sarl', 'sro', 'spa',
    'global', 'international', 'group', 'holdings', 'holding', 'enterprises', 'enterprise',
    'company', 'companies', 'co', 'pty', 'proprietary', 'private',
    'public', 'incorporated', 'llp',
    'sp', 'z', 'o', 's', 'a', 'b', 'v', 'n', 'r', 'l'
}

INDUSTRY_SUFFIXES = {
    'games', 'game', 'gaming', 'studio', 'studios', 'entertainment', 'interactive',
    'digital', 'media', 'publishing', 'publisher', 'publishers', 'software', 'tech',
    'technology', 'solutions', 'services', 'service',
    'casino', 'casinos', 'slots', 'slot', '777', 'gambling', 'betting', 'bets',
    'mobile', 'apps', 'applications', 'application', 'app',
    'social games', 'social gaming', 'online games', 'online gaming', 'billionaire',
    'millionaire', 'jackpot', 'jackpots', 'win', 'wins', 'winning', 'winners',
    'prize', 'prizes', 'tournament', 'tournaments',
    'championship', 'championships', 'league', 'leagues', 'challenge', 'challenges'
}

DOMAIN_SUFFIXES = {
    '.com', '.org', '.net', '.io', '.xyz', '.ai', '.co', '.biz', '.info', '.app',
    '.games', '.game', '.tech', '.studio', '.dev', '.cloud', '.digital'
}


def normalize_company_name(name: str, preserve_industry_suffix: bool = False) -> str:
    """Normalize company name by removing punctuation, corporate suffixes, and more."""
    if not isinstance(name, str) or pd.isna(name):
        return ""

    name = name.lower()
    name = re.sub(r'[^a-z0-9\s]', ' ', name)
    name = re.sub(r'\([^)]*\)', ' ', name)

    words = name.split()
    words = [w for w in words if w not in CORPORATE_SUFFIXES]
    words = [w for w in words if not any(w.endswith(suffix) for suffix in DOMAIN_SUFFIXES)]

    if not preserve_industry_suffix:
        words = [w for w in words if w not in INDUSTRY_SUFFIXES]

    words = [w for w in words if not (w.isdigit() and len(w) <= 4)]

    return ' '.join(words).strip()


# ---------------------------------------------------------------------------
# Fuzzy matching
# ---------------------------------------------------------------------------

def calculate_match_score(name1: str, name2: str) -> float:
    """Calculate match score between two company names using sophisticated matching."""
    if not isinstance(name1, str) or not isinstance(name2, str) or pd.isna(name1) or pd.isna(name2):
        return 0

    clean1 = normalize_company_name(name1)
    clean2 = normalize_company_name(name2)

    if not clean1 or not clean2:
        return 0

    if clean1 == clean2:
        return 100

    len_ratio = min(len(clean1), len(clean2)) / max(len(clean1), len(clean2))
    if len_ratio < 0.8:
        return 0

    if (clean1 in clean2 or clean2 in clean1) and min(len(clean1), len(clean2)) >= 5:
        if len_ratio > 0.9:
            return 97

    ratio = SequenceMatcher(None, clean1, clean2).ratio()
    if ratio >= 0.98:
        return ratio * 100

    return 0


def calculate_match_score_normalized(person_normalized: str, company_normalized: str) -> float:
    """Calculate match score between two pre-normalized company names."""
    if not person_normalized or not company_normalized:
        return 0

    if person_normalized == company_normalized:
        return 100

    len_ratio = min(len(person_normalized), len(company_normalized)) / max(len(person_normalized), len(company_normalized))
    if len_ratio < 0.8:
        return 0

    if (person_normalized in company_normalized or company_normalized in person_normalized) and min(len(person_normalized), len(company_normalized)) >= 5:
        if len_ratio > 0.9:
            return 97

    ratio = SequenceMatcher(None, person_normalized, company_normalized).ratio()
    if ratio >= 0.98:
        return ratio * 100

    return 0


# ---------------------------------------------------------------------------
# Score normalization
# ---------------------------------------------------------------------------

def normalize_scores(scores: List[float],
                     min_score: Optional[float] = None,
                     max_score: Optional[float] = None) -> List[float]:
    """Apply min-max normalization to spread scores across 0-100 range."""
    if not scores or len(scores) == 0:
        return scores

    if min_score is None:
        min_score = min(scores)
    if max_score is None:
        max_score = max(scores)

    if max_score == min_score:
        return scores

    return [(score - min_score) / (max_score - min_score) * 100 for score in scores]


def normalize_scores_0_100(scores):
    """Min-max normalize scores to 0-100 range for human readability."""
    if not scores or all(pd.isna(s) or s == 0 for s in scores):
        return [0.0] * len(scores)

    score_array = np.array([s if not pd.isna(s) else 0 for s in scores])

    min_val = np.min(score_array)
    max_val = np.max(score_array)

    if max_val == min_val:
        return [50.0] * len(scores)

    normalized = ((score_array - min_val) / (max_val - min_val)) * 100
    return [round(score, 1) for score in normalized]
