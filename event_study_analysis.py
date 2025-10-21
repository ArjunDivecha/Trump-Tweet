"""
=============================================================================
SCRIPT NAME: event_study_analysis.py
=============================================================================

INPUT FILES:
- SPY_5min_history.xlsx: S&P 500 ETF 5-minute price data (Date, Time, Open, High, Low, Close, Volume)
- Data Collection and Cleaning/VXX_5min_history.xlsx: Volatility ETF 5-minute price data
- Data Collection and Cleaning/tariff_classified_tweets_full_v5.json: AI-classified Trump tweets with tariff flags (CORRECTED TIMESTAMPS)

OUTPUT FILES:
- outputs/event_study_results.xlsx: Main results with event-level and aggregated metrics
- outputs/trading_strategy_pnl.xlsx: P&L simulation results for all strategies
- outputs/abnormal_returns_timeseries.xlsx: Time series of AR/CAR for each event
- outputs/volatility_analysis.xlsx: VXX spike analysis
- outputs/plots/*.pdf: 15+ visualization charts
- outputs/event_study_summary.txt: Executive summary with key findings

VERSION: 1.0
LAST UPDATED: 2025-10-20
AUTHOR: Claude Code

DESCRIPTION:
Event study testing the hypothesis that Trump's tariff tweets cause immediate market drops
followed by mean reversion, creating profitable "buy the dip" opportunities. The analysis:

1. Tests directional predictions (fall then recover pattern)
2. Analyzes intraday (30-min, 2-hour) and multi-day (T+0 to T+10) reactions
3. Simulates trading strategies with different entry timings
4. Compares tariff events to matched control group (276 random timestamps)
5. Segments by sentiment (Aggressive vs. Informational vs. Defensive)

CORE HYPOTHESIS:
- T+0 to T+1: SPY falls, VXX spikes (initial shock)
- T+2 to T+5: SPY recovers (mean reversion)
- Net effect: Profitable if buying after initial drop

DEPENDENCIES:
- pandas
- numpy
- openpyxl
- matplotlib
- scipy
- datetime
- json

USAGE:
python event_study_analysis.py

NOTES:
- Creates outputs/ directory if it doesn't exist
- Runtime: ~35-40 minutes for full analysis
- Uses T-1 baseline for abnormal returns (prior trading day average)
- All tweets included regardless of confidence score
=============================================================================
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ==================== SETUP ====================

print("="*80)
print("TRUMP TARIFF TWEET EVENT STUDY")
print("CHINA-SPECIFIC + announcing/threatening")
print("Testing: 'Fall then Recover' Hypothesis (with CORRECTED TIMESTAMPS v5)")
print("="*80)
print()

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('outputs/plots', exist_ok=True)

# ==================== DATA LOADING ====================

print("[1/10] Loading market data...")

def load_market_data(filepath):
    """Load and prepare 5-minute market data from Excel"""
    try:
        df = pd.read_excel(filepath)

        # Standardize column names
        df.columns = df.columns.str.lower()

        # Handle datetime - could be single 'date' column or separate 'date' and 'time'
        if 'date' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'])
        elif 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        else:
            print(f"  Warning: No date/datetime column found in {filepath}")
            print(f"  Available columns: {df.columns.tolist()}")
            return None

        # Sort by datetime
        df = df.sort_values('datetime').reset_index(drop=True)

        # Standardize column names for OHLCV
        rename_map = {}
        for col in df.columns:
            if col in ['open', 'high', 'low', 'close', 'volume']:
                rename_map[col] = col.capitalize()

        if rename_map:
            df.rename(columns=rename_map, inplace=True)

        # Set datetime as index
        df.set_index('datetime', inplace=True)

        return df
    except Exception as e:
        print(f"  Error loading {filepath}: {e}")
        return None

# Load SPY data
spy_data = load_market_data('SPY_5min_history.xlsx')
if spy_data is None:
    print("  ERROR: Could not load SPY data. Exiting.")
    exit(1)

print(f"  ✓ SPY data loaded: {len(spy_data)} rows")
print(f"    Date range: {spy_data.index.min()} to {spy_data.index.max()}")

# Load VXX data
vxx_data = load_market_data('Data Collection and Cleaning/VXX_5min_history.xlsx')
if vxx_data is None:
    print("  ERROR: Could not load VXX data. Exiting.")
    exit(1)

print(f"  ✓ VXX data loaded: {len(vxx_data)} rows")
print(f"    Date range: {vxx_data.index.min()} to {vxx_data.index.max()}")
print()

print("[2/10] Loading tariff tweet data from v5 JSON (corrected timestamps)...")

# Load tweets from v5 JSON
try:
    with open('Data Collection and Cleaning/tariff_classified_tweets_full_v5.json', 'r') as f:
        tweets_data = json.load(f)
    tweets_df = pd.DataFrame(tweets_data)
    print(f"  ✓ Total tweets loaded: {len(tweets_df)}")
except Exception as e:
    print(f"  ERROR: Could not load tweet data: {e}")
    exit(1)

# Filter to tariff-related tweets
tariff_tweets = tweets_df[tweets_df['is_tariff_related'] == True].copy()
print(f"  ✓ Tariff-related tweets: {len(tariff_tweets)}")

# Filter by tariff_action_type (announcing or threatening only)
print(f"\n  Tariff action type breakdown (all tariff tweets):")
for action_type, count in tariff_tweets['tariff_action_type'].value_counts().items():
    print(f"    {action_type}: {count}")

tariff_tweets = tariff_tweets[
    tariff_tweets['tariff_action_type'].isin(['announcing', 'threatening'])
].copy()
print(f"\n  ✓ Filtered to announcing or threatening: {len(tariff_tweets)} events")

# Filter by countries_mentioned containing 'China'
def contains_china(countries):
    """Check if China is in the countries list"""
    # Handle None
    if countries is None:
        return False
    # Handle list (from JSON) - this is the primary case
    if isinstance(countries, list):
        return 'China' in countries
    # Handle empty string
    if isinstance(countries, str):
        if countries.strip() == '':
            return False
        # If it's a string representation of a list, try to parse it
        try:
            import ast
            countries_list = ast.literal_eval(countries)
            return 'China' in countries_list
        except:
            return False
    # Handle other types (floats for NaN, etc.)
    try:
        if pd.isna(countries):
            return False
    except:
        pass
    return False

tariff_tweets['has_china'] = tariff_tweets['countries_mentioned'].apply(contains_china)
print(f"\n  Countries breakdown (announcing/threatening):")
print(f"    With China: {tariff_tweets['has_china'].sum()}")
print(f"    Without China: {(~tariff_tweets['has_china']).sum()}")

tariff_tweets = tariff_tweets[tariff_tweets['has_china']].copy()
print(f"\n  ✓ Filtered to China-specific events: {len(tariff_tweets)} events")

# Parse tweet timestamps
tariff_events = []
for idx, tweet in tariff_tweets.iterrows():
    try:
        # Try to parse created_at timestamp
        if pd.notna(tweet.get('created_at')) and tweet.get('created_at'):
            ts = pd.to_datetime(tweet['created_at'])
        elif pd.notna(tweet.get('timestamp')) and tweet.get('timestamp'):
            # Parse from various formats
            ts = pd.to_datetime(tweet['timestamp'])
        elif pd.notna(tweet.get('date')) and tweet.get('date'):
            ts = pd.to_datetime(tweet['date'])
        else:
            continue

        tariff_events.append({
            'post_id': tweet.get('post_id'),
            'datetime': ts,
            'content': tweet.get('content', ''),
            'sentiment': tweet.get('sentiment', 'Unknown'),
            'confidence': tweet.get('confidence', 0),
            'tariff_type': tweet.get('tariff_type', 'General'),
            'countries_mentioned': tweet.get('countries_mentioned', []),
            'tariff_percentage': tweet.get('tariff_percentage', ''),
            'tariff_action_type': tweet.get('tariff_action_type', 'no_mention'),
            'tariff_effective_date': tweet.get('tariff_effective_date', ''),
        })
    except Exception as e:
        # Skip tweets with unparseable timestamps
        continue

tariff_df = pd.DataFrame(tariff_events)
tariff_df = tariff_df.sort_values('datetime').reset_index(drop=True)

print(f"  ✓ Parsed timestamps: {len(tariff_df)} events")
print(f"    Date range: {tariff_df['datetime'].min()} to {tariff_df['datetime'].max()}")
print(f"    Sentiment breakdown:")
for sentiment, count in tariff_df['sentiment'].value_counts().items():
    print(f"      {sentiment}: {count}")
print(f"    Tariff action type breakdown:")
for action_type, count in tariff_df['tariff_action_type'].value_counts().items():
    print(f"      {action_type}: {count}")
print()

# ==================== CONTROL GROUP GENERATION ====================

print("[3/10] Generating matched control group...")

# Get date range from tariff events
min_date = tariff_df['datetime'].min()
max_date = tariff_df['datetime'].max()

# Get time-of-day and day-of-week distributions from tariff events
tariff_df['hour'] = tariff_df['datetime'].dt.hour
tariff_df['dow'] = tariff_df['datetime'].dt.dayofweek

# Generate random timestamps matching distributions
np.random.seed(42)  # For reproducibility
control_events = []

# Create exclusion windows (±3 days around tariff events)
exclusion_windows = []
for dt in tariff_df['datetime']:
    exclusion_windows.append((dt - timedelta(days=3), dt + timedelta(days=3)))

attempts = 0
max_attempts = 10000

while len(control_events) < len(tariff_df) and attempts < max_attempts:
    attempts += 1

    # Random date in range
    random_days = np.random.randint(0, (max_date - min_date).days)
    random_date = min_date + timedelta(days=random_days)

    # Match hour distribution
    random_hour = np.random.choice(tariff_df['hour'])
    random_minute = np.random.randint(0, 60)

    candidate_dt = random_date.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)

    # Check if in exclusion window
    excluded = False
    for exc_start, exc_end in exclusion_windows:
        if exc_start <= candidate_dt <= exc_end:
            excluded = True
            break

    if not excluded:
        # Check if weekday (market is open)
        if candidate_dt.weekday() < 5:  # Monday=0, Friday=4
            control_events.append({
                'datetime': candidate_dt,
                'event_type': 'control'
            })

control_df = pd.DataFrame(control_events[:len(tariff_df)])
control_df = control_df.sort_values('datetime').reset_index(drop=True)

print(f"  ✓ Control group generated: {len(control_df)} events")
print(f"    Date range: {control_df['datetime'].min()} to {control_df['datetime'].max()}")
print()

# ==================== EVENT ALIGNMENT ====================

print("[4/10] Aligning events with market data...")

def align_event_with_market(event_dt, market_data, window_days=12):
    """
    Align event timestamp with market data
    Returns price data for T-1 to T+10
    """
    # Find closest market timestamp
    try:
        # Get market hours data only (9:30 AM - 4:00 PM ET)
        market_hours = market_data.between_time('09:30', '16:00')

        # Find nearest timestamp
        nearest_idx = market_hours.index.get_indexer([event_dt], method='nearest')[0]
        event_market_time = market_hours.index[nearest_idx]

        # Get T-1 (previous trading day)
        prev_day = event_market_time.date() - timedelta(days=1)
        # Adjust for weekends
        while prev_day.weekday() >= 5:
            prev_day = prev_day - timedelta(days=1)

        # Get T+10 (10 trading days forward)
        end_date = event_market_time.date()
        trading_days_forward = 0
        while trading_days_forward < 10:
            end_date = end_date + timedelta(days=1)
            if end_date.weekday() < 5:
                trading_days_forward += 1

        # Extract data window
        window_data = market_data.loc[
            (market_data.index.date >= prev_day) &
            (market_data.index.date <= end_date)
        ].copy()

        return event_market_time, window_data

    except Exception as e:
        return None, None

# Align tariff events
print("  Aligning tariff events...")
tariff_aligned = []
for idx, row in tariff_df.iterrows():
    event_t0, window = align_event_with_market(row['datetime'], spy_data)
    if event_t0 is not None and len(window) > 0:
        tariff_aligned.append({
            **row.to_dict(),
            'event_t0': event_t0,
            'market_data_available': True
        })
    else:
        tariff_aligned.append({
            **row.to_dict(),
            'event_t0': None,
            'market_data_available': False
        })

tariff_df = pd.DataFrame(tariff_aligned)
valid_tariff = tariff_df[tariff_df['market_data_available']].copy()

print(f"  ✓ Tariff events aligned: {len(valid_tariff)} / {len(tariff_df)} have market data")

# Align control events
print("  Aligning control events...")
control_aligned = []
for idx, row in control_df.iterrows():
    event_t0, window = align_event_with_market(row['datetime'], spy_data)
    if event_t0 is not None and len(window) > 0:
        control_aligned.append({
            **row.to_dict(),
            'event_t0': event_t0,
            'market_data_available': True
        })
    else:
        control_aligned.append({
            **row.to_dict(),
            'event_t0': None,
            'market_data_available': False
        })

control_df = pd.DataFrame(control_aligned)
valid_control = control_df[control_df['market_data_available']].copy()

print(f"  ✓ Control events aligned: {len(valid_control)} / {len(control_df)} have market data")
print()

# ==================== RETURN CALCULATIONS ====================

print("[5/10] Calculating returns and abnormal returns...")

def calculate_event_returns(event_t0, spy_data, vxx_data):
    """
    Calculate returns for an event from T-1 to T+10
    Returns dictionary with intraday and daily metrics
    """
    results = {
        'event_t0': event_t0,
        'valid': False
    }

    try:
        # Get event date
        event_date = event_t0.date()

        # Get T-1 (previous trading day)
        t_minus_1 = event_date - timedelta(days=1)
        while t_minus_1.weekday() >= 5:
            t_minus_1 = t_minus_1 - timedelta(days=1)

        # Get T-1 data (baseline)
        t1_data = spy_data[spy_data.index.date == t_minus_1]
        if len(t1_data) == 0:
            return results

        # Calculate T-1 baseline return (mean of all 5-min returns that day)
        t1_data_sorted = t1_data.sort_index()
        t1_returns = t1_data_sorted['Close'].pct_change().dropna()
        baseline_return = t1_returns.mean() if len(t1_returns) > 0 else 0

        results['baseline_return'] = baseline_return
        results['t_minus_1_close'] = t1_data_sorted['Close'].iloc[-1]

        # Get T+0 data (event day)
        t0_data = spy_data[spy_data.index.date == event_date]
        if len(t0_data) == 0:
            return results

        # Find event time within T+0
        event_price_idx = t0_data.index.get_indexer([event_t0], method='nearest')[0]
        event_price = t0_data['Close'].iloc[event_price_idx]
        event_exact_time = t0_data.index[event_price_idx]

        results['t0_event_time'] = event_exact_time
        results['t0_event_price'] = event_price

        # Intraday returns (30-min, 1-hour, 2-hour from event)
        try:
            # 30 minutes
            time_30min = event_exact_time + timedelta(minutes=30)
            data_30min = t0_data[t0_data.index <= time_30min]
            if len(data_30min) > 0:
                price_30min = data_30min['Close'].iloc[-1]
                results['ar_30min'] = (price_30min / event_price - 1) - baseline_return

            # 1 hour
            time_1hr = event_exact_time + timedelta(hours=1)
            data_1hr = t0_data[t0_data.index <= time_1hr]
            if len(data_1hr) > 0:
                price_1hr = data_1hr['Close'].iloc[-1]
                results['ar_1hr'] = (price_1hr / event_price - 1) - baseline_return

            # 2 hours
            time_2hr = event_exact_time + timedelta(hours=2)
            data_2hr = t0_data[t0_data.index <= time_2hr]
            if len(data_2hr) > 0:
                price_2hr = data_2hr['Close'].iloc[-1]
                results['ar_2hr'] = (price_2hr / event_price - 1) - baseline_return
        except:
            pass

        # T+0 close (same day)
        t0_close = t0_data['Close'].iloc[-1]
        results['t0_close'] = t0_close
        results['car_t0'] = (t0_close / results['t_minus_1_close'] - 1) - baseline_return

        # Calculate daily returns T+1 to T+10
        current_date = event_date
        for day_offset in range(1, 11):
            # Get next trading day
            next_date = current_date + timedelta(days=1)
            while next_date.weekday() >= 5:
                next_date = next_date + timedelta(days=1)

            day_data = spy_data[spy_data.index.date == next_date]
            if len(day_data) > 0:
                day_close = day_data['Close'].iloc[-1]
                results[f't{day_offset}_close'] = day_close
                results[f't{day_offset}_return'] = (day_close / results['t_minus_1_close'] - 1) - baseline_return

            current_date = next_date

        # Calculate CARs
        results['car_t0_t1'] = results.get('t1_return', 0)
        results['car_t2_t5'] = sum([results.get(f't{i}_return', 0) for i in range(2, 6)])
        results['car_t6_t10'] = sum([results.get(f't{i}_return', 0) for i in range(6, 11)])
        results['car_t0_t10'] = sum([results.get(f't{i}_return', 0) for i in range(0, 11)])

        # VXX analysis
        if vxx_data is not None:
            try:
                vxx_t1 = vxx_data[vxx_data.index.date == t_minus_1]
                vxx_t0 = vxx_data[vxx_data.index.date == event_date]

                if len(vxx_t1) > 0 and len(vxx_t0) > 0:
                    vxx_baseline = vxx_t1['Close'].iloc[-1]
                    vxx_event = vxx_t0['Close'].iloc[-1]
                    results['vxx_t0_return'] = (vxx_event / vxx_baseline - 1)

                    # VXX at T+5
                    t5_date = current_date
                    days_forward = 0
                    while days_forward < 5:
                        t5_date = t5_date + timedelta(days=1)
                        if t5_date.weekday() < 5:
                            days_forward += 1

                    vxx_t5 = vxx_data[vxx_data.index.date == t5_date]
                    if len(vxx_t5) > 0:
                        vxx_t5_close = vxx_t5['Close'].iloc[-1]
                        results['vxx_t5_return'] = (vxx_t5_close / vxx_baseline - 1)
            except:
                pass

        results['valid'] = True

    except Exception as e:
        print(f"    Error processing event at {event_t0}: {e}")

    return results

# Calculate for tariff events
print("  Processing tariff events...")
tariff_returns = []
for idx, row in valid_tariff.iterrows():
    if idx % 50 == 0:
        print(f"    Progress: {idx}/{len(valid_tariff)}")
    returns = calculate_event_returns(row['event_t0'], spy_data, vxx_data)
    if returns['valid']:
        tariff_returns.append({**row.to_dict(), **returns})

tariff_results_df = pd.DataFrame(tariff_returns)
print(f"  ✓ Tariff events processed: {len(tariff_results_df)}")

# Calculate for control events
print("  Processing control events...")
control_returns = []
for idx, row in valid_control.iterrows():
    if idx % 50 == 0:
        print(f"    Progress: {idx}/{len(valid_control)}")
    returns = calculate_event_returns(row['event_t0'], spy_data, vxx_data)
    if returns['valid']:
        control_returns.append({**row.to_dict(), **returns})

control_results_df = pd.DataFrame(control_returns)
print(f"  ✓ Control events processed: {len(control_results_df)}")
print()

# ==================== FILTER TO AGGRESSIVE SENTIMENT + POST APRIL 3 ====================

print("[6/10] Filtering to Aggressive sentiment events after April 3, 2025...")
print()

# Filter to Aggressive only AND after April 3, 2025
tariff_all = tariff_results_df.copy()
control_all = control_results_df.copy()

# Convert datetime to comparable format
cutoff_date = pd.to_datetime('2025-04-03')
tariff_results_df['datetime_parsed'] = pd.to_datetime(tariff_results_df['datetime'])
control_results_df['datetime_parsed'] = pd.to_datetime(control_results_df['datetime'])

print(f"  Original tariff events: {len(tariff_all)}")
print(f"  Date range: {tariff_all['datetime'].min()} to {tariff_all['datetime'].max()}")
print()

# Apply filters - TARIFF EVENTS
tariff_results_df = tariff_results_df[
    (tariff_results_df['sentiment'] == 'Aggressive') &
    (tariff_results_df['datetime_parsed'] > cutoff_date)
].copy()

print(f"  Aggressive events only: {(tariff_all['sentiment'] == 'Aggressive').sum()}")
print(f"  Aggressive + after April 3: {len(tariff_results_df)}")
print(f"  New tariff date range: {tariff_results_df['datetime'].min()} to {tariff_results_df['datetime'].max()}")
print()

# Apply filters - CONTROL EVENTS (same date filter!)
print(f"  Original control events: {len(control_all)}")
control_results_df = control_results_df[
    control_results_df['datetime_parsed'] > cutoff_date
].copy()
print(f"  Control after April 3: {len(control_results_df)}")
print(f"  New control date range: {control_results_df['datetime'].min()} to {control_results_df['datetime'].max()}")
print()

print(f"  Sentiment breakdown in original tariff events:")
for sentiment, count in tariff_all['sentiment'].value_counts().items():
    print(f"    {sentiment}: {count}")
print()

# ==================== VALIDATION: SAMPLE EVENTS ====================

print("[7/10] Validating results - China-Specific Aggressive Events Post-April 3")
print()

# Show sample of tariff events with returns
print("="*80)
print("SAMPLE EVENTS - CHINA TARIFFS - AGGRESSIVE POST-APRIL 3 - RETURN ANALYSIS")
print("="*80)
print()

# Get a few diverse events
sample_indices = [0, len(tariff_results_df)//4, len(tariff_results_df)//2, len(tariff_results_df)-1]

for idx in sample_indices:
    if idx < len(tariff_results_df):
        event = tariff_results_df.iloc[idx]

        print(f"Event #{idx+1}: {event['datetime']}")
        print(f"  Content: {event.get('content', '')[:100]}...")
        print(f"  Sentiment: {event.get('sentiment', 'N/A')}")
        print(f"  Confidence: {event.get('confidence', 'N/A')}%")
        print()
        print(f"  INTRADAY RETURNS:")
        print(f"    30-min AR:  {event.get('ar_30min', np.nan)*100:.3f}%" if not pd.isna(event.get('ar_30min')) else "    30-min AR:  N/A")
        print(f"    1-hour AR:  {event.get('ar_1hr', np.nan)*100:.3f}%" if not pd.isna(event.get('ar_1hr')) else "    1-hour AR:  N/A")
        print(f"    2-hour AR:  {event.get('ar_2hr', np.nan)*100:.3f}%" if not pd.isna(event.get('ar_2hr')) else "    2-hour AR:  N/A")
        print()
        print(f"  DAILY CUMULATIVE RETURNS:")
        print(f"    T+0 (same day):    {event.get('car_t0', np.nan)*100:.3f}%")
        print(f"    T+0 to T+1:        {event.get('car_t0_t1', np.nan)*100:.3f}%")
        print(f"    T+2 to T+5:        {event.get('car_t2_t5', np.nan)*100:.3f}%")
        print(f"    T+6 to T+10:       {event.get('car_t6_t10', np.nan)*100:.3f}%")
        print(f"    T+0 to T+10 (NET): {event.get('car_t0_t10', np.nan)*100:.3f}%")
        print()
        if not pd.isna(event.get('vxx_t0_return')):
            print(f"  VXX VOLATILITY:")
            print(f"    T+0 return:        {event.get('vxx_t0_return', np.nan)*100:.3f}%")
            if not pd.isna(event.get('vxx_t5_return')):
                print(f"    T+5 return:        {event.get('vxx_t5_return', np.nan)*100:.3f}%")
        print()
        print("-"*80)
        print()

# Summary statistics across all events
print("="*80)
print("AGGREGATE STATISTICS - CHINA TARIFFS - AGGRESSIVE POST-APRIL 3 (N={})".format(len(tariff_results_df)))
print("="*80)
print()

# Calculate mean returns
print("MEAN RETURNS:")
print(f"  30-min AR:         {tariff_results_df['ar_30min'].mean()*100:.3f}%")
print(f"  1-hour AR:         {tariff_results_df['ar_1hr'].mean()*100:.3f}%")
print(f"  2-hour AR:         {tariff_results_df['ar_2hr'].mean()*100:.3f}%")
print(f"  CAR[0] (same day): {tariff_results_df['car_t0'].mean()*100:.3f}%")
print(f"  CAR[0,1]:          {tariff_results_df['car_t0_t1'].mean()*100:.3f}%")
print(f"  CAR[2,5]:          {tariff_results_df['car_t2_t5'].mean()*100:.3f}%")
print(f"  CAR[6,10]:         {tariff_results_df['car_t6_t10'].mean()*100:.3f}%")
print(f"  CAR[0,10] (NET):   {tariff_results_df['car_t0_t10'].mean()*100:.3f}%")
print()

# Directional tests
print("DIRECTIONAL PATTERN:")
print(f"  % negative T+0:    {(tariff_results_df['car_t0'] < 0).sum() / len(tariff_results_df) * 100:.1f}%")
print(f"  % negative T+0,1:  {(tariff_results_df['car_t0_t1'] < 0).sum() / len(tariff_results_df) * 100:.1f}%")
print(f"  % positive T+2,5:  {(tariff_results_df['car_t2_t5'] > 0).sum() / len(tariff_results_df) * 100:.1f}%")
print(f"  % V-pattern:       {((tariff_results_df['car_t0_t1'] < 0) & (tariff_results_df['car_t2_t5'] > 0)).sum() / len(tariff_results_df) * 100:.1f}%")
print()

# VXX
vxx_valid = tariff_results_df['vxx_t0_return'].notna()
if vxx_valid.sum() > 0:
    print("VXX VOLATILITY:")
    print(f"  Mean T+0 return:   {tariff_results_df.loc[vxx_valid, 'vxx_t0_return'].mean()*100:.3f}%")
    print(f"  % positive T+0:    {(tariff_results_df.loc[vxx_valid, 'vxx_t0_return'] > 0).sum() / vxx_valid.sum() * 100:.1f}%")
    print()

print("="*80)
print("AGGREGATE STATISTICS - CONTROL EVENTS (N={})".format(len(control_results_df)))
print("="*80)
print()

print("MEAN RETURNS:")
print(f"  30-min AR:         {control_results_df['ar_30min'].mean()*100:.3f}%")
print(f"  1-hour AR:         {control_results_df['ar_1hr'].mean()*100:.3f}%")
print(f"  2-hour AR:         {control_results_df['ar_2hr'].mean()*100:.3f}%")
print(f"  CAR[0] (same day): {control_results_df['car_t0'].mean()*100:.3f}%")
print(f"  CAR[0,1]:          {control_results_df['car_t0_t1'].mean()*100:.3f}%")
print(f"  CAR[2,5]:          {control_results_df['car_t2_t5'].mean()*100:.3f}%")
print(f"  CAR[6,10]:         {control_results_df['car_t6_t10'].mean()*100:.3f}%")
print(f"  CAR[0,10] (NET):   {control_results_df['car_t0_t10'].mean()*100:.3f}%")
print()

print("DIRECTIONAL PATTERN:")
print(f"  % negative T+0:    {(control_results_df['car_t0'] < 0).sum() / len(control_results_df) * 100:.1f}%")
print(f"  % negative T+0,1:  {(control_results_df['car_t0_t1'] < 0).sum() / len(control_results_df) * 100:.1f}%")
print(f"  % positive T+2,5:  {(control_results_df['car_t2_t5'] > 0).sum() / len(control_results_df) * 100:.1f}%")
print()

print("="*80)
print("INITIAL HYPOTHESIS TEST RESULTS")
print("="*80)
print()

# Simple t-tests
from scipy.stats import ttest_1samp, ttest_ind

# Test 1: Does SPY fall on T+0?
t_stat, p_val = ttest_1samp(tariff_results_df['car_t0'].dropna(), 0, alternative='less')
print(f"Test 1: Does SPY fall same-day (CAR[0] < 0)?")
print(f"  Mean CAR[0]: {tariff_results_df['car_t0'].mean()*100:.3f}%")
print(f"  t-statistic: {t_stat:.3f}")
print(f"  p-value: {p_val:.4f}")
print(f"  Result: {'✓ SUPPORTED' if p_val < 0.05 else '✗ NOT SUPPORTED'} (α=0.05)")
print()

# Test 2: Does SPY fall through T+1?
t_stat, p_val = ttest_1samp(tariff_results_df['car_t0_t1'].dropna(), 0, alternative='less')
print(f"Test 2: Does decline persist through T+1 (CAR[0,1] < 0)?")
print(f"  Mean CAR[0,1]: {tariff_results_df['car_t0_t1'].mean()*100:.3f}%")
print(f"  t-statistic: {t_stat:.3f}")
print(f"  p-value: {p_val:.4f}")
print(f"  Result: {'✓ SUPPORTED' if p_val < 0.05 else '✗ NOT SUPPORTED'} (α=0.05)")
print()

# Test 3: Does SPY recover T+2 to T+5?
t_stat, p_val = ttest_1samp(tariff_results_df['car_t2_t5'].dropna(), 0, alternative='greater')
print(f"Test 3: Does market recover T+2 to T+5 (CAR[2,5] > 0)?")
print(f"  Mean CAR[2,5]: {tariff_results_df['car_t2_t5'].mean()*100:.3f}%")
print(f"  t-statistic: {t_stat:.3f}")
print(f"  p-value: {p_val:.4f}")
print(f"  Result: {'✓ SUPPORTED' if p_val < 0.05 else '✗ NOT SUPPORTED'} (α=0.05)")
print()

# Test 4: VXX spike
vxx_data_test = tariff_results_df['vxx_t0_return'].dropna()
if len(vxx_data_test) > 0:
    t_stat, p_val = ttest_1samp(vxx_data_test, 0, alternative='greater')
    print(f"Test 4: Does VXX spike on T+0 (VXX[0] > 0)?")
    print(f"  Mean VXX[0]: {vxx_data_test.mean()*100:.3f}%")
    print(f"  t-statistic: {t_stat:.3f}")
    print(f"  p-value: {p_val:.4f}")
    print(f"  Result: {'✓ SUPPORTED' if p_val < 0.05 else '✗ NOT SUPPORTED'} (α=0.05)")
    print()

# Test 5: Tariff vs Control
t_stat, p_val = ttest_ind(tariff_results_df['car_t0'].dropna(), control_results_df['car_t0'].dropna(), alternative='less')
print(f"Test 5: Do tariff events cause larger drops than control (Tariff CAR[0] < Control CAR[0])?")
print(f"  Tariff mean:  {tariff_results_df['car_t0'].mean()*100:.3f}%")
print(f"  Control mean: {control_results_df['car_t0'].mean()*100:.3f}%")
print(f"  Difference:   {(tariff_results_df['car_t0'].mean() - control_results_df['car_t0'].mean())*100:.3f}%")
print(f"  t-statistic: {t_stat:.3f}")
print(f"  p-value: {p_val:.4f}")
print(f"  Result: {'✓ SUPPORTED' if p_val < 0.05 else '✗ NOT SUPPORTED'} (α=0.05)")
print()

print()
print("="*80)
print("VALIDATION COMPLETE")
print("="*80)
print()
print("Next steps:")
print("  - Review sample events and aggregate statistics above")
print("  - Verify the 'fall then recover' pattern is visible in the data")
print("  - If results look correct, proceed with full implementation")
print()
