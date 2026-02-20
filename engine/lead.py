"""
Lead score computation: Contact Score x Company Score + penalties.

Lead Score = (Contact Score / 100) * Company Score
Penalties:
  - No company match, has title: Contact Score * 0.3  (70% penalty)
  - Has company, no title: Company Score * 0.3  (70% penalty)
  - No company, no title: 5.0
"""


def calculate_lead_score(contact_score: float, company_score: float,
                         has_company_match: bool, has_job_title: bool) -> float:
    """Calculate final Lead Score based on Contact Score and Company Score."""
    if has_company_match and has_job_title:
        lead_score = (contact_score / 100.0) * company_score
    elif has_company_match and not has_job_title:
        lead_score = company_score * 0.3
    elif not has_company_match and has_job_title:
        lead_score = contact_score * 0.3
    else:
        lead_score = 5.0

    return max(0.0, min(100.0, lead_score))
