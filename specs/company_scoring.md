# Overview

This system scores potential client companies using three pillars (Budget, Alignment, Demand). 

For each pillar, the system combines weighted factors to calculate a pillar score (1-100), \*\*\*normalized across the pillar . This allows granular tuning of pillar components, while maintaining a consistent frame of reference across all scores, for filtering, prioritization, and automation.

The pillar scores are then combined, using a weighted average, and another normalization pass (across all available company scores), for the final **Company Score**.

Data completeness is inherently integrated into pillar scores – i.e. companies with more data typically score higher. But data quality (i.e. **Confidence**) is also provided separately as a tunable cut-off for filtering in prioritization.

\*\*\*Min-Max Normalization (0-to-100) takes the spread of a data set (i.e., the distance from min to max), and stretches all values in the set, such that the min becomes 0 and max becomes 100\. This ensures that proportional distances between values are preserved, including major outliers, while enforcing a consistent frame of reference.

*Example: For the data set 3, 4, 10, 13... normalized values \= 0, 10, 70, 100*

***Result:** The company with Alignment \= 100 will always have the best Alignment score in the data set (or be tied for it), and the company with Company Score \= 100 will always have the best weighted average across pillar scores, regardless of subcomponent tuning.*

### Pillar Definitions & Weights {#pillar-definitions-&-weights}

Company Score consists of the following pillars: 

1) **Alignment**: Their alignment with our offerings.  
2) **Budget**: Their ability to afford us.  
3) **Demand**: Apparent need for our services, or sales funnel status, and signal recency.

Pillar scores are averaged using these weights:

* **Budget**: 100  
* **Alignment**: 60  
* **Demand**: 40

#### [Company Profile Examples](https://docs.google.com/spreadsheets/d/1GrLI_-FGDz83GilIgHO0hsGDtkTud98EoZz26qoa0dI/edit?gid=680518103#gid=680518103)

# Score Components

Each pillar score is the sum of its components, normalized 0-to-100 across all company scores for that pillar. The pillars and their components are…

1. **Alignment** \= Dev \+ F2P \+ Mobile \+ Fresh  
2. **Budget** \= Revenue \+ Funding \+ Headcount  
3. **Demand** \= Customer \+ Met \+ Interested \+ Volatility \+ Hiring

*Up-to-date component scores and weights can be found in [“Company Score \- Components & Tuning”](https://docs.google.com/spreadsheets/d/1GrLI_-FGDz83GilIgHO0hsGDtkTud98EoZz26qoa0dI/edit?gid=1048715908#gid=1048715908).*

Alignment  
The company operates in our domain of expertise.

* **Dev** (10): Has games (live or in dev), scaled by portfolio size percentile rank.  
* **F2P** (8): Has free-to-play games (live or in dev), scaled by percent of portfolio.  
* **Mobile** (7): Has mobile games (live or in dev), scaled by percent of portfolio.  
* **Fresh** (5): Has fresh product (prelaunch, or launched \< 3M), scaled by portfolio %.

## Budget

The company can afford our services.

* **Revenue** (10): Estimated quarterly revenue, inferred as needed from other time frames and sources (e.g. monthly revenue, ad rev from installs, etc). Percentile rank of quarterly revenue across companies, multiplied as percent of max points available, to scale points given. *Ex: 1M DAU \= $400k/mo \= higher revenue than 80% of companies \= 8 points given.*  
* **Funding** (8): Total funding amount, all time. Percentile rank across companies multiplied as percent to scale points given. *Ex: $10M total funding \= more funding than 90% of companies \= 7.2 points given, out of 8 points.*  
* **Headcount** (5): Estimate of current employees count, as proxy for funding or revenue. Percentile rank across companies, applied as percent to scale points given. *Ex: 100 total employees \= more headcount than 40% of companies \= 2 points given, out of 5 points.*

## Demand

The company shows signals suggesting a need for our services, or has already progressed into our sales funnel.   
*(Total: 22\)*

* **Status** (10): Company has status in our sales funnel. Points given (up to max) based on their stage in the funnel. Each stage has a half-life.  
  * **Past Client** (10) – Previously had paid engagement. Number 6-8 in status. (2 year half-life)  
  * **Client** (8) – Currently on paid contract. Number 5 or 9 in status. (1 year half-life)  
  * **Met with Matt** (6) – They’ve met with Matt or the team for a demo. Matches status. (6 month half-life)  
  * **Qualified** (5) – They’ve met with Dan, and qualified for sales. Matches status. (3 month half-life)  
  * **Disco Incoming** (2) – They’re scheduling a kickoff call with Daniel. Matches status. (1 month half-life)  
* **Volatility** (7): High \= good. Combines three components to scale the total points awarded. Finds the company’s percentile rank for each component, averages the component ranks (weights defined below), then awards that percent of max points available. *Ex: AVG perc rank 60 \= 60% of 7 \= 4.2 of 7 points...*  
  * **Revenue ∆** (weight 5): Recent revenue dips. Negative change \= good. CALC: Percent revenue change from previous quarter to latest. *Ex: \-80% QoQ \= bigger revenue dip than 90% of companies.*  
  * **Runway ∆** (weight 4\) : Recency and size of latest funding (requires data for Latest Funding Amount and Latest Funding Date). Bigger and more recent \= better. CALC: Get the size of the latest funding, attenuated by the time since that funding, with an exponential half-life of 12 months. *Ex: $10M two years ago \= $2.5M now \= better runway than 70% of companies.*  
  * **Headcount ∆** (weight 3): Similar to Revenue Change, but with headcount (lay-offs \= they need help). CALC: Get headcount change % from previous quarter to latest. Ex:   
* **Hiring** (5, scaling): Recently announced senior product role opening(s). (Half-life 3 months)

## Blacklisting

A separate blacklist will be kept, listing companies which we shouldn’t contact further, along with the reason for blacklisting, and date they were blacklisted. The master Companies List will include these companies, but will have a filter column for clearly and simply filtering these companies from outreach, which will be engaged to filter by default in all views in systems.

# Data Confidence

The likelihood that a Company Score is accurate, given the availability and reliability of its scoring data. 

For each Company Score pillar (e.g. Budget, Alignment, Demand), the system multiplies Strength x Quality (as percentages 0-100), and normalizes each across the pillar (0-100). It then averages the pillar confidence scores for the company using [pillar weights](#pillar-definitions-&-weights) (defined above), and normalizes the average (1-100) across companies, to calculate **Confidence**.

1. **Strength**: The amount and agreement of corroborating data. CALC: The percentile rank of the number of data sources used for this pillar, multiplied by the inverse Mean Absolute Deviation (e.g. the average of data point deviations from the median) of this company’s data points. *Ex: 4 data sources for Demand \= more than 80% of companies; with data agreement (inverse MAD) of .7 x 80% \= Strength 56\.*  
2. **Quality**: The reliability of the data sources used in Strength (defined manually). Each source is given a reliability score 1-5. Scores are averaged, then normalized across all reliability scores for pillar (0-100). *Ex: Four Budget sources scored 3,5,5,2 AVG \= 3.75 reliability, normalized across companies \= 64\.*

### Example

Pillar confidence scores…  
**Budget** \= .90 x .73 \= 0.66 normalized \= 82 Pillar Confidence  
**Alignment** \= .82 x .45 (Strength x Quality) \= .37 normalized \= 60 Pillar Confidence  
**Demand** \= .32 x .50 \= 0.16 normalized \= 34 Pillar Confidence

**Confidence**: Pillar Confidence weighted average of 60, 82, 34 \= 59 Total Confidence.

## Blacklisting

A living blacklist table specifies companies who we shouldn’t engage further, along with the reason for blacklisting, and date they were blacklisted. COMPANY\_SCORES (defined below) will include these companies, but will have a filter column for clearly and simply filtering them from BD. The blacklist flag will be universal and obvious in all systems and UX used to prioritize and initiate outreach.

# Architecture

The required data objects and throughputs of this system will include:

1. **\[SOURCE\]\_COMPANY\_RAW\_DATA\_\[DATE UPDATED\]**: The raw data snapshots pulled from each lead generation and qualification source, structured for efficient and reliable throughput into subsequent stages. These will be periodically scraped, and stored as timestamped snapshots for version control.   
   Example: CRUNCHBASE\_RAW\_DATA\_2025-10-25

   1. **COMPANY\_SCORE\_SOURCES\_\[DATE UPDATED\]:** A JSON mapping each data source to its respective score component(s), defining the priority order for deciding which data source to use (in cases where multiple sources can inform a calculation), and the Data Quality score to give each data source in the Confidence calculation.   
      Pulled from [Company Score \- Data Sources](https://docs.google.com/spreadsheets/d/1GrLI_-FGDz83GilIgHO0hsGDtkTud98EoZz26qoa0dI/edit?gid=0#gid=0).

   2. **\[SOURCE\]\_SCHEMA\_\[DATE UPDATED\]:** A schema table with columns listing the fields, field data types, field examples, and field context/descriptions for each field in the respective source’s scraped data.

2. **COMPANY\_STAGING\_\[DATE UPDATED\]**: A coalesced table of all data sources in RAW\_DATA, with cleanup, dedupe, and processing to prepare the data for scoring calculations. The periodic scrape of new RAW\_DATA snapshots will trigger a search for data to add to \_STAGING – e.g. new company records, and new or changed fields to update for preexisting companies.

3. **COMPANY\_SCORES\_\[DATE UPDATED\]**: The human-readable, simplified output table of scored companies, with basic ID fields to help distinguish similar companies (e.g. Company Name, URL, Country), and all top-level scores (e.g. Budget, Alignment, Demand, Confidence, Company Score, and all component scores). Updates to \_STAGING will trigger recalculation and update of \_SCORES.

   1. **COMPANY\_SCORE\_TUNING\_\[DATE UPDATED\]:** A JSON containing the latest company scoring system variables, weights, and tuning values, to be used in scoring calculation.   
      Pulled from [Company Score \- Components & Tuning](https://docs.google.com/spreadsheets/d/1GrLI_-FGDz83GilIgHO0hsGDtkTud98EoZz26qoa0dI/edit?gid=1048715908#gid=1048715908).

*Note: All \[DATE UPDATED\] suffixes in YYYY-MM-DD format.*