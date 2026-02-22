# GDC SF v3 Scoring Results + Workflow
*Feb 22, 2026 — For Katz review*

---

## What We Just Did (v3)

Ran scoring iteration #3 for GDC San Francisco '26. Accumulated all prior scrapes (LISN v1, MTM Scrapes 1-3) into a single deduplicated attendee list, then scored against the full company store (11K+ companies).

**Corrected from earlier run:** The initial v3 combine dropped ~370 people from prior MTM scrapes. That's fixed — the accumulated list now includes everyone from all sources across all iterations.

## Signal Velocity: v1 → v2 → v3

| Version | People | Matched | Match % | Mean Lead | High (40+) | Δ People |
|---------|--------|---------|---------|-----------|------------|----------|
| v1 (LISN + MTM Scrape 1) | 1,835 | 350 | 19.1% | — | — | — |
| v2 (LISN + MTM Scrapes 1-2) | 2,263 | 413 | 18.2% | — | — | +428 |
| **v3 (LISN + MTM Scrapes 1-3)** | **2,824** | **524** | **18.6%** | **8.9** | **20** | **+561** |

**Key takeaways:**
- 561 net new people from MTM Scrape 3 (after dedup against prior scrapes)
- 524 people matched to scored companies (18.6%)
- 20 high-priority leads (Lead Score ≥40) identified
- 2 people scored 60+ (top targets for manual review)

## v3 Lead Score Distribution

- Top priority (60+): **2** — manual review, high-value targets
- High priority (40-59): **18** — worth personal outreach
- Worth contacting (20-39): **609** — template DMs / connection requests
- Low priority (10-19): **502** — contact if easy
- Noise (<10): **1,693** — skip unless something changes

## Where the Output Lives

The scored TSV is in the GitHub repo: `output/GDC_SAN_FRANCISCO_26_Scored_People_2026-02-21.tsv`

**Columns:** First Name, Last Name, Full Name, Job Title, Company Name, Lead Score, Contact Score, Company Score, Seniority, Domain, Warmth, Matched Company, Match Confidence, Source, Date Created, Date Updated, Extra Data

Sorted by Lead Score descending — top targets first.

---

## How the Workflow Works Now

Here's the honest picture of what's automated vs. what's manual.

### What you do (manual):
1. **Scrape MTM** — Log into Meet-to-Match, browse attendees, export/copy data. This is the part that requires a human navigating the MTM website. You decide the scrape cadence (weekly, bi-weekly, etc.).
2. **Export LISN** — LinkedIn Sales Nav searches + Evaboot/PhantomBuster export. Also manual.
3. **Drop source files** into the `sources/` folder in the repo as TSV/CSV.
4. **Annotate in Google Sheets** — After scored output is uploaded, you add your DK columns (title flags, scores, notes, BD status). This is your working surface.
5. **Export your annotated Sheet** when you want notes carried into the next iteration (File → Download → TSV). Drop it in `sources/`.

### What the engine does (automated):
1. **Accumulate** — Takes any new source files and merges them with the existing attendee list. Deduplicates by name + company. Never drops people from prior scrapes. Tracks which scrapes each person appeared in.
2. **Score** — Scores all accumulated people against the company store. Seniority, Domain, Warmth → Contact Score. Budget, Alignment, Demand → Company Score. Lead Score = Contact % × Company.
3. **Carry notes forward** — When you export your annotated Sheet and re-ingest it, the engine matches people by name + company and carries your DK columns into the new scored output.
4. **Track velocity** — Each scoring iteration records: total people, company matches, match rate, lead score distribution, and delta vs. prior iteration. Produces a velocity report automatically.
5. **Output** — Sorted TSV ready to upload to Google Sheets.

### The v4 workflow (one cycle):
```
You scrape MTM / LISN → drop files in sources/
  ↓
Run accumulate (adds new people to the pile, updates existing)
  ↓
Run scorer (scores all accumulated people)
  ↓
Export your annotated v3 Sheet → re-ingest (carries notes forward)
  ↓
Output: v4 scored TSV with your v3 notes pre-filled
  ↓
Upload to Google Sheets → annotate → repeat for v5
```

### What's NOT automated yet:
- **Scraping itself.** MTM browsing, LISN exports — still manual. We can assess automating the MTM scrape (the SOP doc describes the process), but that's a separate effort.
- **Google Sheets upload/download.** Currently you download TSV from the repo and import it. Setting up the Sheets API would make this automatic, but it's not wired up yet.

---

## Your Notes Carry Forward Now

Looked at the current GDC sheet. Here's what I found:

**v1 tab:** Your DK columns (G:J) are populated — title flags, scores, notes, BD status. You've annotated many of the top leads with notes like "Not f2p", "not a game studio", "xbox-focused", "Company looks irrelevant", and BD statuses (DK email, LIDM, LIDM + MTM, Scheduling, Skipped).

**v2 tab:** DK columns exist (R:U) but only ~5 leads have notes carried over. Most of your v1 annotations didn't make it. That was a manual copy-paste process and it was lossy.

**The problem:** Every time a new scored iteration lands, your per-lead notes risk getting lost or incomplete. You're tracking both scoring feedback (for us to improve the engine) and BD status (for your outreach). Losing either is bad.

**What's now built:**

The scoring engine has a notes persistence system that:

1. **Matches people across iterations** by Full Name + Company Name (same dedup logic the engine uses)
2. **Carries forward all 4 DK columns** automatically:
   - `DK: title too low (1) or too high (0)` — your scoring feedback
   - `DK Score (0-2)` — your manual quality rating
   - `DK notes` — your free-text notes per lead
   - `DK status` — your BD status (LIDM, Skipped, DK email, Scheduling, etc.)
3. **New people get empty DK columns** — ready for you to annotate
4. **Notes are backed up in git** — `store/notes/` holds snapshots per iteration, so even if a Sheet gets messed up, your notes are recoverable
5. **Scoring feedback gets extracted** — we can pull out rows where you flagged title issues or bad scores, and feed them directly into engine improvements

**What this means for you:** When v4 lands, you'll get a new Scored People tab where every person you already annotated in v3 still has their notes. No more manual copy-paste. No more lost outreach status.

---

## What I Need From You

1. **Review the top 20 high-scoring leads** (40+) — do the scores make sense? Any obvious mis-scores? This calibration input directly improves the engine.
2. **Confirm the DK column layout works** — same 4 columns (title flag, score, notes, status). Want any changes? Additional columns?
3. **Try the v3 import** — upload the TSV to a new "v3 Scored People - GDC" tab. Start annotating. This becomes the baseline that carries forward to v4.
4. **When v4 scraping is done:** Drop your new MTM/LISN source files in the repo. The engine accumulates, scores, and carries your notes forward. One command.

---

## GDC Timeline

| Date | What |
|------|------|
| ~~Feb 20~~ | v3 scored (2,824 people) |
| Feb 25 | GDC Scrape #4 → v4 scoring (with v3 notes carried forward) |
| Mar 4 | GDC Scrape #5 → v5 scoring + conference brief |
| Mar 17-21 | **GDC San Francisco** |

Each scoring run produces a velocity report, carries forward your notes, and outputs a ready-to-import TSV.
