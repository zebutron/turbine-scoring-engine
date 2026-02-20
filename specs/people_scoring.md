# Overview

Lead Score is used to prioritize outreach to contacts at potential client companies. Each Company is a potential client, and each of their Employees (our contacts) is a potential path to that sale. Overall lead strength is essentially a Company Score, attenuated by the contact’s usefulness in facilitating the sale. 

The system calculates normalized scores for each **Pillar** (0-100)**,** then averages them (weighted) into a **Contact Score**. It then attempts to match the person to a scored company, and multiplies Contact Score (as a percentage) against the matched [Company Score](https://docs.google.com/document/d/1Ak3rl0MBRyRSyDcf2kSJhHbUVzJFnO1p4sZOWCKHJu4/edit?tab=t.0) for an overall **Lead Score** (0-100), and normalizes that across People.

*If no company match exists, or contact has no company listed, their Contact Score is used as Lead Score, with a \-70% penalty.*

*If contact has no job title, but has a matchable Company, their Company Score is used as Lead Score, with a \-40% penalty.*

### Pillars & Weights

A person’s Contact Score is calculated using the following pillars: 

1) **Seniority**: Their ability to influence a decision to hire us.  
2) **Domain**: The relevance of their job domain to our offerings.  
3) **Warmth**: The recency of their interactions with our BD (outreach or social media).  
   

Pillar scores are averaged using these weights… 

* **Seniority**: 100  
* **Domain**: 70  
* **Warmth**: 50

### Scoring Example

**Seniority** \= 76  
**Domain** \= 90  
**Warmth** \= 32

**Contact** Score \= 70  
Matched **Company** Score \= 92  
**Lead Score** \= 70% of 92 \= 64

# Score Components

Seniority and Domain scoring both attempt to assign scores by string matching keywords to a contact’s job title. Together, they attempt to identify and score all potentially interesting job titles, as accurately and exhaustively as possible.

Specific edge case job titles – which either aren’t identified by the keyword system, or deserve special scoring treatment – have score overrides defined in the One-Offs section.

## Seniority

The contact’s decision-making authority and influence.

Examples (all up-to-date values live in [“People Score \- Components & Tuning”](https://docs.google.com/spreadsheets/d/1GrLI_-FGDz83GilIgHO0hsGDtkTud98EoZz26qoa0dI/edit?gid=1791309685#gid=1791309685)):

* CEO \=	100  
* VP \= 80  
* Director \= 70

## Domain

The relevance of the contact’s role domain to our BD efforts.

***Note: Owner/Founder/CEO roles converge to 100 across both Domain and Seniority.***

Examples:

* CEO \= 100  
* Product \= 95  
* Publishing \= 70

## One-Offs

Job titles with an exact match will receive the respective overrides to both Seniority and Domain scores.

Examples:

* Head of Studio, Studio Director, Studio Lead, General Manager \= 90  
* Executive Producer \= 80  
* Product Owner, Product Lead \= 70

## Warmth

Recency of any positive contact, either via outreach or social media. Calculated by summing the points contributed by each vector (each scaled by applying a specific half-life, based on signal recency), and then normalizing across people (0-100).

* **Response** (7): Responded positively to outreach, or contacted Turbine. (Half-life 6 months)  
* **Engaged** (5): Engaged positively with social media content, i.e. Linkedin Post. (Half-life 3 months)

## Company Matching

A person’s Lead Score is a combination of their Contact Score (Seniority, Domain, Warmth) and the Company Score of their employer. To find Company Score, the system attempts to match each contact to a company, using fuzzy string matching against normalized company names.

This matching ensures…

* **High confidence thresholds**: Minimum 90% similarity required.  
* **Match confidence** exact value provided in output, for filtering and prioritization.

## Blacklisting

A living blacklist table specifies people who we shouldn’t contact further, along with the reason for blacklisting, and date they were blacklisted. PEOPLE\_SCORES (defined below) will include these people, but will have a filter column for clearly and simply filtering them from outreach if the person or their company is blacklisted. The blacklist flag will be universal and obvious in all systems and UX used to prioritize and initiate outreach.

# Architecture

The required data objects and throughputs of this system will include:

1. **\[SOURCE\]\_PEOPLE\_RAW\_DATA\_\[DATE UPDATED\]:** The raw data snapshots pulled from each lead generation and qualification source, structured for efficient and reliable throughput into subsequent stages. These will be periodically scraped, and stored as timestamped snapshots for version control.   
   Example: LISN\_RAW\_DATA\_2025-10-25

   1. **\[SOURCE\]\_SCHEMA\_\[DATE UPDATED\]:** A schema table with columns listing the fields, field data types, field examples, and field context/descriptions for each field in the respective source’s scraped data.

2. **PEOPLE\_STAGING\_\[DATE UPDATED\]:** A coalesced table of all data sources in RAW\_DATA, with cleanup, dedupe, and processing to prepare the data for scoring calculations. Also includes fields showing outputs from dedupe and cleanup steps, for manual checks (e.g. matched\_company, match\_confidence). The periodic scrape of new RAW\_DATA snapshots will trigger a search for data to add to \_STAGING – e.g. new people records, and new or changed fields to update for preexisting people.

3. **PEOPLE\_SCORES\_\[DATE UPDATED\]:** The human-readable, simplified output table of scored people, with basic ID fields to help distinguish similar people (e.g. First Name, Last, Job, Company), and all top-level scores (e.g. Domain, Seniority, Warmth, and Lead Score). Updates to \_STAGING will trigger recalculation and update of \_SCORES.

   1. **PEOPLE\_SCORE\_TUNING\_\[DATE UPDATED\]:** A JSON containing the latest company scoring system variables, weights, and tuning values, to be used in scoring calculation.   
      Pulled from [Company Score \- Components & Tuning](https://docs.google.com/spreadsheets/d/1GrLI_-FGDz83GilIgHO0hsGDtkTud98EoZz26qoa0dI/edit?gid=1048715908#gid=1048715908).

*Note: All \[DATE UPDATED\] suffixes in YYYY-MM-DD format.*