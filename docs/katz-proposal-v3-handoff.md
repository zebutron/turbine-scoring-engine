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

## Your Notes Carry Forward Now

Looked at the current GDC sheet. Here's what I found:

**v1 tab:** Your DK columns (G:J) are populated — title flags, scores, notes, BD status. You've annotated many of the top leads with notes like "Not f2p", "not a game studio", "xbox-focused", "Company looks irrelevant", and BD statuses (DK email, LIDM, LIDM + MTM, Scheduling, Skipped).

**v2 tab:** DK columns exist (R:U) but only ~5 leads have notes carried over. Most of your v1 annotations didn't make it. That was a manual copy-paste process and it was lossy.

**The problem:** Every time a new scored iteration lands, your per-lead notes risk getting lost or incomplete. You're tracking both scoring feedback (for us to improve the engine) and BD status (for your outreach). Losing either is bad.

**What's now built:**

The scoring engine has a notes persistence system (`engine/notes.py`) that:

1. **Matches people across iterations** by Full Name + Company Name (same dedup logic the scoring engine uses)
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

## Proposed Workflow Going Forward

### What stays the same for Katz:
1. **Google Sheet as your working surface.** You steer BD from the scored people tab — filter, sort, take notes, flag scoring issues. That doesn't change.
2. **Your DK columns stay in the same position.** Title flag, DK Score, DK notes, DK status — same columns, same workflow.
3. **Velocity reports with each iteration.** Each time we score, you get: new people count, total list, new company matches, lead score distribution.
4. **You decide when to score.** Scrape schedule stays on your cadence.

### What changes (improvements):
1. **Notes persist automatically.** When a new scoring iteration uploads, your DK annotations from the prior version merge in. No manual copying.
2. **Notes are backed up.** Every iteration's annotations are saved to git. Even if the Sheet breaks, your notes are safe.
3. **Scoring feedback loops back.** When you flag a title as "too low" or note "not a game studio", we can extract those flags and use them to improve the scoring engine.
4. **Velocity tracking is automated.** The scoring engine records iteration stats and produces a velocity report automatically.
5. **Scoring runs faster.** Source prep + scoring + notes merge + summary in one command.

### How scored data gets to your Sheet:

**For v3 right now:** The scored output is a TSV. To get it into Google Sheets:
- Open the GDC Scored People sheet
- Add a new tab: "v3 Scored People - GDC"
- File → Import → Upload the TSV → Import into current sheet (select the new tab)
- The DK columns are already included (empty for v3 since it's the first automated run)

**Starting with v4 (next iteration):**
1. You annotate v3 in the Sheet (business as usual)
2. When v4 scoring runs, the engine pulls your v3 notes from the Sheet (or from a quick CSV export you do)
3. v4 scored output includes your v3 DK columns pre-filled for returning people
4. Upload v4 tab — your notes are already there

**Short-term (next week):** Set up Google Sheets API so this is fully automated: score → merge notes → publish new tab. One command, no manual import/export.

---

## What I Need From You

1. **Review the top 19 high-scoring leads** (40+) — do the scores make sense? Any obvious mis-scores? This calibration input directly improves the engine.
2. **Confirm the DK column layout works** — same 4 columns (title flag, score, notes, status). Want any changes? Additional columns?
3. **Try the v3 import** — upload the TSV to a new "v3 Scored People - GDC" tab. Start annotating. This becomes the baseline that carries forward to v4.
4. **Google Sheets API access** (when ready) — I'll need you or Zeb to create a Google Cloud service account and share the sheet with it. 15 min setup, then the full loop (score → merge notes → publish tab) is automatic.

---

## GDC Timeline

| Date | What |
|------|------|
| ~~Feb 20~~ | v3 scored ✅ |
| Feb 25 | GDC Scrape #4 → v4 scoring (with v3 notes carried forward) |
| Mar 4 | GDC Scrape #5 → v5 scoring + conference brief |
| Mar 17-21 | **GDC San Francisco** |

Each scoring run will produce a velocity report, carry forward your notes, and output a ready-to-import TSV. Once Sheets API is set up, it'll auto-publish.
