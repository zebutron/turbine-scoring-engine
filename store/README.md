# Store — Entity Data Schemas

The `store/` directory holds Turbine's canonical entity data. These files are committed to git (shared state). Enrichment scripts update them incrementally. Scoring is computed at runtime against this data.

## companies.csv

~11,200 pre-scored companies. Vintage: Sep 2025 enrichment data.

### Key Columns

| Column | Type | Description |
|--------|------|-------------|
| Company Name | str | Display name |
| Company Score | float | Final weighted score (0-100) |
| Alignment | float | Alignment pillar (0-100) |
| Budget | float | Budget pillar (0-100) |
| Demand | float | Demand pillar (0-100) |
| Dev | float | Makes games (normalized 0-100) |
| F2P | float | Free-to-play (normalized 0-100) |
| Mobile | float | Mobile games (normalized 0-100) |
| Fresh | float | Recent product (normalized 0-100) |
| Revenue | float | Revenue percentile (normalized 0-100) |
| Funding | float | Total funding percentile (normalized 0-100) |
| Headcount | float | Employee count percentile (normalized 0-100) |
| Status | float | Close CRM funnel status (normalized 0-100) |
| Volatility | float | Combined volatility signal (normalized 0-100) |
| URL | str | Website or LinkedIn URL |
| Country | str | HQ country |
| FLAG | str | Manual flags |
| Notes | str | Manual notes |
| Discover Source | str | How this company was found |
| Normalized Name | str | Cleaned name for fuzzy matching |

### Data Sources

- SensorTower: Revenue (Rev <30D), revenue change
- Growjo: Headcount, headcount change
- Crunchbase: Funding amounts, dates
- Close CRM: Funnel status, status change dates
- Manual: Makes Games, F2P, Mobile flags

## people.csv

~4,200 scored people across all conferences and sources. Master list built by `engine/master.py`.

### Key Columns

| Column | Type | Description |
|--------|------|-------------|
| First Name | str | |
| Last Name | str | |
| Full Name | str | First + Last |
| Job Title | str | |
| Company Name | str | Employer |
| Lead Score | float | Final lead score (0-100, normalized) |
| Contact Score | float | Contact score (0-100, normalized) |
| Company Score | float | Matched company's score |
| Seniority | int | Seniority pillar (0-100) |
| Domain | int | Domain relevance pillar (0-100) |
| Warmth | int | Engagement warmth (0-100) |
| Matched Company | str | Best company match from store |
| Match Confidence | float | Fuzzy match confidence (0-100) |
| Source | str | Data source (M2M, LISN, etc.) |
| Score Version | str | Scoring version used |
| Source List | str | Which file this person came from |

## baselines/

Pre-computed normalization ranges for absolute scoring mode.

- `MASTER_PEOPLE_STATS.json` — Min/max lead and contact scores across the full master list. Used by the scoring engine to normalize new lists against the master baseline (absolute mode).
