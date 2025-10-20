# Product Requirements Document: Trump Tweet Market Impact Analysis

**Version:** 1.0  
**Created:** 2025-01-20  
**Author:** Droid AI  
**Status:** Draft

---

## 1. Overview & Purpose

### 1.1 Product Vision
Develop a quantitative analysis system to measure and evaluate the statistical relationship between Donald Trump's tariff-related tweets and subsequent S&P 500 (SPY) price movements across multiple time horizons.

### 1.2 Business Objective
Enable data-driven insights into political-market correlations by:
- Quantifying market reactions to tariff-related political communications
- Identifying patterns in pre-tweet and post-tweet market behavior
- Supporting investment strategy research with empirical evidence

### 1.3 Success Criteria
- Ability to analyze 276 tariff-related tweets against 46,986 5-minute market data points
- Calculate returns across multiple time windows (5min, 15min, 30min, 1hr, 4hr, 1day, 3day)
- Generate statistical significance measures for observed correlations
- Produce visualizations and reports suitable for research publication

---

## 2. Data Specification

### 2.1 Input Data Sources

#### Market Data (`SPY_5min_history.xlsx`)
- **Location:** `/Users/macbook2024/Library/CloudStorage/Dropbox/AAA Backup/A Working/Trump Tweet/SPY_5min_history.xlsx`
- **Format:** Excel (.xlsx)
- **Structure:**
  - `date`: Timestamp (datetime, UTC)
  - `open`, `high`, `low`, `close`: Price levels (float)
  - `volume`: Trading volume (integer)
- **Coverage:** 2024-10-24 to 2025-10-17 (46,986 bars)
- **Granularity:** 5-minute intervals
- **Trading Hours:** 24-hour futures data (includes pre-market/after-hours)

#### Tweet Data (`tariff_classified_tweets_full.json`)
- **Location:** `/Users/macbook2024/Library/CloudStorage/Dropbox/AAA Backup/A Working/Trump Tweet/Data Collection and Cleaning/tariff_classified_tweets_full.json`
- **Format:** JSON array (2,562 total tweets)
- **Key Fields:**
  - `post_id`: Unique identifier
  - `content`: Full tweet text
  - `date`: Date string (YYYY-MM-DD)
  - `created_at`: ISO timestamp (YYYY-MM-DDTHH:MM:SS)
  - `timestamp`: Human-readable timestamp
  - `is_tariff_related`: Boolean classifier
  - `confidence`: AI confidence score (0-100)
  - `tariff_type`: China, Mexico, EU, BRICS, General, None
  - `countries_mentioned`: Array of country names
  - `tariff_percentage`: Specific rate mentioned (e.g., "25%", "100%")
  - `sentiment`: Aggressive, Defensive, Informational, Neutral
  - `key_phrases`: Array of trade-related terms
  - `explanation`: AI reasoning for classification
- **Tariff Tweets:** 276 (10.8% of total)
- **Coverage:** 2025-01-01 to 2025-10-18

### 2.2 Data Alignment Constraints
- **Overlapping Period:** January 2025 to October 2025 (~10 months)
- **Timezone Handling:** All timestamps must be normalized to same timezone (UTC preferred)
- **Market Hours:** Consider filtering to regular trading hours (9:30 AM - 4:00 PM EST) vs 24-hour analysis
- **Weekend/Holiday Handling:** Market closed periods require special handling for return calculations

---

## 3. Functional Requirements

### 3.1 Data Preparation Pipeline

#### FR-1.1: Timestamp Alignment
**Priority:** High  
**Description:** Normalize all timestamps to UTC timezone and ensure consistent datetime parsing
- Parse tweet timestamps from `created_at` field (ISO format)
- Parse market timestamps from `date` column (Excel datetime)
- Convert both to UTC pandas datetime64 objects
- Handle missing or malformed timestamps with logging

#### FR-1.2: Tweet Filtering
**Priority:** High  
**Description:** Filter tweets to tariff-related subset for analysis
- Filter `is_tariff_related == true`
- Apply confidence threshold (configurable, default >= 80%)
- Optionally filter by `tariff_type` for sub-analyses (China vs Mexico, etc.)
- Log filtered tweet count and distributions

#### FR-1.3: Market Data Windowing
**Priority:** High  
**Description:** For each tariff tweet, extract relevant market data windows
- Pre-tweet windows: 1hr, 4hr, 1day before tweet timestamp
- Post-tweet windows: 5min, 15min, 30min, 1hr, 4hr, 1day, 3day after tweet
- Handle boundary cases (tweet occurs outside market hours, weekend tweets)

### 3.2 Return Calculation Engine

#### FR-2.1: Simple Return Calculation
**Priority:** High  
**Description:** Calculate percentage returns for each time window
```
Return = (Price_end - Price_start) / Price_start * 100
```
- Use `close` prices from market data
- Calculate for each pre/post window relative to tweet timestamp
- Handle cases where insufficient data exists for window (early/late in dataset)

#### FR-2.2: Baseline Return Comparison
**Priority:** Medium  
**Description:** Calculate benchmark returns for comparison
- Compute average SPY return for same time windows across non-tweet periods
- Calculate standard deviation of returns for each window size
- Enable z-score calculation: `(tweet_return - avg_return) / std_return`

#### FR-2.3: Cumulative Impact Measurement
**Priority:** Medium  
**Description:** Aggregate returns across multiple tweets
- Calculate mean/median returns for all tariff tweets at each time horizon
- Group by tweet characteristics: `tariff_type`, `sentiment`, `countries_mentioned`
- Support weighted averaging by confidence score

### 3.3 Statistical Analysis

#### FR-3.1: Significance Testing
**Priority:** High  
**Description:** Test whether observed returns differ from baseline
- T-test: Compare tweet-period returns vs non-tweet baseline
- Report p-values for each time horizon
- Calculate confidence intervals (95%)

#### FR-3.2: Correlation Analysis
**Priority:** Medium  
**Description:** Identify relationships between tweet features and market response
- Correlate confidence score with return magnitude
- Correlate sentiment (encoded numerically) with returns
- Analyze tariff_percentage mentions vs return size

#### FR-3.3: Event Study Methodology
**Priority:** Low  
**Description:** Apply formal event study framework
- Calculate abnormal returns (AR) = actual return - expected return
- Calculate cumulative abnormal returns (CAR) over multi-period windows
- Plot CAR charts for visualization

### 3.4 Output & Reporting

#### FR-4.1: Results Dataset
**Priority:** High  
**Description:** Generate structured output with one row per tweet-window combination
**Schema:**
```
- tweet_id
- tweet_timestamp
- tweet_content (truncated)
- tariff_type
- sentiment
- confidence
- window_type (pre_1hr, post_5min, post_1hr, etc.)
- window_start_time
- window_end_time
- price_start
- price_end
- return_pct
- baseline_return
- z_score
- n_bars (number of 5-min bars in window)
```
**Format:** CSV + JSON

#### FR-4.2: Summary Statistics
**Priority:** High  
**Description:** Aggregate analysis report
- Mean/median/std returns by time horizon
- Statistical significance results (p-values)
- Breakdown by tariff_type and sentiment
- Count of profitable vs unprofitable reactions
**Format:** JSON + Markdown report

#### FR-4.3: Visualizations
**Priority:** Medium  
**Description:** Generate charts for analysis
- Bar chart: Average returns by time horizon
- Heatmap: Returns by tariff_type x time horizon
- Scatter: Confidence score vs return magnitude
- Time series: Cumulative returns over study period
**Format:** PNG images (matplotlib/seaborn)

### 3.5 Configurable Parameters

#### FR-5.1: Analysis Configuration
**Priority:** Medium  
**Description:** Support parameterized execution via config file or CLI args
**Configurable Parameters:**
- Time horizons (default: 5min, 15min, 30min, 1hr, 4hr, 1day, 3day)
- Confidence threshold (default: 80)
- Market hours filter (on/off)
- Baseline calculation method (rolling average, all-period average)
- Statistical test type (t-test, Mann-Whitney, etc.)
- Output directory path

---

## 4. Non-Functional Requirements

### 4.1 Performance
- **NFR-1.1:** Analysis of 276 tweets x 10 time windows = 2,760 calculations should complete in < 5 minutes
- **NFR-1.2:** Memory usage should remain < 4GB (well within M4 Max 128GB capacity)
- **NFR-1.3:** Support incremental processing (add new tweets without full recomputation)

### 4.2 Accuracy & Reliability
- **NFR-2.1:** Return calculations must be accurate to 4 decimal places
- **NFR-2.2:** No data loss due to timestamp mismatches (log warnings for unmatched tweets)
- **NFR-2.3:** Graceful handling of missing data (weekends, holidays) with clear reporting

### 4.3 Usability
- **NFR-3.1:** Single-command execution with sensible defaults
- **NFR-3.2:** Progress bars for long-running operations (via tqdm)
- **NFR-3.3:** Detailed logging to file with timestamps and operation context

### 4.4 Reproducibility
- **NFR-4.1:** Analysis must be deterministic (same inputs → same outputs)
- **NFR-4.2:** Log all configuration parameters to output directory
- **NFR-4.3:** Version control integration (git-friendly output formats)

### 4.5 Extensibility
- **NFR-5.1:** Modular design to support additional data sources (VXX volatility data)
- **NFR-5.2:** Pluggable return calculation methods (log returns, risk-adjusted returns)
- **NFR-5.3:** Easy addition of new statistical tests or grouping dimensions

---

## 5. System Architecture

### 5.1 Component Design

```
┌─────────────────────────────────────────────────────────┐
│                  Main Analysis Script                    │
│              tweet_market_impact_analyzer.py             │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌─────────────┐ ┌─────────────┐
│ Data Loader  │ │   Return    │ │  Statistical │
│   Module     │ │  Calculator │ │    Engine    │
└──────────────┘ └─────────────┘ └─────────────┘
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌─────────────┐ ┌─────────────┐
│   Market     │ │   Window    │ │   Report     │
│   Aligner    │ │   Extractor │ │  Generator   │
└──────────────┘ └─────────────┘ └─────────────┘
```

### 5.2 Module Responsibilities

**Data Loader Module:**
- Read Excel market data → pandas DataFrame
- Read JSON tweet data → list of dicts
- Validate schema and data types
- Handle encoding issues (UTF-8)

**Market Aligner:**
- Normalize timestamps to UTC
- Merge/align tweet timestamps with market bars
- Implement market hours filtering logic

**Window Extractor:**
- For given tweet timestamp, extract price data for each pre/post window
- Handle edge cases (insufficient data, market closures)
- Return structured window data

**Return Calculator:**
- Compute simple percentage returns
- Compute baseline returns from non-tweet periods
- Calculate z-scores and abnormal returns

**Statistical Engine:**
- Run significance tests (t-tests, etc.)
- Calculate correlation matrices
- Aggregate statistics by groupings

**Report Generator:**
- Create CSV/JSON output files
- Generate summary markdown report
- Produce matplotlib visualizations
- Save configuration metadata

### 5.3 Data Flow

```
SPY_5min_history.xlsx ──────┐
                             ├──> Data Loader ──> Market Aligner
tariff_classified_tweets.json┘              │
                                             ▼
                             Configuration ──> Window Extractor ──> Return Calculator
                                                                         │
                                                                         ▼
                                                     Statistical Engine <─┘
                                                                         │
                                                                         ▼
                                                     ┌──────────────────────────┐
                                                     │   Output Directory       │
                                                     ├──────────────────────────┤
                                                     │ - results.csv            │
                                                     │ - summary_stats.json     │
                                                     │ - report.md              │
                                                     │ - returns_by_horizon.png │
                                                     │ - config_log.json        │
                                                     └──────────────────────────┘
```

---

## 6. Implementation Approach

### 6.1 Technology Stack
- **Language:** Python 3.12
- **Data Manipulation:** pandas (DataFrame operations)
- **Statistical Analysis:** scipy.stats (t-tests, correlations)
- **Visualization:** matplotlib, seaborn
- **Time Handling:** pandas datetime, pytz (timezone conversions)
- **CLI/Progress:** argparse, tqdm
- **File I/O:** pandas (read_excel, to_csv), json module

### 6.2 Development Phases

**Phase 1: Data Loading & Validation (Week 1)**
- Implement data loader module
- Write unit tests for timestamp parsing
- Validate data integrity (no missing critical fields)
- Output: Loaded data structures ready for analysis

**Phase 2: Window Extraction & Return Calculation (Week 1-2)**
- Build market aligner and window extractor
- Implement simple return calculator
- Test edge cases (weekends, market gaps)
- Output: Return calculation engine working for single tweet

**Phase 3: Statistical Analysis (Week 2)**
- Implement baseline return calculation
- Add significance testing (t-test)
- Build aggregation logic (group by tariff_type, sentiment)
- Output: Statistical engine producing p-values and confidence intervals

**Phase 4: Reporting & Visualization (Week 2-3)**
- Generate CSV/JSON outputs
- Create markdown summary report
- Build matplotlib charts
- Output: Complete analysis report package

**Phase 5: Configuration & Polish (Week 3)**
- Add CLI argument parsing
- Implement config file support (YAML or JSON)
- Add comprehensive logging
- Write user documentation
- Output: Production-ready analysis script

### 6.3 Coding Standards
- Follow PEP 8 style guidelines
- Use type hints (Python 3.12+ syntax)
- Document functions with docstrings (Google style)
- Maintain test coverage > 80% for core calculation logic
- Use descriptive variable names (no abbreviations in business logic)

---

## 7. Testing Strategy

### 7.1 Unit Tests
**Coverage:** Individual functions in each module
- **Data Loader:** Test Excel/JSON parsing with sample files
- **Return Calculator:** Test return formula with known inputs
- **Window Extractor:** Test boundary conditions (no data, partial data)
- **Statistical Engine:** Test t-test with synthetic data

**Framework:** pytest  
**Target:** > 80% code coverage

### 7.2 Integration Tests
**Coverage:** End-to-end scenarios
- Load real data → calculate returns → generate outputs
- Test with subset of tweets (10 tweets) for fast validation
- Verify output files exist and contain expected structure

**Framework:** pytest  
**Runtime:** < 30 seconds per test

### 7.3 Validation Tests
**Coverage:** Result accuracy
- **Known Event Test:** Manually identify a high-confidence tariff tweet with obvious market reaction, verify analysis captures it
- **Baseline Sanity Check:** Verify baseline returns match manual calculation in Excel
- **Statistical Validation:** Compare p-values from script vs manual calculation in R/Excel

### 7.4 Performance Tests
**Coverage:** Execution time and memory
- Benchmark full analysis (276 tweets) on M4 Max
- Monitor memory usage with tracemalloc
- Target: < 5 minutes total runtime, < 4GB RAM

### 7.5 Manual Testing Checklist
- [ ] Run analysis with default parameters
- [ ] Run with different confidence thresholds (70, 80, 90)
- [ ] Run with market hours filter on/off
- [ ] Verify all output files created
- [ ] Inspect visualizations for correctness
- [ ] Review summary statistics for reasonableness

---

## 8. Acceptance Criteria

### 8.1 Functional Acceptance
- [ ] System processes all 276 tariff tweets without errors
- [ ] Returns calculated for all specified time horizons (5min to 3day)
- [ ] Statistical significance (p-values) reported for each horizon
- [ ] Output CSV contains one row per tweet-window combination
- [ ] Summary report includes mean/median returns and significance results
- [ ] Visualizations generated: returns by horizon, heatmap by tariff type

### 8.2 Quality Acceptance
- [ ] No data loss: All tweets with overlapping market data analyzed
- [ ] Accuracy: Manual validation of 5 random tweets matches script output
- [ ] Logging: All operations logged with timestamps and clear messages
- [ ] Error Handling: Graceful failure with informative error messages

### 8.3 Usability Acceptance
- [ ] Single command execution with default parameters works
- [ ] Progress bar shows during long operations
- [ ] README documentation explains how to run analysis
- [ ] Configuration options documented in help message (`--help`)

### 8.4 Performance Acceptance
- [ ] Full analysis completes in < 5 minutes on M4 Max
- [ ] Memory usage stays < 4GB
- [ ] No memory leaks (repeated runs use same memory)

---

## 9. Risk Assessment

### 9.1 Data Quality Risks
**Risk:** Timestamp mismatches between tweets and market data  
**Mitigation:** Implement fuzzy matching (nearest 5-min bar), log all matches  
**Severity:** Medium

**Risk:** Market data gaps (holidays, technical issues)  
**Mitigation:** Detect gaps, exclude affected windows, report in summary  
**Severity:** Low

### 9.2 Statistical Risks
**Risk:** Multiple testing problem (testing 10+ hypotheses inflates false positives)  
**Mitigation:** Apply Bonferroni correction, report adjusted p-values  
**Severity:** Medium

**Risk:** Insufficient sample size for sub-group analysis (e.g., BRICS tweets)  
**Mitigation:** Report sample size for each group, flag low-N results  
**Severity:** Low

### 9.3 Implementation Risks
**Risk:** Complex timezone handling leads to off-by-one errors  
**Mitigation:** Extensive unit tests for timestamp alignment, manual validation  
**Severity:** High

**Risk:** Memory issues with large datasets if architecture changes  
**Mitigation:** Profile memory usage, use chunking if needed  
**Severity:** Low

---

## 10. Future Enhancements

### 10.1 Phase 2 Features (Post-MVP)
- **Volatility Analysis:** Integrate VXX data to measure volatility spikes
- **Intraday Patterns:** Analyze if tweet timing (morning vs afternoon) matters
- **Volume Analysis:** Correlate trading volume changes with tweet events
- **Machine Learning:** Train model to predict market reaction from tweet features

### 10.2 Advanced Analytics
- **Regime Detection:** Identify periods where tweet impact changes (election cycle, policy shifts)
- **Sentiment Refinement:** Use NLP to extract more granular sentiment scores
- **Cross-Asset Analysis:** Extend to other ETFs (QQQ, IWM, sector ETFs)
- **Real-Time Monitoring:** Stream live tweets and market data for alerts

### 10.3 UX Improvements
- **Interactive Dashboard:** Web UI (Streamlit/Dash) for exploring results
- **Auto-Update:** Scheduled runs to incorporate new tweets/market data
- **Alert System:** Notify when high-confidence tariff tweet detected

---

## 11. Dependencies & Constraints

### 11.1 External Dependencies
- **Data Files:** Requires up-to-date SPY market data and classified tweets
- **Python Packages:** pandas, openpyxl, scipy, matplotlib, seaborn, tqdm
- **Hardware:** Analysis designed for M4 Max but should run on any modern machine

### 11.2 Assumptions
- Tweet timestamps are accurate (scraped correctly)
- Market data is clean (no erroneous prices)
- 5-minute granularity sufficient for analysis (not tick-level)
- SPY is appropriate proxy for market reaction (S&P 500 most relevant)

### 11.3 Constraints
- **Historical Data Only:** No real-time data integration in MVP
- **Single Asset:** Only SPY analyzed (VXX postponed to Phase 2)
- **Linear Analysis:** No machine learning or predictive modeling in MVP

---

## 12. Success Metrics

### 12.1 Technical Metrics
- **Execution Time:** < 5 minutes for full analysis
- **Test Coverage:** > 80% code coverage
- **Error Rate:** < 1% of tweets fail processing

### 12.2 Business Metrics
- **Insight Generation:** Identify at least 3 statistically significant patterns
- **Reproducibility:** 100% reproducible results across runs
- **Usability:** Non-technical user can run analysis with < 5 minutes training

### 12.3 Research Metrics
- **Statistical Power:** Sufficient sample size to detect 0.5% return difference
- **Publication Quality:** Results formatted suitable for academic/industry report
- **Credibility:** Analysis methodology defensible to financial professionals

---

## Appendix A: Example Output Structure

### A.1 Results CSV Schema
```csv
tweet_id,tweet_timestamp,tweet_content,tariff_type,sentiment,confidence,window_type,window_start,window_end,price_start,price_end,return_pct,baseline_return,z_score,n_bars
2025-01-07_9,2025-01-07T10:45:00,Many people in Canada...,General,Informational,85,post_5min,2025-01-07T10:45:00,2025-01-07T10:50:00,580.25,580.31,0.0103,-0.0012,1.8,1
2025-01-07_9,2025-01-07T10:45:00,Many people in Canada...,General,Informational,85,post_1hr,2025-01-07T10:45:00,2025-01-07T11:45:00,580.25,581.05,0.1378,0.0234,2.1,12
...
```

### A.2 Summary Statistics JSON
```json
{
  "analysis_date": "2025-01-20",
  "total_tweets": 276,
  "date_range": "2025-01-07 to 2025-10-18",
  "time_horizons": ["post_5min", "post_15min", "post_30min", "post_1hr", "post_4hr", "post_1day", "post_3day"],
  "returns_by_horizon": {
    "post_5min": {"mean": 0.012, "median": 0.008, "std": 0.045, "p_value": 0.23},
    "post_1hr": {"mean": 0.034, "median": 0.025, "std": 0.12, "p_value": 0.08},
    "post_1day": {"mean": -0.15, "median": -0.11, "std": 0.67, "p_value": 0.04}
  },
  "by_tariff_type": {
    "China": {"count": 156, "mean_return_1hr": 0.045, "p_value": 0.02},
    "Mexico": {"count": 48, "mean_return_1hr": -0.023, "p_value": 0.31}
  }
}
```

### A.3 Markdown Report Excerpt
```markdown
# Tweet Market Impact Analysis Report

**Analysis Date:** 2025-01-20  
**Tweet Period:** 2025-01-07 to 2025-10-18  
**Total Tweets Analyzed:** 276 tariff-related tweets  

## Key Findings

1. **Short-Term Impact (5-minute):** No statistically significant market reaction (p=0.23)
2. **Medium-Term Impact (1-hour):** Marginal positive reaction, mean return +0.034% (p=0.08)
3. **Daily Impact (1-day):** Significant negative reaction, mean return -0.15% (p=0.04) **SIGNIFICANT**

## Returns by Time Horizon

| Horizon | Mean Return | Median Return | Std Dev | P-Value | Significant |
|---------|-------------|---------------|---------|---------|-------------|
| 5 min   | 0.012%      | 0.008%        | 0.045%  | 0.23    | No          |
| 1 hour  | 0.034%      | 0.025%        | 0.12%   | 0.08    | Marginal    |
| 1 day   | -0.15%      | -0.11%        | 0.67%   | 0.04    | **Yes**     |

## Breakdown by Tariff Type

**China Tariff Tweets (n=156):**
- 1-hour return: +0.045% (p=0.02) **SIGNIFICANT**
- Interpretation: Market initially rallies on China tariff news

**Mexico Tariff Tweets (n=48):**
- 1-hour return: -0.023% (p=0.31)
- Interpretation: No significant reaction to Mexico tariff announcements
```

---

## Appendix B: CLI Usage Examples

```bash
# Basic analysis with defaults
python3 tweet_market_impact_analyzer.py

# Custom confidence threshold and output directory
python3 tweet_market_impact_analyzer.py --confidence 85 --output results_20250120/

# Filter to regular market hours only
python3 tweet_market_impact_analyzer.py --market-hours-only

# Analyze only China tariff tweets
python3 tweet_market_impact_analyzer.py --tariff-type China

# Custom time horizons
python3 tweet_market_impact_analyzer.py --horizons 5min 30min 2hr 1day

# Verbose logging
python3 tweet_market_impact_analyzer.py --verbose

# Configuration file mode
python3 tweet_market_impact_analyzer.py --config analysis_config.yaml
```

---

**End of PRD**
