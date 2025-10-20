# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Trump Analysis Pipeline**: A comprehensive data collection and analysis system combining financial market data (SPY/VXX) with Trump's Truth Social political content, using AI classification to identify trade/tariff discussions and correlate them with market movements.

**Key Goal**: Enable market-political analysis by combining institutional financial data with AI-powered political content analysis.

## Core Architecture

The project follows a **linear 3-stage pipeline**:

1. **Data Collection Phase** (`Data Collection and Cleaning/` directory)
   - Financial data scrapers (SPY, VXX from Interactive Brokers)
   - Web scraper for Trump's Truth Social posts
   - Raw data cleaning pipeline

2. **AI Analysis Phase**
   - Claude Sonnet 4.5 AI classification of posts for tariff/trade content
   - Batch processing with checkpoint/resume capability

3. **Analysis-Ready Output**
   - Cleaned financial datasets (Excel)
   - Classified political posts with detailed AI metadata
   - Ready for correlation analysis and visualization

### Data Flow

```
Interactive Brokers → SPY/VXX Data Files (.xlsx)
                 ↓
            Financial Data Ready

trumpstruth.org → Raw Posts (JSON/CSV)
                ↓
          clean_trump_archive.py → Cleaned Posts
                ↓
          tariff_classifier_optimized.py → AI Analysis → Results (JSON/CSV + checkpoint)
                ↓
          Analysis-Ready Data
```

## Critical Commands

### Financial Data Collection
```bash
# S&P 500 ETF (5-minute intervals, 1-year history)
python3 "Data Collection and Cleaning/SPY History.py"

# High-granularity SPY (1-minute intervals, recent month)
python3 "Data Collection and Cleaning/SPY History 1 Min.py"

# Volatility ETF (5-minute intervals, 1-year history)
python3 "Data Collection and Cleaning/VXX History.py"

# Requirements: Interactive Brokers account + TWS/Gateway running
# Output: _5min_history.xlsx or _1min_history.xlsx files in Data Collection and Cleaning/
```

### Truth Social Data Collection & Cleaning
```bash
# Scrape all Trump posts from trumpstruth.org (30-45 minutes)
python3 "Data Collection and Cleaning/trumpstruth_scraper_auto.py"
# Output: trump_truth_archive.json, trump_truth_archive.csv

# Clean scraped data (2-3 minutes)
python3 "Data Collection and Cleaning/clean_trump_archive.py"
# Input: trump_truth_archive.json
# Output: trump_truth_archive_clean.json, trump_truth_archive_clean.csv
```

### AI Tariff Classification
```bash
# Full analysis (~45-60 minutes, $7-10 API cost)
python3 "Data Collection and Cleaning/tariff_classifier_optimized.py" YOUR_ANTHROPIC_API_KEY

# Fast analysis with pre-filter (~5-10 minutes, $1-2 cost)
python3 "Data Collection and Cleaning/tariff_classifier_optimized.py" YOUR_ANTHROPIC_API_KEY --pre-filter

# Resume interrupted analysis (continues from checkpoint.json)
python3 "Data Collection and Cleaning/tariff_classifier_optimized.py" YOUR_ANTHROPIC_API_KEY --resume

# Output: tariff_classified_tweets.json, tariff_classified_tweets.csv, checkpoint.json, classification_log.txt
```

## Important Architectural Details

### AI Classification System (tariff_classifier_optimized.py)

**Input**: Clean CSV with columns: `post_id, content, date, timestamp, username`

**Processing Model**: Batch analysis (10 posts per API call)
- Reduces API costs and improves efficiency
- Uses checkpoint.json for resume capability
- Can interrupt and resume without losing progress

**Output Schema** (per classified post):
- `is_tariff_related`: Boolean
- `confidence`: 0-100 percentage
- `tariff_type`: China, Mexico, EU, BRICS, General, None
- `countries_mentioned`: List (e.g., ["China", "Mexico"])
- `tariff_percentage`: Specific rates (e.g., "100%", "25%")
- `sentiment`: Aggressive, Defensive, Informational, Neutral
- `key_phrases`: Trade-related language
- `explanation`: AI reasoning for classification

**Expected Results** (~2,562 posts):
- ~276 tariff-related (10.8%)
- China: 156 posts (56% of tariff posts)
- Aggressive tone: 89% of tariff discussions

### Financial Data Structure

**SPY/VXX Files** (Excel format, 5-minute intervals):
- Columns: Date, Time, Open, High, Low, Close, Volume
- Expected: 4,000-6,000 rows per year
- Used for: Correlation analysis with political events

### Data Quality Expectations

- **Financial Data**: Institutional quality from IBKR (100% accurate)
- **Scraped Posts**: 95%+ accuracy after cleaning (removing duplicates/navigation)
- **AI Classification**: 98%+ confidence (uses Claude Sonnet 4.5)

## Key Considerations

### API & External Dependencies

- **Interactive Brokers**: Required for financial data (TWS/Gateway must be running)
- **Anthropic API**: Required for AI classification (~$20/month adequate for full analysis)
- **trumpstruth.org**: Web scraper (respectful delays built-in, 2-3 seconds per page)

### Hardware Optimization

Your M4 Max Mac (128GB RAM) is well-suited for this project:
- Financial data: Minimal resources needed
- Scraping: Single-threaded, ~30-45 minutes
- AI classification: Sequential batch processing (network-bound, not CPU-bound)

**Note**: No parallelization is currently implemented or needed—network I/O is the bottleneck, not compute.

### File Management

- **Input data files**: Located in `Data Collection and Cleaning/`
- **Output files**: Generated in same directory (trump_truth_archive_clean.*, tariff_classified_tweets.*)
- **Checkpoint files**: checkpoint.json enables resuming interrupted AI analysis
- **Log files**: cleaning_log.txt, classification_log.txt track all processing

## Workflow Checklist

When modifying or extending this pipeline, ensure:

1. **Data Integrity**: Never delete intermediate files (checkpoint.json, archive files) without explicit user permission
2. **API Costs**: Pre-filter option reduces AI costs 80% (good for testing/development)
3. **Resume Capability**: Maintain checkpoint.json structure if modifying AI classification
4. **Logging**: All scripts write detailed logs (not just errors) for debugging
5. **File Formats**: 
   - Financial data: Always .xlsx (not CSV) for consistency
   - Post data: Both .json and .csv for flexibility
   - Ensure UTF-8 encoding for text data

## Data File Reference

| File | Purpose | Created By | Format | Size (~) |
|------|---------|-----------|--------|---------|
| `SPY_5min_history.xlsx` | Market data | SPY History.py | Excel | 1-2 MB |
| `VXX_5min_history.xlsx` | Volatility data | VXX History.py | Excel | 1-2 MB |
| `trump_truth_archive.json` | Raw posts | trumpstruth_scraper_auto.py | JSON | 10-15 MB |
| `trump_truth_archive_clean.json` | Cleaned posts | clean_trump_archive.py | JSON | 8-12 MB |
| `trump_truth_archive_clean.csv` | Cleaned posts | clean_trump_archive.py | CSV | 6-10 MB |
| `tariff_classified_tweets.json` | AI analysis | tariff_classifier_optimized.py | JSON | 15-20 MB |
| `tariff_classified_tweets.csv` | AI analysis | tariff_classifier_optimized.py | CSV | 10-15 MB |
| `checkpoint.json` | AI progress | tariff_classifier_optimized.py | JSON | <1 MB |

## Common Development Tasks

### To add a new financial data source (e.g., Russell 2000):
1. Copy structure from `SPY History.py` or `VXX History.py`
2. Modify ticker symbol and IBKR contract parameters
3. Ensure same .xlsx output format for consistency
4. Test with small data chunk before full extraction

### To modify AI classification criteria:
1. Edit the system prompt in `tariff_classifier_optimized.py` (AI behavior)
2. Update output schema if adding new fields
3. Test with `--pre-filter` flag first (cheaper)
4. Verify checkpoint.json remains compatible if changing structure

### To investigate data quality issues:
1. Check `cleaning_log.txt` for scraping/cleaning problems
2. Check `classification_log.txt` for AI processing errors
3. Review checkpoint.json for incomplete batches
4. Compare raw vs cleaned record counts

## MCP Servers Available

Per `.claude/settings.local.json`, the following MCP servers are enabled:
- `disk-search`: File searching capabilities
- `filesystem`: File read/write operations
- `codeservant`: Code analysis and formatting

## Dependencies

All Python scripts require:
```
ib_insync          # Interactive Brokers API
pandas             # Data manipulation
openpyxl           # Excel file handling
requests           # HTTP requests for scraping
beautifulsoup4     # HTML parsing
lxml               # XML parsing
tqdm               # Progress bars
```

Install with:
```bash
pip install ib_insync pandas openpyxl requests beautifulsoup4 lxml tqdm
```

For AI classification, also install:
```bash
pip install anthropic
```

## Debugging & Troubleshooting

**IBKR Connection Issues**: Ensure TWS or IB Gateway is running with API access enabled

**Scraper Failures**: Check website structure hasn't changed; might need to update selectors in BeautifulSoup parsing

**AI Classification Errors**: Check API key validity; verify input CSV has required columns; review classification_log.txt for specific failures

**Checkpoint Resume Fails**: Delete checkpoint.json and restart if file becomes corrupted; system will reprocess from beginning
