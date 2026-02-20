"""
Tests for the scoring engine. Verifies that core scoring functions produce
expected results given known inputs.
"""

import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.config import load_latest_config
from engine.people import (
    calculate_seniority_score,
    calculate_domain_score,
    calculate_contact_score,
    check_one_offs,
    apply_seniority_modifiers,
)
from engine.lead import calculate_lead_score
from engine.normalize import normalize_company_name, calculate_match_score, normalize_scores


def test_config_loads():
    """Config loads without error."""
    config = load_latest_config()
    assert 'peopleScore' in config
    assert 'companyScore' in config
    assert 'pillars' in config['peopleScore']
    print("  config loads OK")


def test_seniority_scores(config):
    """Known titles produce expected seniority ranges."""
    ceo = calculate_seniority_score("CEO", config)
    assert ceo >= 90, f"CEO seniority should be >= 90, got {ceo}"

    vp = calculate_seniority_score("VP of Marketing", config)
    assert vp >= 70, f"VP seniority should be >= 70, got {vp}"

    pm = calculate_seniority_score("Product Manager", config)
    assert pm > 0, f"Product Manager seniority should be > 0, got {pm}"

    empty = calculate_seniority_score("", config)
    assert empty == 0, f"Empty title seniority should be 0, got {empty}"

    print("  seniority scores OK")


def test_domain_scores(config):
    """Known titles produce expected domain ranges."""
    ceo = calculate_domain_score("CEO", config)
    assert ceo >= 90, f"CEO domain should be >= 90, got {ceo}"

    product = calculate_domain_score("Product Director", config)
    assert product > 0, f"Product Director domain should be > 0, got {product}"

    print("  domain scores OK")


def test_contact_score(config):
    """Contact score is a weighted average of pillars."""
    contact = calculate_contact_score(80, 95, 0, config)
    assert 0 < contact < 100, f"Contact score should be in (0, 100), got {contact}"
    print("  contact score OK")


def test_lead_score():
    """Lead score follows the spec rules."""
    # Normal case
    lead = calculate_lead_score(80, 90, True, True)
    assert abs(lead - 72.0) < 0.1, f"Expected ~72, got {lead}"

    # No company match
    lead_no_co = calculate_lead_score(80, 0, False, True)
    assert abs(lead_no_co - 24.0) < 0.1, f"Expected ~24, got {lead_no_co}"

    # No title
    lead_no_title = calculate_lead_score(0, 90, True, False)
    assert abs(lead_no_title - 27.0) < 0.1, f"Expected ~27, got {lead_no_title}"

    # Neither
    lead_none = calculate_lead_score(0, 0, False, False)
    assert abs(lead_none - 5.0) < 0.1, f"Expected ~5, got {lead_none}"

    print("  lead score OK")


def test_company_name_normalization():
    """Company names normalize consistently."""
    assert normalize_company_name("Supercell Oy") == "supercell"
    assert normalize_company_name("Moon Active Games Ltd.") == "moon active"
    assert normalize_company_name("") == ""
    assert normalize_company_name(None) == ""
    print("  company name normalization OK")


def test_fuzzy_matching():
    """Fuzzy matching scores identical names as 100."""
    score = calculate_match_score("Supercell Oy", "Supercell Games")
    assert score == 100, f"Expected 100 for same normalized name, got {score}"

    no_match = calculate_match_score("Apple Inc", "Microsoft Corp")
    assert no_match == 0, f"Expected 0 for different companies, got {no_match}"
    print("  fuzzy matching OK")


def test_score_normalization():
    """Min-max normalization produces correct range."""
    scores = [10, 20, 30, 40, 50]
    normalized = normalize_scores(scores)
    assert min(normalized) == 0.0
    assert max(normalized) == 100.0
    assert len(normalized) == 5

    # Single value
    single = normalize_scores([42])
    assert single == [42]

    print("  score normalization OK")


def main():
    print("Running scoring engine tests...\n")

    test_config_loads()
    config = load_latest_config()

    test_seniority_scores(config)
    test_domain_scores(config)
    test_contact_score(config)
    test_lead_score()
    test_company_name_normalization()
    test_fuzzy_matching()
    test_score_normalization()

    print("\nAll tests passed!")


if __name__ == "__main__":
    main()
