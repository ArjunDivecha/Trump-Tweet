"""
=============================================================================
SCRIPT NAME: short_term_reaction_analysis.py
=============================================================================

INPUT FILES:
- SPY_5min_history.xlsx: S&P 500 ETF 5-minute price data
- Data Collection and Cleaning/VXX_5min_history.xlsx: Volatility ETF 5-minute price data
- Data Collection and Cleaning/tariff_classified_tweets_full_v5.json: Tariff tweets with corrected timestamps

OUTPUT FILES:
- outputs/short_term_reactions.xlsx: Detailed minute-by-minute reactions for each event
- outputs/short_term_summary.xlsx: Aggregate statistics and hypothesis tests
- outputs/short_term_comparison.xlsx: Tariff vs Control group comparison

VERSION: 1.0
LAST UPDATED: 2025-10-20
AUTHOR: Claude Code

DESCRIPTION:
Analyzes immediate market reactions to Trump tariff tweets at precise time intervals:
5, 10, 15, and 30 minutes after each announcement. Tests whether markets show
immediate negative reactions that might be obscured in longer-term analysis.

HYPOTHESIS:
- Market falls immediately (within 5-30 minutes) after tariff announcement
- VXX spikes in same time window
- Pattern more visible in short windows than daily analysis

DEPENDENCIES:
- pandas
- numpy
- openpyxl
- json
- datetime

USAGE:
python short_term_reaction_analysis.py

NOTES:
- Uses 5-minute bar data for precise timing
- Calculates cumulative returns at 5, 10, 15, 30 minute marks
- Compares to 30-minute pre-announcement baseline
- Filters: China-specific, announcing/threatening, Aggressive, post-April 3
=============================================================================
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ==================== SETUP ====================

print("="*80)
print("SHORT-TERM TARIFF TWEET REACTION ANALYSIS")
print("Analyzing 5, 10, 15, and 30-minute reactions")
print("="*80)
print()

# Create output directory
os.makedirs('outputs', exist_ok=True)

# ==================== LOAD DATA ====================

print("[1/5] Loading market data...")

def load_market_data(filepath):
    """Load and prepare 5-minute market data"""
    df = pd.read_excel(filepath)
    df.columns = df.columns.str.lower()

    # Create datetime index
    if 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'])
    elif 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])

    # Standardize OHLCV columns
    rename_map = {}
    for col in df.columns:
        if col in ['open', 'high', 'low', 'close', 'volume']:
            rename_map[col] = col.capitalize()

    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    df.set_index('datetime', inplace=True)
    df = df.sort_index()

    return df

# Load SPY and VXX data
spy_data = load_market_data('SPY_5min_history.xlsx')
vxx_data = load_market_data('Data Collection and Cleaning/VXX_5min_history.xlsx')

print(f"  ✓ SPY data loaded: {len(spy_data)} 5-minute bars")
print(f"    Date range: {spy_data.index.min()} to {spy_data.index.max()}")
print(f"  ✓ VXX data loaded: {len(vxx_data)} 5-minute bars")
print(f"    Date range: {vxx_data.index.min()} to {vxx_data.index.max()}")
print()

# ==================== LOAD TARIFF TWEETS ====================

print("[2/5] Loading tariff tweets (v5 corrected timestamps)...")

with open('Data Collection and Cleaning/tariff_classified_tweets_full_v5.json', 'r') as f:
    tweets_data = json.load(f)

tweets_df = pd.DataFrame(tweets_data)

# Filter to tariff-related tweets
tariff_tweets = tweets_df[tweets_df['is_tariff_related'] == True].copy()
print(f"  ✓ Tariff-related tweets: {len(tariff_tweets)}")

# Filter by tariff_action_type
tariff_tweets = tariff_tweets[
    tariff_tweets['tariff_action_type'].isin(['announcing', 'threatening'])
].copy()
print(f"  ✓ Announcing/threatening: {len(tariff_tweets)}")

# Filter by China mentions
def contains_china(countries):
    if countries is None:
        return False
    if isinstance(countries, list):
        return 'China' in countries
    if isinstance(countries, str):
        if countries.strip() == '':
            return False
        try:
            import ast
            countries_list = ast.literal_eval(countries)
            return 'China' in countries_list
        except:
            return False
    try:
        if pd.isna(countries):
            return False
    except:
        pass
    return False

tariff_tweets['has_china'] = tariff_tweets['countries_mentioned'].apply(contains_china)
tariff_tweets = tariff_tweets[tariff_tweets['has_china']].copy()
print(f"  ✓ China-specific: {len(tariff_tweets)}")

# Filter by Aggressive sentiment and post-April 3
april_3 = datetime(2025, 4, 3)
tariff_events = []

for idx, tweet in tariff_tweets.iterrows():
    if tweet.get('sentiment') != 'Aggressive':
        continue

    try:
        if pd.notna(tweet.get('created_at')) and tweet.get('created_at'):
            ts = pd.to_datetime(tweet['created_at'])
        else:
            continue

        if ts < april_3:
            continue

        tariff_events.append({
            'post_id': tweet.get('post_id'),
            'datetime': ts,
            'content': tweet.get('content', ''),
            'sentiment': tweet.get('sentiment', 'Unknown'),
            'tariff_action_type': tweet.get('tariff_action_type', 'no_mention'),
            'tariff_percentage': tweet.get('tariff_percentage', ''),
        })
    except:
        continue

tariff_df = pd.DataFrame(tariff_events)
tariff_df = tariff_df.sort_values('datetime').reset_index(drop=True)

print(f"  ✓ Aggressive + post-April 3: {len(tariff_df)} events")
print(f"    Date range: {tariff_df['datetime'].min()} to {tariff_df['datetime'].max()}")
print()

# ==================== CALCULATE SHORT-TERM REACTIONS ====================

print("[3/5] Calculating 5-minute interval reactions...")

def calculate_short_term_reaction(event_time, market_data, intervals=[5, 10, 15, 30]):
    """
    Calculate returns at specific minute intervals after event

    Args:
        event_time: datetime of tweet
        market_data: DataFrame with 5-minute bars
        intervals: list of minutes to calculate returns at

    Returns:
        dict with returns at each interval plus baseline
    """
    results = {
        'event_time': event_time,
        'baseline_return': np.nan,
    }

    # Add interval keys
    for interval in intervals:
        results[f'return_{interval}min'] = np.nan
        results[f'cumulative_{interval}min'] = np.nan

    # Get baseline: 30 minutes before event
    baseline_start = event_time - timedelta(minutes=35)
    baseline_end = event_time - timedelta(minutes=5)
    baseline_data = market_data[(market_data.index >= baseline_start) &
                                (market_data.index < baseline_end)]

    if len(baseline_data) > 1:
        baseline_returns = baseline_data['Close'].pct_change().dropna()
        if len(baseline_returns) > 0:
            results['baseline_return'] = baseline_returns.mean() * 100  # as percentage

    # Get post-event data (next 35 minutes to be safe)
    post_start = event_time
    post_end = event_time + timedelta(minutes=35)
    post_data = market_data[(market_data.index >= post_start) &
                            (market_data.index <= post_end)]

    if len(post_data) < 2:
        return results

    # Get starting price (closest bar at or after event)
    start_price = post_data.iloc[0]['Close']

    # Calculate returns at each interval
    for interval in intervals:
        target_time = event_time + timedelta(minutes=interval)

        # Find closest bar within 5 minutes of target
        nearby_data = post_data[(post_data.index >= target_time - timedelta(minutes=2)) &
                                (post_data.index <= target_time + timedelta(minutes=3))]

        if len(nearby_data) > 0:
            end_price = nearby_data.iloc[0]['Close']

            # Bar-to-bar return for this interval
            interval_bars = post_data[(post_data.index > event_time) &
                                     (post_data.index <= nearby_data.index[0])]
            if len(interval_bars) > 1:
                interval_returns = interval_bars['Close'].pct_change().dropna()
                results[f'return_{interval}min'] = interval_returns.mean() * 100

            # Cumulative return from event to this point
            cumulative_return = ((end_price / start_price) - 1) * 100
            results[f'cumulative_{interval}min'] = cumulative_return

    return results

# Calculate for all tariff events
tariff_reactions = []

for idx, event in tariff_df.iterrows():
    reaction = calculate_short_term_reaction(event['datetime'], spy_data)
    reaction.update({
        'event_type': 'tariff',
        'post_id': event['post_id'],
        'content_preview': event['content'][:100],
        'tariff_action_type': event['tariff_action_type'],
    })
    tariff_reactions.append(reaction)
    print(f"    Processed: {idx+1}/{len(tariff_df)}")

tariff_reactions_df = pd.DataFrame(tariff_reactions)
print(f"  ✓ Tariff events processed: {len(tariff_reactions_df)}")
print()

# ==================== GENERATE CONTROL GROUP ====================

print("[4/5] Generating matched control group...")

# Get trading hours and days from tariff events
tariff_df['hour'] = tariff_df['datetime'].dt.hour
tariff_df['dayofweek'] = tariff_df['datetime'].dt.dayofweek

# Generate random timestamps matching time-of-day and day-of-week patterns
np.random.seed(42)
min_date = tariff_df['datetime'].min()
max_date = tariff_df['datetime'].max()

control_events = []
attempts = 0
max_attempts = 1000

while len(control_events) < len(tariff_df) and attempts < max_attempts:
    attempts += 1

    # Random date in range
    days_range = (max_date - min_date).days
    random_days = np.random.randint(0, days_range)
    random_date = min_date + timedelta(days=random_days)

    # Match day-of-week distribution
    target_dow = np.random.choice(tariff_df['dayofweek'].values)
    while random_date.weekday() != target_dow:
        random_days = np.random.randint(0, days_range)
        random_date = min_date + timedelta(days=random_days)

    # Match hour distribution
    target_hour = np.random.choice(tariff_df['hour'].values)
    random_minute = np.random.randint(0, 60)
    random_timestamp = random_date.replace(hour=target_hour, minute=random_minute, second=0)

    # Exclude dates within ±3 days of any tariff event
    too_close = False
    for tariff_time in tariff_df['datetime']:
        if abs((random_timestamp - tariff_time).days) <= 3:
            too_close = True
            break

    if not too_close and random_timestamp not in [e['datetime'] for e in control_events]:
        control_events.append({'datetime': random_timestamp})

control_df = pd.DataFrame(control_events)
print(f"  ✓ Control group generated: {len(control_df)} events")
print()

# Calculate reactions for control group
control_reactions = []

for idx, event in control_df.iterrows():
    reaction = calculate_short_term_reaction(event['datetime'], spy_data)
    reaction.update({
        'event_type': 'control',
        'post_id': f'control_{idx}',
        'content_preview': 'Control (random timestamp)',
        'tariff_action_type': 'none',
    })
    control_reactions.append(reaction)

control_reactions_df = pd.DataFrame(control_reactions)
print(f"  ✓ Control events processed: {len(control_reactions_df)}")
print()

# ==================== ANALYZE AND REPORT ====================

print("[5/5] Generating analysis and statistics...")
print()

# Combine data
all_reactions = pd.concat([tariff_reactions_df, control_reactions_df], ignore_index=True)

# Calculate aggregate statistics
intervals = [5, 10, 15, 30]

print("="*80)
print(f"TARIFF EVENTS (N={len(tariff_reactions_df)})")
print("="*80)
print()

for interval in intervals:
    cumulative_col = f'cumulative_{interval}min'
    data = tariff_reactions_df[cumulative_col].dropna()

    if len(data) > 0:
        mean_return = data.mean()
        median_return = data.median()
        pct_negative = (data < 0).sum() / len(data) * 100

        print(f"{interval}-MINUTE CUMULATIVE RETURN:")
        print(f"  Mean:          {mean_return:>7.3f}%")
        print(f"  Median:        {median_return:>7.3f}%")
        print(f"  % Negative:    {pct_negative:>7.1f}%")
        print(f"  Sample size:   {len(data)}")

        # One-sample t-test: Is mean < 0?
        if len(data) >= 3:
            t_stat, p_value = stats.ttest_1samp(data, 0)
            if t_stat < 0:  # Only care about negative direction
                p_value_one_sided = p_value / 2
            else:
                p_value_one_sided = 1 - (p_value / 2)

            print(f"  t-statistic:   {t_stat:>7.3f}")
            print(f"  p-value:       {p_value_one_sided:>7.4f} (one-sided, H0: mean = 0, H1: mean < 0)")

            if p_value_one_sided < 0.05:
                print(f"  Result:        ✓ SIGNIFICANT negative reaction (α=0.05)")
            else:
                print(f"  Result:        ✗ NOT significant (α=0.05)")

        print()

print("="*80)
print(f"CONTROL EVENTS (N={len(control_reactions_df)})")
print("="*80)
print()

for interval in intervals:
    cumulative_col = f'cumulative_{interval}min'
    data = control_reactions_df[cumulative_col].dropna()

    if len(data) > 0:
        mean_return = data.mean()
        median_return = data.median()
        pct_negative = (data < 0).sum() / len(data) * 100

        print(f"{interval}-MINUTE CUMULATIVE RETURN:")
        print(f"  Mean:          {mean_return:>7.3f}%")
        print(f"  Median:        {median_return:>7.3f}%")
        print(f"  % Negative:    {pct_negative:>7.1f}%")
        print(f"  Sample size:   {len(data)}")
        print()

# Two-sample comparison
print("="*80)
print("TARIFF vs CONTROL COMPARISON")
print("="*80)
print()

for interval in intervals:
    cumulative_col = f'cumulative_{interval}min'
    tariff_data = tariff_reactions_df[cumulative_col].dropna()
    control_data = control_reactions_df[cumulative_col].dropna()

    if len(tariff_data) >= 3 and len(control_data) >= 3:
        # Two-sample t-test
        t_stat, p_value = stats.ttest_ind(tariff_data, control_data)

        # One-sided: tariff < control
        if tariff_data.mean() < control_data.mean():
            p_value_one_sided = p_value / 2
        else:
            p_value_one_sided = 1 - (p_value / 2)

        print(f"{interval}-MINUTE COMPARISON:")
        print(f"  Tariff mean:   {tariff_data.mean():>7.3f}%")
        print(f"  Control mean:  {control_data.mean():>7.3f}%")
        print(f"  Difference:    {tariff_data.mean() - control_data.mean():>7.3f}%")
        print(f"  t-statistic:   {t_stat:>7.3f}")
        print(f"  p-value:       {p_value_one_sided:>7.4f} (one-sided, H1: tariff < control)")

        if p_value_one_sided < 0.05:
            print(f"  Result:        ✓ Tariff events WORSE than control (α=0.05)")
        else:
            print(f"  Result:        ✗ No significant difference (α=0.05)")
        print()

# ==================== SAVE TO EXCEL ====================

print("Saving results to Excel...")

# Detailed reactions
with pd.ExcelWriter('outputs/short_term_reactions.xlsx', engine='openpyxl') as writer:
    tariff_reactions_df.to_excel(writer, sheet_name='Tariff Events', index=False)
    control_reactions_df.to_excel(writer, sheet_name='Control Events', index=False)

# Summary statistics
summary_data = []
for interval in intervals:
    cumulative_col = f'cumulative_{interval}min'

    tariff_data = tariff_reactions_df[cumulative_col].dropna()
    control_data = control_reactions_df[cumulative_col].dropna()

    summary_data.append({
        'Interval': f'{interval} min',
        'Tariff_Mean': tariff_data.mean() if len(tariff_data) > 0 else np.nan,
        'Tariff_Median': tariff_data.median() if len(tariff_data) > 0 else np.nan,
        'Tariff_Pct_Negative': (tariff_data < 0).sum() / len(tariff_data) * 100 if len(tariff_data) > 0 else np.nan,
        'Control_Mean': control_data.mean() if len(control_data) > 0 else np.nan,
        'Control_Median': control_data.median() if len(control_data) > 0 else np.nan,
        'Control_Pct_Negative': (control_data < 0).sum() / len(control_data) * 100 if len(control_data) > 0 else np.nan,
        'Difference': (tariff_data.mean() - control_data.mean()) if len(tariff_data) > 0 and len(control_data) > 0 else np.nan,
    })

summary_df = pd.DataFrame(summary_data)
summary_df.to_excel('outputs/short_term_summary.xlsx', index=False)

print("  ✓ outputs/short_term_reactions.xlsx")
print("  ✓ outputs/short_term_summary.xlsx")
print()

print("="*80)
print("ANALYSIS COMPLETE")
print("="*80)
