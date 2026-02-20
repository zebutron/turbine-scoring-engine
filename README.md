# Turbine Scoring Engine

Lead scoring engine for Turbine Games Consulting. Scores potential clients (companies) and their contacts (people) to prioritize sales outreach across conferences, LinkedIn, and CRM.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Score a conference attendee list

```bash
# Copy the template
cp scorers/TEMPLATE.py scorers/my_conference.py

# Edit the 4 config lines, then:
python -m scorers.my_conference
```

### Update scoring config from Google Sheets

```bash
python -m engine.config --force
```

### Run tests

```bash
python -m tests.test_scoring
```

## Architecture

- `engine/` — Core scoring logic (stateless, importable)
- `store/` — Canonical entity data (11K companies, 4K people)
- `scorers/` — Per-conference scoring scripts
- `enrichment/` — Data source update scripts
- `configs/` — Cached scoring weight JSONs
- `specs/` — Scoring specification docs

See [CLAUDE.md](CLAUDE.md) for detailed architecture docs.
