# MTM Scrape Automation — Assessment
*Feb 22, 2026*

---

## Context

Zeb's intention was to automate the Meet-to-Match (MTM) scrape process as part of the conference targeting pipeline. The SOP doc describes the manual process. This assessment covers what we know about the opportunity, what's needed, and what's blocked.

**Note:** The Conference Lead Targeting SOP doc (Google Doc) could not be read via API — requires authentication. This assessment is based on context from sales-hacking.md, prior session history, and the MTM scrape data we've already processed. **Before building anything, the SOP doc should be read via Chrome MCP to confirm the exact manual workflow.**

---

## What We Know About the MTM Scrape Process

### From prior sessions + sales-hacking.md:
1. **MTM = Meet-to-Match** (app.meettomatch.com) — conference networking platform where attendees register profiles
2. **Katz scrapes attendee lists** by browsing the MTM website for each conference
3. **There's a "Google Sheet tool with App Script for parsing"** — suggests the raw MTM page data gets pasted/imported into a Sheet, and an AppScript processes it into structured columns (First Name, Last Name, Job Title, Company)
4. **Scrapes happen iteratively** — MTM lists grow as the conference approaches (Scrape 1, 2, 3... each capturing new registrations)
5. **MTM adoption varies by conference** — PGC ~80% of attendees, GDC only 10-20%
6. **MTM credentials:** matt@turbine.games (password in sales-hacking.md)

### From the data we've processed:
- MTM Scrape 3 (GDC SF): 1,067 people, columns: First Name, Last Name, Job Title, Company, Source, Extra Data
- 253 of 1,067 (23.7%) had empty Job Title and Company — MTM profiles aren't always complete
- Source labels include "M2M" prefix (Meet-to-Match internal naming)

---

## Automation Opportunity Assessment

### What could be automated:

**1. MTM website scraping (Medium-High complexity)**
- **What:** Navigate MTM website, paginate through attendee list, extract names/titles/companies
- **How:** Chrome MCP (Claude in Chrome) navigating the MTM website, extracting attendee data page by page
- **Precedent:** MTM Scrape 3 was already done via Chrome MCP in a prior session — so this has been proven to work at least once
- **Blockers:**
  - Chrome MCP reliability (connection drops, "multiple extensions" errors)
  - MTM website structure may change between conferences
  - Need to handle pagination, search filters, and profile detail pages
  - Login session management
- **Effort estimate:** 4-8 hours to build a reliable, reusable scraper
- **Risk:** Medium — depends on Chrome MCP stability and MTM site structure

**2. AppScript parser replacement (Low complexity)**
- **What:** Replace the Google Sheet + AppScript parsing step with Python
- **How:** The scoring engine already handles the structured output (TSV with standard columns). If the Chrome MCP scraper outputs data in the right format, the AppScript is unnecessary.
- **Effort estimate:** Already handled by `engine/accumulate.py` — new scrape data goes directly into the accum
- **Risk:** Low

**3. Scrape scheduling / cadence tracking (Low complexity)**
- **What:** Track when each scrape was done, flag when the next scrape is due
- **How:** The velocity tracking system already records iteration timestamps. Could add a "next scrape due" alert.
- **Effort estimate:** 1-2 hours
- **Risk:** Low

### What can NOT be automated:

**1. LISN (LinkedIn Sales Navigator) exports**
- Sales Nav doesn't have an API. Exports require Evaboot or PhantomBuster (paid tools with per-credit pricing).
- Chrome MCP could theoretically navigate Sales Nav, but LinkedIn actively detects and blocks automation.
- **Recommendation:** Keep LISN exports manual. Katz or Matt runs the export tool, drops the file.

**2. Conference-specific apps**
- DICE required a mobile-only Biz Connect pass. Other conferences may have unique attendee systems.
- **Recommendation:** Handle case-by-case. Source files dropped manually.

---

## Recommendation

### Short-term (before GDC, now through Mar 4):
**Don't build MTM automation right now.** Reasons:
1. Chrome MCP is flaky on this machine (the "multiple extensions" error is a recurring problem)
2. The current manual workflow works — Katz scrapes, drops files, engine accumulates and scores
3. GDC is 3.5 weeks away. Building automation that might not work reliably is higher risk than the current manual process
4. The accumulation + scoring + notes pipeline is the real value-add right now

### Medium-term (after GDC, for future conferences):
**Build it as an R&D project with explicit scope:**
1. Read the SOP doc to confirm exact manual steps
2. Build a Chrome MCP-based MTM scraper as a standalone script
3. Test it against a live conference MTM instance (next PGC or similar)
4. If it works reliably, integrate into the scoring pipeline
5. If Chrome MCP remains flaky, assess Playwright/Puppeteer alternatives

### What to tell Katz:
**Honest framing:** "The scoring pipeline handles everything after you provide source files — accumulation, dedup, scoring, notes persistence, velocity tracking. Scraping itself is still manual. MTM scrape automation is on the R&D roadmap after GDC."

---

## Blocked On

- [ ] **Read the Conference Lead Targeting SOP doc** via Chrome MCP — need the exact manual MTM workflow steps to scope automation properly
- [ ] **Chrome MCP stability** — recurring "multiple extensions" connection issue needs resolution before building any Chrome-based automation
- [ ] **Zeb's sign-off** on the "don't automate MTM before GDC" recommendation

---

## What IS Automated (honest accounting)

| Component | Status | Details |
|-----------|--------|---------|
| Source accumulation | **Built** | `engine/accumulate.py` — dedup, merge, never drop people |
| Scoring | **Built** | `scorers/gdc_sf_26.py` — reads accum, scores all people |
| Notes persistence | **Built** | `engine/notes.py` — carry DK annotations across iterations |
| Sheet re-ingest | **Built** | `engine/accumulate.ingest_sheet_export()` — pull annotated Sheet back in |
| Velocity tracking | **Built** | `engine/velocity.py` — iteration-over-iteration metrics |
| MTM scraping | **Not built** | Manual — Katz scrapes MTM, drops file |
| LISN export | **Not built** | Manual — always will be (no API) |
| Google Sheets upload | **Not built** | Manual TSV import for now |
