# Turbine Scoring Engine — Claude Context

## What This Is

Lead scoring engine for Turbine Games Consulting. Prioritizes sales targets by scoring people (contacts) against companies (potential clients). Used for conference targeting, LinkedIn BD, and pipeline management.

**Primary user:** Katz's Claude (daily conference scoring + BD ops).
**R&D:** Zeb's Claude (architecture improvements, new enrichment sources).

## Quick Start: Score a Conference

This is the most common operation. Given an attendee CSV/TSV, produce a prioritized lead list.

```bash
# 1. Place your attendee file in sources/
#    Expected columns: First Name, Last Name, Job Title, Company (or Company Name), Source

# 2. Copy the template scorer
cp scorers/TEMPLATE.py scorers/your_conference.py

# 3. Edit the 4 config lines at the top:
#    - input_file: path to your attendee file in sources/
#    - companies_file: store/companies.csv (usually don't change)
#    - output_file: where you want the scored output
#    - Column mapping if your input has different column names

# 4. Run it
python -m scorers.your_conference

# 5. Results land in output/ as a TSV sorted by Lead Score (high to low)
```

See `scorers/gdc_sf_26.py` for a working example.

### Signal Velocity Tracking

Each scoring run automatically records iteration stats. To view:

```bash
# View velocity report for a conference
python -m engine.velocity --conference gdc_sf_26

# Markdown format (for sharing)
python -m engine.velocity --conference gdc_sf_26 --format markdown
```

The scorer records velocity automatically. Stats tracked per iteration:
- Total people, new people vs prior iteration
- Company match count and rate
- Lead score distribution (tiers: 60+, 40-59, 20-39, 10-19, <10)
- Mean/median lead score trend

## Architecture Overview

```
engine/          Core scoring logic (stateless, importable)
  people.py      Contact scoring: Seniority x Domain x Warmth
  companies.py   Company scoring: Budget x Alignment x Demand
  lead.py        Lead Score = Contact x Company + penalties
  normalize.py   Name normalization, fuzzy matching, min-max
  config.py      Load scoring config from JSON / Google Sheets
  master.py      Build master people list from all scored files
  velocity.py    Conference signal velocity tracking (iteration-over-iteration metrics)

store/           Canonical entity data (committed to git)
  companies.csv  11K+ scored companies
  people.csv     8K+ scored people (master list)
  baselines/     Normalization ranges for absolute scoring
  velocity/      Per-conference velocity logs (JSON, auto-generated)

scorers/         Per-conference scoring scripts
  TEMPLATE.py    Copy this for new conferences
  gdc_sf_26.py   Working example

enrichment/      Source-specific data update scripts (stubs)
configs/         Cached scoring config JSONs
specs/           Scoring specification docs
```

## Scoring Model

**Lead Score = Contact Score (as %) x Company Score**

- Contact Score (0-100): Seniority (wt 100) + Domain (wt 70) + Warmth (wt 50)
- Company Score (0-100): Budget (wt 100) + Alignment (wt 60) + Demand (wt 40)
- Penalties: no company match = -70%, no title = -70%, neither = score 5

**Workflow tiers:**
- MANUAL (≥90): White glove review
- AUTO (30-89): Template outreach
- IGNORE (<30): No action

## What NOT to Touch

- **store/companies.csv** and **store/people.csv** are shared state. Don't delete or restructure columns without understanding downstream impact.
- **configs/** JSON files are the cached scoring weights. Don't edit manually — use `python -m engine.config --force` to refresh from Google Sheets.
- **specs/** are authoritative scoring documentation. Reference but don't modify unless the spec actually changes.

## Updating Scoring Config

The scoring weights/keywords live in a [Google Sheet](https://docs.google.com/spreadsheets/d/1GrLI_-FGDz83GilIgHO0hsGDtkTud98EoZz26qoa0dI/). To pull fresh config:

```bash
python -m engine.config --force
```

## Running Tests

```bash
python -m tests.test_scoring
```

## Key Dependencies

- pandas, numpy, scipy (scoring math)
- requests (Google Sheets config fetch)
- difflib (fuzzy name matching — stdlib)
