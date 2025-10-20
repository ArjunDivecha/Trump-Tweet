# Trump Tariff Tweets Event Study - Methodology & Analysis Plan

## Research Hypothesis

**Main Thesis**: Trump's tariff-related tweets cause immediate negative market reactions (SPY falls, VXX/volatility spikes), but these effects revert within a few days, creating profitable "buy the dip" opportunities.

**Testable Predictions**:
1. **Immediate Impact** (T+0 to T+1): Tariff tweets → SPY declines, VXX increases
2. **Reversion Pattern** (T+2 to T+5): Returns normalize/reverse, volatility declines
3. **Sentiment Matters**: Aggressive tweets have stronger initial reactions than Informational/Defensive
4. **Trading Strategy**: Buying SPY immediately after aggressive tariff tweets and holding 3-5 days generates positive abnormal returns

---

## Data Sources

### 1. Market Data
- **SPY (S&P 500 ETF)**: 5-minute interval price data
  - File: `SPY_5min_history.xlsx`
  - Columns: Date, Time, Open, High, Low, Close, Volume
  - Expected: ~4,000-6,000 rows covering 2024-2025

- **VXX (Volatility ETF)**: 5-minute interval price data
  - File: `Data Collection and Cleaning/VXX_5min_history.xlsx`
  - Same structure as SPY

### 2. Political Events
- **Trump Tariff Tweets**: AI-classified Truth Social posts
  - File: `Data Collection and Cleaning/tariff_classified_tweets_full.json`
  - Total tweets: 2,562
  - Tariff-related: 276 tweets (10.8%)
  - Key fields:
    - `is_tariff_related`: Boolean filter
    - `sentiment`: Aggressive, Defensive, Informational, Neutral
    - `confidence`: AI classification confidence (0-100)
    - `created_at`: Timestamp (e.g., "2025-01-07T10:45:00")
    - `tariff_type`: China, Mexico, BRICS, General, etc.
    - `countries_mentioned`: List of countries

---

## Event Study Methodology

### Event Definition
- **Event = Tariff-related tweet** (`is_tariff_related == true`)
- **Event Time (T=0)**: Timestamp of tweet publication
- **Confidence Filter**: ALL tweets included (no minimum threshold)
- **Overlapping Events**: All events retained even if within 10 days of each other

### Event Windows
We'll analyze multiple time horizons:

| Window | Description | Purpose |
|--------|-------------|---------|
| **Intraday** | T+0: 0-30 min, 30-60 min, 1-2 hours, 3-6 hours | Immediate market reaction |
| **Short-term** | T+1, T+2, T+3 | Initial reaction period |
| **Reversion Test** | T+4, T+5, T+6, T+7 | Test mean reversion hypothesis |
| **Extended** | T+8, T+9, T+10 | Longer-term effects |
| **Pre-event** | T-1 | Baseline/control |

### Abnormal Return Calculation

**Method: Prior-Day Adjusted Returns**

```
Abnormal Return (AR) = Actual Return - Baseline Return
Baseline Return = Average intraday return from T-1 (previous trading day)
```

**For each event window:**
1. Calculate SPY 5-minute returns: `(Price_t - Price_t-1) / Price_t-1`
2. Calculate baseline: Mean of all 5-minute returns from T-1 (full previous trading day)
3. Abnormal return: `AR = Actual - Baseline`

**Cumulative Abnormal Return (CAR)**:
```
CAR[0,10] = Sum of AR from T+0 to T+10
```

**Intraday Analysis**:
- Track 5-minute returns for first 6 hours after tweet
- Aggregate into 30-min, 1-hour, 2-hour, 6-hour windows
- Compare to T-1 baseline for same time-of-day

### Volatility Analysis (VXX)

**Metrics**:
1. **Level Change**: `(VXX_t - VXX_t-1) / VXX_t-1`
2. **Abnormal Volatility**: VXX return vs. baseline
3. **Volatility Spike**: Count of times VXX increases >2 std deviations

---

## Trading Strategy Simulation

### Strategy: "Buy the Tariff Dip"

**Core Hypothesis**: Tariff tweets create temporary market overreaction, allowing profitable mean reversion trades.

**Trading Rules**:
1. **Entry Signal**: Tariff-related tweet detected
2. **Entry Timing**: Buy SPY at close of T+0 (or next open if after-hours tweet)
3. **Position Size**: Fixed $10,000 per trade (for standardization)
4. **Exit Timing**: Multiple exit scenarios tested:
   - T+3 (3 trading days)
   - T+5 (5 trading days)
   - T+10 (10 trading days)
5. **Transaction Costs**: $0 (assumes institutional/high-frequency trader with negligible costs)

**P&L Calculation**:
```
Entry Price = SPY close at T+0
Exit Price = SPY close at T+N (where N = 3, 5, or 10)
Return = (Exit Price - Entry Price) / Entry Price
P&L per Trade = $10,000 × Return
```

### Control Group: Random Non-Tariff Events

**Purpose**: Test if profits are specific to tariff tweets or just general market mean reversion

**Control Group Design**:
1. **Sample Size**: Match tariff group (276 random timestamps)
2. **Sampling Method**: Random timestamps from same date range as tariff tweets
3. **Exclusion Criteria**:
   - Exclude dates within ±3 days of any tariff tweet
   - Exclude dates within ±3 days of FOMC meetings, major earnings, or known events
4. **Same Strategy**: Apply identical entry/exit rules to control events

**Control Matching**:
- Match by time-of-day distribution (e.g., if 40% of tariff tweets are morning, 40% of control is morning)
- Match by day-of-week distribution
- Match by market regime (same volatility quintile as tariff tweet)

### Performance Metrics

**For Both Tariff and Control Groups**:
1. **Total Return**: Sum of all P&L
2. **Win Rate**: % of trades with positive returns
3. **Average P&L per Trade**: Mean return across all trades
4. **Median P&L per Trade**: Robust to outliers
5. **Sharpe Ratio**: Risk-adjusted return (mean return / std dev of returns)
6. **Maximum Drawdown**: Largest cumulative loss
7. **Best/Worst Single Trade**: Range of outcomes

**Comparative Tests**:
- **T-test**: Is mean P&L(Tariff) > mean P&L(Control)?
- **Sign Test**: Is win rate(Tariff) > win rate(Control)?
- **Cumulative P&L Chart**: Track cumulative profits over time for both groups

### Segmented Strategy Performance

Test if certain tariff tweet characteristics predict higher returns:

| Segment | Hypothesis |
|---------|------------|
| **Aggressive Sentiment** | Higher initial drop → better reversion profits |
| **High Confidence (>90%)** | Stronger signal → better performance |
| **China Tariffs** | Largest economy → biggest market reaction |
| **Specific Percentages** | Concrete threats → more credible → stronger reaction |
| **Market Hours** | Immediate reaction vs. overnight processing |

**Expected Result**: If thesis is correct, tariff group should significantly outperform control group, especially for aggressive/high-confidence tweets.

---

## Segmentation & Cross-Sectional Analysis

### Primary Segmentation: Sentiment
| Sentiment | Expected Impact | Sample Size (~) |
|-----------|----------------|-----------------|
| **Aggressive** | Strongest negative reaction | ~89% of tariff tweets |
| **Defensive** | Moderate reaction | ~5% |
| **Informational** | Weak/no reaction | ~6% |

### Secondary Segmentation
1. **Tariff Type**: China vs. Mexico vs. BRICS vs. General
2. **Confidence Level**: High (95-100%) vs. Medium (80-94%)
3. **Time of Day**: Market hours (9:30am-4pm ET) vs. After hours
4. **Specific Percentages**: Tweets mentioning "25%", "100%", etc.

---

## Testing the Directional Hypothesis

### Your Thesis: "Fall then Recover"
**Prediction**: Tariff tweets cause an initial market drop followed by mean reversion, creating profit opportunities.

**Specific Directional Predictions to Test**:

| Phase | Time Window | SPY Direction | VXX Direction | Test |
|-------|-------------|---------------|---------------|------|
| **Immediate Shock** | T+0: 0-30 min | ⬇️ FALL | ⬆️ SPIKE | AR_30min < 0 & VXX Δ > 0 |
| **Intraday Decline** | T+0: 0-2 hours | ⬇️ FALL | ⬆️ ELEVATED | AR_2hr < 0 |
| **Same Day Effect** | T+0: Full day close | ⬇️ FALL | ⬆️ ELEVATED | CAR[0] < 0 |
| **Next Day** | T+1 | ⬇️ or ↔️ | ⬆️ or ↔️ | CAR[0,1] < 0 |
| **Reversion Phase** | T+2 to T+5 | ⬆️ RECOVER | ⬇️ NORMALIZE | CAR[2,5] > 0 |
| **Extended** | T+6 to T+10 | ↔️ STABLE | ↔️ NORMAL | CAR[6,10] ≈ 0 |
| **Net Effect** | T+0 to T+10 | ⬆️ FULL REVERT | ⬇️ REVERT | CAR[0,10] > CAR[0,1] |

### Directional Tests (Tariff Events vs Control Events)

#### Test 1A: Immediate Intraday Drop (0-30 minutes)
**Hypothesis**: SPY falls within first 30 minutes after tariff tweets
- **Metric**: Mean AR_30min (0 to 30 minutes post-tweet)
- **Expected**: AR_30min < 0 for tariff group
- **Test**: One-sided t-test H0: AR_30min >= 0 vs H1: AR_30min < 0
- **Benchmark**: Control group should show AR_30min ≈ 0

#### Test 1B: Extended Intraday Drop (0-2 hours)
**Hypothesis**: SPY continues falling through first 2 hours
- **Metric**: Mean AR_2hr (cumulative 0 to 2 hours)
- **Expected**: AR_2hr < 0 for tariff group
- **Test**: One-sided t-test H0: AR_2hr >= 0 vs H1: AR_2hr < 0
- **Comparison**: Is |AR_2hr| > |AR_30min|? (continued decline)

#### Test 1C: Same-Day Close Effect
**Hypothesis**: SPY closes lower on day of tweet
- **Metric**: Mean CAR[0] (close-to-close return on T+0)
- **Expected**: CAR[0] < 0 for tariff group
- **Test**: One-sided t-test H0: CAR[0] >= 0 vs H1: CAR[0] < 0
- **Benchmark**: Control group should show CAR[0] ≈ 0

#### Test 2: Volatility Spike (Intraday)
**Hypothesis**: VXX spikes immediately after tariff tweets
- **Metric**: VXX return at T+0 (same day)
- **Expected**: VXX[0] > 0 for tariff group
- **Test**: One-sided t-test H0: VXX[0] <= 0 vs H1: VXX[0] > 0
- **Frequency**: % of events with VXX spike >1 std dev
- **Intraday**: Track VXX at 30min, 1hr, 2hr intervals

#### Test 3: Next-Day Persistence
**Hypothesis**: Decline persists into next trading day
- **Metric**: CAR[0,1] (cumulative 2-day return)
- **Expected**: CAR[0,1] < 0 for tariff group
- **Test**: One-sided t-test H0: CAR[0,1] >= 0 vs H1: CAR[0,1] < 0
- **Comparison**: Is CAR[0,1] more negative than CAR[0]?

#### Test 4: Mean Reversion (Days 2-5)
**Hypothesis**: Market recovers from T+2 to T+5
- **Metric**: CAR[2,5] (cumulative return days 2-5)
- **Expected**: CAR[2,5] > 0 for tariff group
- **Test**: One-sided t-test H0: CAR[2,5] <= 0 vs H1: CAR[2,5] > 0
- **Strength**: Is CAR[2,5] large enough to offset CAR[0,1]?

#### Test 5: Full Pattern Confirmation
**Hypothesis**: The complete "fall then recover" pattern exists
- **Metric**: CAR[0,10] vs. minimum CAR in [0,1]
- **Expected**: CAR[0,10] > min(CAR[0], CAR[0,1])
- **Pattern Test**:
  - Identify intraday/daily minimum (trough)
  - Test if CAR[10] - trough > 0
  - This measures the recovery from the worst point
  - **Ideal Pattern**: CAR[0,1] < 0, CAR[2,5] > 0, CAR[0,10] > 0

#### Test 6: Tariff vs Control Comparison
**Hypothesis**: Pattern is specific to tariff events, not general mean reversion
- **Metric**: Intraday AR, CAR[0,1], and CAR[2,5] for both groups
- **Expected**:
  - Tariff: AR_2hr < Control AR_2hr (bigger intraday drops)
  - Tariff: CAR[0,1] < Control CAR[0,1] (bigger initial drops)
  - Tariff: CAR[2,5] > Control CAR[2,5] (stronger recovery)
- **Test**: Two-sample t-test comparing groups

### "Buy the Dip" Strategy Test

**Refined Strategy**: Enter AFTER confirming the initial drop

**Entry Timing Options**:
1. **Immediate (Baseline)**: Buy at T+0 close (same day as tweet)
2. **Wait-One-Day**: Buy at T+1 close (next day, after overnight processing)
3. **Optimal Entry**: Buy at worst point in [0,1] (intraday low or T+1 close)

**Exit Rules**: All strategies exit at T+5 (primary) and T+10 (extended)

**Strategy Comparison**:
```
Strategy A (Immediate):     Buy T+0 close → Sell T+5
                           Return = CAR[0,5]

Strategy B (Wait-One-Day):  Buy T+1 close → Sell T+5
                           Return = CAR[1,5] = CAR[2,5] only

Strategy C (Optimal):       Buy at min(T+0,T+1) → Sell T+5
                           Return = max recovery from trough

Expected Ranking: Strategy B or C > Strategy A
Reason: Avoids initial same-day drop, captures reversion starting T+2
```

**Exit Horizon Testing**:
```
Exit T+3:  Quick reversion play (test if recovery starts early)
Exit T+5:  Medium-term reversion (main hypothesis)
Exit T+10: Extended hold (test if gains persist or fade)

Expected: T+5 optimal (recovery complete, low drift after)
```

**Control Comparison**:
- Apply same 3 entry strategies to control events
- Tariff events should show:
  - Larger difference between Strategy A and B (bigger initial drop to avoid)
  - Higher absolute returns for Strategy B (stronger reversion)
- Control events should show:
  - Minimal difference between strategies (no systematic pattern)
  - Returns ≈ 0 for all strategies (no edge)

---

## Statistical Tests

### 1. Directional Significance Tests (ONE-SIDED)
**Intraday Tests**:
- **30-min Drop**: H1: mean(AR_30min) < 0
- **2-hour Drop**: H1: mean(AR_2hr) < 0
- **Same-day Close**: H1: mean(CAR[0]) < 0

**Multi-day Tests**:
- **Next-day Persistence**: H1: mean(CAR[0,1]) < 0
- **Reversion Test**: H1: mean(CAR[2,5]) > 0
- **Extended Test**: H1: mean(CAR[6,10]) ≈ 0 (two-sided, test for no drift)

**Volatility Tests**:
- **VXX Spike Test**: H1: mean(VXX[0]) > 0
- **VXX Reversion**: H1: VXX[5] < VXX[0]

**Sign Tests** (non-parametric):
- % of events with negative CAR[0,1]
- % of events with positive CAR[2,5]
- % of events with full pattern (CAR[0,1]<0 AND CAR[2,5]>0)

### 2. Pattern Confirmation Tests
- **Trough-to-Peak**: Mean recovery from worst point (T+0 or T+1) to T+5
- **Full Cycle Profitability**: CAR[0,10] > 0 despite initial drop
- **Volatility Reversion**: VXX[5] < VXX[0] (volatility normalizes)
- **Pattern Frequency**: % of events showing "V-shaped" recovery

### 3. Cross-Sectional Analysis
- **ANOVA**: Do aggressive tweets cause larger reactions than others?
- **Regression**: `AR = β0 + β1*Aggressive + β2*Confidence + β3*MarketHours + ε`

### 4. Volatility Tests
- **VXX Spike Frequency**: % of events with VXX >1 std dev increase
- **Correlation**: Is VXX spike magnitude correlated with SPY decline magnitude?

### 5. Trading Strategy Performance Tests
- **T-test**: Mean P&L(Tariff) vs. Mean P&L(Control)
- **Bootstrap**: 95% confidence intervals for difference in returns
- **Win Rate Comparison**: Chi-square test for difference in proportions
- **Risk-Adjusted**: Compare Sharpe ratios (tariff vs. control)

---

## Analysis Steps (Sequential)

### Step 1: Data Preparation
- Load SPY and VXX market data (5-minute bars)
- Parse timestamps and create datetime index
- Load tariff tweets and filter to `is_tariff_related == true` (ALL confidence levels)
- Align tweet timestamps with market data (match to nearest 5-min bar)
- Generate control group: 276 random timestamps matched by time-of-day and day-of-week

### Step 2: Event Matching
- For each tariff tweet AND control event:
  - Find corresponding market timestamp (T=0)
  - Extract intraday 5-min price data for T-1 to T+10
  - Handle after-hours tweets (use next trading day open as T=0)
  - Flag weekends/holidays

### Step 3: Return Calculation
- Calculate 5-minute returns for SPY and VXX
- Compute baseline returns for each event (T-1 average)
- Calculate abnormal returns for intraday and daily windows (T+0 to T+10)
- Aggregate 5-min returns into 30-min, 1-hour, 2-hour, 6-hour windows

### Step 4: P&L Simulation
- For tariff events: Simulate $10,000 buy at T+0 close, exit at T+3/T+5/T+10
- For control events: Apply identical strategy
- Calculate per-trade returns and cumulative P&L
- Compute performance metrics (win rate, Sharpe, max drawdown)

### Step 5: Aggregation
- Compute mean and median abnormal returns across all events
- Calculate CARs for different windows (T+0 to T+10)
- Generate distributions and confidence intervals
- Compare tariff vs. control performance metrics

### Step 6: Segmentation Analysis
- Repeat abnormal return analysis for each sentiment category
- Repeat P&L simulation for aggressive vs. other sentiments
- Analyze by tariff type (China, Mexico, BRICS)
- Compare high-confidence (>90%) vs. lower confidence

### Step 7: Statistical Testing
- Run t-tests, sign tests, Wilcoxon tests on abnormal returns
- Test reversion hypothesis (CAR[4,10] > 0)
- Cross-sectional regression analysis
- Test tariff vs. control P&L difference (bootstrap confidence intervals)

### Step 8: Visualization & Reporting
- Event timeline plots (CAR from T-1 to T+10, tariff vs. control)
- Cumulative P&L charts (tariff vs. control over time)
- Heatmaps (AR by sentiment × time window)
- Distribution plots (histogram of abnormal returns and P&L per trade)
- Scatter plots (VXX change vs SPY change)
- Summary tables with test statistics

---

## Expected Outputs

### 1. Analysis Files (outputs/)
- `event_study_results.xlsx`: Main results table with all metrics
  - Sheet 1: Tariff Events - Event-level data (276 events × all metrics)
  - Sheet 2: Control Events - Event-level data (276 control events × all metrics)
  - Sheet 3: Aggregated Abnormal Returns (mean/median AR by window, tariff vs. control)
  - Sheet 4: Sentiment segmentation (Aggressive vs. Informational vs. Defensive)
  - Sheet 5: Statistical test results
  - Sheet 6: Intraday analysis (30-min, 1-hour, 2-hour, 6-hour windows)

- `trading_strategy_pnl.xlsx`: P&L simulation results
  - Sheet 1: Tariff Group - Per-trade P&L and cumulative returns
  - Sheet 2: Control Group - Per-trade P&L and cumulative returns
  - Sheet 3: Performance Comparison (win rates, Sharpe ratios, drawdowns)
  - Sheet 4: Segmented Performance (by sentiment, confidence, tariff type)
  - Sheet 5: Statistical Tests (t-tests, bootstrap CIs)

- `abnormal_returns_timeseries.xlsx`: Intraday and daily AR/CAR for each event (T-1 to T+10)
- `volatility_analysis.xlsx`: VXX metrics by event (spikes, correlations with SPY)

### 2. Visualizations (outputs/plots/)
All plots as PDF files:

**Event Study Charts**:
- `event_timeline_tariff_vs_control.pdf`: Average CAR from T-1 to T+10 (tariff vs. control)
  - **KEY CHART**: Should show tariff line drops T+0-1, recovers T+2-5, control line flat
- `event_timeline_by_sentiment.pdf`: Separate lines for each sentiment (Aggressive, Informational, Defensive)
- `intraday_reaction.pdf`: Average AR for first 6 hours (5-min or 30-min intervals)
  - **Shows immediate drop**: Should visualize 30-min, 1-hr, 2-hr decline
- `fall_and_recover_pattern.pdf`: **THESIS TEST CHART**
  - Bar chart showing mean returns for: CAR[0], CAR[0,1], CAR[2,5], CAR[6,10]
  - Should show negative bars for initial periods, positive for reversion
- `reversion_test.pdf`: CAR comparison across windows with confidence intervals

**Distribution Charts**:
- `distribution_ar_t0.pdf`: Histogram of immediate returns (T+0)
- `distribution_car_t10.pdf`: Histogram of cumulative returns through T+10
- `distribution_pnl_comparison.pdf`: Side-by-side histograms of P&L (tariff vs. control)

**P&L Strategy Charts**:
- `cumulative_pnl_tariff_vs_control.pdf`: Cumulative P&L over time for both groups
- `pnl_by_exit_horizon.pdf`: Comparison of T+3, T+5, T+10 exit strategies
- `pnl_by_entry_timing.pdf`: **BUY THE DIP TEST**
  - Compare Strategy A (T+0), B (T+1), C (Optimal)
  - Should show Strategy B/C outperform if thesis correct
- `pnl_by_sentiment.pdf`: P&L performance segmented by tweet sentiment
- `win_rate_comparison.pdf`: Bar chart of win rates across groups
- `strategy_waterfall.pdf`: P&L decomposition showing contribution from decline vs. reversion periods

**Correlation Charts**:
- `scatter_spy_vxx.pdf`: SPY AR vs VXX AR at T+0 (immediate reaction)
- `heatmap_sentiment_windows.pdf`: AR intensity by sentiment × time window
- `spy_vxx_timeseries.pdf`: Joint price action for major tariff events

### 3. Summary Report
- `event_study_summary.txt`: Key findings and statistics

  **Section 1: Directional Hypothesis Test Results**
  - ✓ or ✗ Does SPY fall same-day? (CAR[0] < 0?)
  - ✓ or ✗ Does VXX spike same-day? (VXX[0] > 0?)
  - ✓ or ✗ Does decline persist to T+1? (CAR[0,1] < 0?)
  - ✓ or ✗ Does market recover T+2-5? (CAR[2,5] > 0?)
  - ✓ or ✗ Is full pattern profitable? (CAR[0,10] > 0?)
  - Statistical significance (p-values for each test)

  **Section 2: Pattern Frequency**
  - % of events showing immediate drop (CAR[0] < 0)
  - % showing persistence (CAR[0,1] < 0)
  - % showing reversion (CAR[2,5] > 0)
  - % showing full "V-pattern" (drop then recover)

  **Section 3: Trading Strategy Results**
  - Strategy A (Buy T+0): Total P&L, Win Rate, Sharpe
  - Strategy B (Buy T+1): Total P&L, Win Rate, Sharpe
  - Strategy C (Optimal): Total P&L, Win Rate, Sharpe
  - Control Group: Same metrics (should be ≈0)
  - **KEY FINDING**: Which strategy performs best and by how much?

  **Section 4: Sentiment Analysis**
  - Aggressive tweets: CAR[0,1] and CAR[2,5]
  - Informational tweets: CAR[0,1] and CAR[2,5]
  - Defensive tweets: CAR[0,1] and CAR[2,5]
  - Which sentiment shows strongest pattern?

  **Section 5: Actionable Conclusion**
  - **Is the thesis supported?** (Yes/No + confidence level)
  - **Optimal entry timing**: T+0, T+1, or wait for trough?
  - **Optimal exit timing**: T+3, T+5, or T+10?
  - **Expected return per trade**: Mean and median
  - **Risk metrics**: Win rate, max drawdown, volatility
  - **Recommended action**: Trade or don't trade

---

## Key Assumptions & Limitations

### Assumptions
1. **Market efficiency**: Prices react quickly to public information
2. **Tweet timing**: `created_at` timestamp is accurate
3. **Independence**: Events are independent (no overlapping windows)
4. **Causality**: Tweet causes reaction, not reverse or confounding factor

### Limitations
1. **Small sample**: Only 276 events (smaller for some sentiment categories)
2. **Overlapping events**: Some tweets occur within 5 days of each other
3. **Confounding news**: Other market-moving news may occur simultaneously
4. **After-hours tweets**: Market can't react until next open
5. **Survivorship bias**: Only analyzing Trump's second term (2025 data)

### Robustness Checks
- Exclude events within 5 days of each other (test independence)
- Vary baseline window (T-30 to T-11 vs. T-60 to T-11)
- Vary confidence threshold (90% vs. 80%)
- Exclude after-hours tweets

---

## APPROVED PARAMETERS ✓

Based on user approval, the following parameters are confirmed:

1. **Event windows**: **T-1 to T+10** (extended to capture longer reversion)
2. **Baseline period**: **T-1 only** (previous trading day average)
3. **Return calculation**: **Intraday (5-minute bars)** for granular analysis
4. **Confidence threshold**: **ALL tweets included** (no minimum confidence filter)
5. **Overlapping events**: **Keep all** (no exclusions for proximity)
6. **Trading strategy**: **Full P&L simulation** with control group
   - Tariff events: Buy SPY at T+0 close, exit at T+3/T+5/T+10
   - Control events: Same strategy on 276 random non-tariff timestamps
   - Position size: $10,000 per trade
   - Compare performance: tariff vs. control

---

## Implementation Roadmap

### Phase 1: Data Loading & Preparation (5 min)
1. Load SPY/VXX market data from Excel files
2. Load and filter tariff tweets (276 events)
3. Generate matched control group (276 random timestamps)
4. Align all events with market data timestamps

### Phase 2: Event Study Analysis (10 min)
1. Calculate intraday and daily abnormal returns
2. Compute CARs for T-1 to T+10
3. Analyze VXX volatility patterns
4. Segment by sentiment, confidence, tariff type

### Phase 3: P&L Simulation (10 min)
1. Simulate trading strategy for tariff events
2. Simulate identical strategy for control events
3. Calculate performance metrics (win rate, Sharpe, drawdown)
4. Run statistical tests comparing tariff vs. control

### Phase 4: Visualization & Reporting (10 min)
1. Generate all PDF charts (~13 visualizations)
2. Create Excel output files with all results
3. Write summary report with key findings

**Total Estimated Runtime**: 35-40 minutes
**Estimated Output Size**: ~10-15 MB (Excel files + PDFs)

---

## Ready to Proceed

**Status**: ✓ APPROVED - Ready for implementation
**Next Action**: Create `event_study_analysis.py` script
**Last Updated**: 2025-10-20
