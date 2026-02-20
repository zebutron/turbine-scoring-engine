# GDC SF v3 Scoring Results + Proposed Workflow
*Feb 20, 2026 — For Katz review*

---

## What We Just Did (v3)

Ran scoring iteration #3 for GDC San Francisco '26. Combined your latest MTM Scrape 3 with the existing LISN data, deduplicated, and scored against the full company store (11K+ companies).

## Signal Velocity: v1 → v2 → v3

| Version | People | Matched | Match % | Mean Lead | High (40+) | Δ People |
|---------|--------|---------|---------|-----------|------------|----------|
| v1 (LISN + MTM Scrape 1) | 1,835 | 350 | 19.1% | — | — | — |
| v2 (LISN + MTM Scrapes 1-2) | 2,263 | 413 | 18.2% | — | — | +428 |
| **v3 (Scrape 3 + LISN)** | **2,452** | **495** | **20.2%** | **8.4** | **19** | **+189** |

**Key takeaways:**
- MTM list grew substantially: 348 → 777 → **1,067** people from MTM across 3 scrapes
- Company match rate improved from 18.2% → **20.2%** (82 new matches)
- 19 high-priority leads (Lead Score ≥40) identified
- 2 people scored 60+ (Douglas Hare @ Outplay, Saikat Mondal @ Nazara)

## v3 Lead Score Distribution

- 🔴 Top priority (≥60): **2** — manual review, high-value targets
- 🟠 High priority (40-59): **17** — worth personal outreach
- 🟡 Worth contacting (20-39): **475** — template DMs / connection requests
- ⚪ Low priority (10-19): **399** — contact if easy
- ⬜ Noise (<10): **1,559** — skip unless something changes

## Where the Output Lives Right Now

The scored TSV is in the GitHub repo: `output/GDC_SAN_FRANCISCO_26_Scored_People_2026-02-20.tsv`

**Columns:** First Name, Last Name, Full Name, Job Title, Company Name, Lead Score, Contact Score, Company Score, Seniority, Domain, Warmth, Matched Company, Match Confidence, Source, Date Created, Date Updated, Extra Data

Sorted by Lead Score descending — top targets first.

---

## Proposed Workflow Going Forward

### What stays the same for Katz:
1. **Google Sheet as your working surface.** You steer BD from the scored people tab — filter, sort, take notes, flag scoring issues. That doesn't change.
2. **Velocity reports with each iteration.** Each time we score, you get: new people count, total list, new company matches, lead score distribution. Same info you've been getting.
3. **You decide when to score.** Scrape schedule stays on your cadence. When a new scrape lands, we score it and deliver results.

### What changes (improvements):
1. **Velocity tracking is now automated.** The scoring engine records iteration stats automatically. Running the scorer produces a velocity report comparing to all prior iterations. No manual tracking needed.
2. **Scoring runs faster.** Source prep + scoring + summary in one command. The engine handles merging MTM + LISN sources, deduplication, and scoring.
3. **Master people list stays current.** Every scoring run updates the master list (now 8,051 people across all conferences). Cross-conference dedup means no double-outreach.

### How scored data gets to your Sheet:

**Right now (pragmatic):** The scored output is a TSV. To get it into Google Sheets:
- Open the GDC Scored People sheet
- Add a new tab: "v3 Scored People - GDC"
- File → Import → Upload the TSV → Import into current sheet (select the new tab)
- Or: open the TSV, select all, copy, paste into the new tab

**Short-term (next week):** Set up Google Sheets API with a service account so the scoring engine can push results directly to a new tab in your sheet. One command: score + publish.

**Why not Sheets API today:** No service account credentials configured yet. Setting that up takes ~15 min but I want your sign-off on the overall workflow before adding infrastructure.

---

## What I Need From You

1. **Review the top 19 high-scoring leads** (40+) — do the scores make sense? Any obvious mis-scores? This is the most important calibration input.
2. **Confirm this workflow works for you** — scored TSV → import to Sheet tab → work from there. Or tell me what you'd change.
3. **Google Sheets API access** (when ready) — I'll need you to create a Google Cloud service account and share the sheet with it. 15 min setup, then scoring → Sheet is automatic.
4. **Katz's GitHub handle** — `turbinekatz` (grabbed from Slack). I'll add you as collaborator on `zebutron/turbine-scoring-engine` so you can run scoring from your own Claude Code.

---

## GDC Timeline

| Date | What |
|------|------|
| ~~Feb 20~~ | v3 scored ✅ |
| Feb 25 | GDC Scrape #4 → v4 scoring |
| Mar 4 | GDC Scrape #5 → v5 scoring + conference brief |
| Mar 17-21 | **GDC San Francisco** |

Each scoring run will produce a velocity report and updated scored TSV. If we get Sheets API set up, it'll auto-publish to your tab.
