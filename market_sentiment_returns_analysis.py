"""
=============================================================================
SCRIPT NAME: market_sentiment_returns_analysis.py
=============================================================================

INPUT FILES:
- Data Collection and Cleaning/market_sentiment_classified.csv: Classified tweets
- SPY_5min_history.xlsx: S&P 500 ETF 5-minute price data

OUTPUT FILES:
- outputs/market_sentiment_returns.xlsx: Detailed returns by sentiment type
- outputs/market_sentiment_summary.xlsx: Aggregate statistics
- outputs/market_sentiment_report.txt: Comprehensive findings

VERSION: 1.0
LAST UPDATED: 2025-10-20
AUTHOR: Claude Code

DESCRIPTION:
Analyzes market returns around tweets classified as MARKET_FRIENDLY,
MARKET_HOSTILE, or NEUTRAL across multiple time windows:
- T-1: Day before (baseline)
- T+30min: Immediate reaction
- T+1: Same day / next day
- T+5: 5 trading days
- T+10: 10 trading days

Tests hypothesis that:
- MARKET_HOSTILE tweets cause negative returns
- MARKET_FRIENDLY tweets cause positive returns
- NEUTRAL tweets have no effect

DEPENDENCIES:
- pandas
- numpy
- openpyxl
- scipy
- datetime

USAGE:
python market_sentiment_returns_analysis.py

NOTES:
- Uses 5-minute bars for intraday (30-min)
- Uses daily close-to-close for multi-day windows
- All tweets included (no filters)
=============================================================================
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ==================== SETUP ====================

print("="*80)
print("MARKET SENTIMENT RETURNS ANALYSIS")
print("Analyzing -1 day, 30-min, 1-day, 5-day, 10-day returns")
print("="*80)
print()

os.makedirs('outputs', exist_ok=True)

# ==================== LOAD DATA ====================

print("[1/5] Loading market data...")

def load_market_data(filepath):
    """Load and prepare 5-minute market data"""
    df = pd.read_excel(filepath)
    df.columns = df.columns.str.lower()

    if 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'])
    elif 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])

    rename_map = {}
    for col in df.columns:
        if col in ['open', 'high', 'low', 'close', 'volume']:
            rename_map[col] = col.capitalize()

    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    df.set_index('datetime', inplace=True)
    df = df.sort_index()

    return df

spy_data = load_market_data('SPY_5min_history.xlsx')
print(f"  ✓ SPY data loaded: {len(spy_data)} 5-minute bars")
print(f"    Date range: {spy_data.index.min()} to {spy_data.index.max()}")

# Create daily data for multi-day analysis
spy_daily = spy_data.resample('D').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

print(f"  ✓ SPY daily data: {len(spy_daily)} trading days")
print()

# ==================== LOAD CLASSIFIED TWEETS ====================

print("[2/5] Loading classified tweets...")

tweets_df = pd.read_csv('Data Collection and Cleaning/market_sentiment_classified.csv')
print(f"  ✓ Loaded {len(tweets_df)} classified tweets")

# Parse timestamps
tweets_with_dates = []
for idx, tweet in tweets_df.iterrows():
    try:
        if pd.notna(tweet.get('created_at')) and tweet.get('created_at') != '':
            ts = pd.to_datetime(tweet['created_at'])
            tweets_with_dates.append({
                'datetime': ts,
                'content': tweet.get('content', ''),
                'market_sentiment': tweet.get('market_sentiment', 'NEUTRAL'),
                'confidence': tweet.get('classification_confidence', 0),
                'reasoning': tweet.get('classification_reasoning', ''),
                'key_topics': tweet.get('key_topics', []),
            })
    except:
        continue

tweets_df_parsed = pd.DataFrame(tweets_with_dates)
tweets_df_parsed = tweets_df_parsed.sort_values('datetime').reset_index(drop=True)

print(f"  ✓ Tweets with valid timestamps: {len(tweets_df_parsed)}")
print(f"    Date range: {tweets_df_parsed['datetime'].min()} to {tweets_df_parsed['datetime'].max()}")
print()

# Show sentiment breakdown
print("  Market sentiment breakdown:")
for sentiment, count in tweets_df_parsed['market_sentiment'].value_counts().items():
    print(f"    {sentiment}: {count}")
print()

# ==================== CALCULATE RETURNS ====================

print("[3/5] Calculating returns for all time windows...")

def get_trading_day(date, offset_days, daily_data):
    """Get trading day that is offset_days away from date"""
    target_date = date + timedelta(days=offset_days)

    # Find closest trading day
    if offset_days < 0:
        # Look backwards
        nearby = daily_data[daily_data.index <= target_date]
        if len(nearby) > 0:
            return nearby.index[-1]
    else:
        # Look forwards
        nearby = daily_data[daily_data.index >= target_date]
        if len(nearby) > 0:
            return nearby.index[0]

    return None

def calculate_all_returns(event_time, spy_5min, spy_daily):
    """Calculate returns across all time windows"""

    result = {
        'event_time': event_time,
        'return_minus_1d': np.nan,
        'return_30min': np.nan,
        'return_1d': np.nan,
        'return_5d': np.nan,
        'return_10d': np.nan,
    }

    event_date = event_time.date()

    # -1 DAY RETURN (day before tweet)
    t_minus_2 = get_trading_day(event_time, -2, spy_daily)
    t_minus_1 = get_trading_day(event_time, -1, spy_daily)

    if t_minus_2 and t_minus_1:
        close_t2 = spy_daily.loc[t_minus_2, 'Close']
        close_t1 = spy_daily.loc[t_minus_1, 'Close']
        result['return_minus_1d'] = ((close_t1 / close_t2) - 1) * 100

    # 30-MINUTE RETURN
    post_start = event_time
    post_end = event_time + timedelta(minutes=35)
    post_data = spy_5min[(spy_5min.index >= post_start) & (spy_5min.index <= post_end)]

    if len(post_data) >= 2:
        start_price = post_data.iloc[0]['Close']
        target_time = event_time + timedelta(minutes=30)
        nearby = post_data[(post_data.index >= target_time - timedelta(minutes=2)) &
                          (post_data.index <= target_time + timedelta(minutes=3))]

        if len(nearby) > 0:
            end_price = nearby.iloc[0]['Close']
            result['return_30min'] = ((end_price / start_price) - 1) * 100

    # 1-DAY RETURN (T+0 to T+1)
    t0 = get_trading_day(event_time, 0, spy_daily)
    t1 = get_trading_day(event_time, 1, spy_daily)

    if t0 and t1:
        close_t0 = spy_daily.loc[t0, 'Close']
        close_t1 = spy_daily.loc[t1, 'Close']
        result['return_1d'] = ((close_t1 / close_t0) - 1) * 100

    # 5-DAY RETURN (T+0 to T+5)
    t5 = get_trading_day(event_time, 5, spy_daily)

    if t0 and t5:
        close_t0 = spy_daily.loc[t0, 'Close']
        close_t5 = spy_daily.loc[t5, 'Close']
        result['return_5d'] = ((close_t5 / close_t0) - 1) * 100

    # 10-DAY RETURN (T+0 to T+10)
    t10 = get_trading_day(event_time, 10, spy_daily)

    if t0 and t10:
        close_t0 = spy_daily.loc[t0, 'Close']
        close_t10 = spy_daily.loc[t10, 'Close']
        result['return_10d'] = ((close_t10 / close_t0) - 1) * 100

    return result

# Calculate for all tweets
all_returns = []

for idx, tweet in tweets_df_parsed.iterrows():
    returns = calculate_all_returns(tweet['datetime'], spy_data, spy_daily)
    returns.update({
        'content_preview': tweet['content'][:100],
        'market_sentiment': tweet['market_sentiment'],
        'confidence': tweet['confidence'],
        'key_topics': str(tweet['key_topics'])[:100],
    })
    all_returns.append(returns)

    if (idx + 1) % 500 == 0:
        print(f"    Processed: {idx+1}/{len(tweets_df_parsed)}")

returns_df = pd.DataFrame(all_returns)
print(f"  ✓ All tweets processed: {len(returns_df)}")
print()

# ==================== ANALYZE BY SENTIMENT ====================

print("[4/5] Analyzing by market sentiment...")
print()

sentiments = ['MARKET_FRIENDLY', 'MARKET_HOSTILE', 'NEUTRAL']
time_windows = [
    ('return_minus_1d', '-1 Day (Before Tweet)'),
    ('return_30min', '30 Minutes'),
    ('return_1d', '1 Day'),
    ('return_5d', '5 Days'),
    ('return_10d', '10 Days'),
]

print("="*80)
print("RESULTS BY SENTIMENT TYPE")
print("="*80)
print()

summary_stats = []

for sentiment in sentiments:
    sentiment_data = returns_df[returns_df['market_sentiment'] == sentiment]

    if len(sentiment_data) == 0:
        continue

    print(f"{sentiment}")
    print("-"*80)
    print(f"Total events: {len(sentiment_data)}")
    print()

    for return_col, window_name in time_windows:
        returns = sentiment_data[return_col].dropna()

        if len(returns) < 3:
            print(f"  {window_name}: Insufficient data (N={len(returns)})")
            continue

        mean_return = returns.mean()
        median_return = returns.median()
        std_return = returns.std()
        pct_negative = (returns < 0).sum() / len(returns) * 100

        # T-test
        t_stat, p_value = stats.ttest_1samp(returns, 0)

        print(f"  {window_name} (N={len(returns)}):")
        print(f"    Mean:        {mean_return:>8.3f}%")
        print(f"    Median:      {median_return:>8.3f}%")
        print(f"    Std Dev:     {std_return:>8.3f}%")
        print(f"    % Negative:  {pct_negative:>8.1f}%")
        print(f"    t-stat:      {t_stat:>8.3f}")
        print(f"    p-value:     {p_value:>8.4f}")

        if p_value < 0.05:
            direction = "POSITIVE" if mean_return > 0 else "NEGATIVE"
            print(f"    ✓ SIGNIFICANT {direction}")
        else:
            print(f"    ✗ Not significant")
        print()

        # Save for summary
        summary_stats.append({
            'Sentiment': sentiment,
            'Time_Window': window_name,
            'N': len(returns),
            'Mean': mean_return,
            'Median': median_return,
            'Std_Dev': std_return,
            'Pct_Negative': pct_negative,
            't_stat': t_stat,
            'p_value': p_value,
            'Significant': 'Yes' if p_value < 0.05 else 'No',
        })

    print()

# ==================== PAIRWISE COMPARISONS ====================

print("="*80)
print("PAIRWISE COMPARISONS (HOSTILE vs FRIENDLY)")
print("="*80)
print()

hostile_data = returns_df[returns_df['market_sentiment'] == 'MARKET_HOSTILE']
friendly_data = returns_df[returns_df['market_sentiment'] == 'MARKET_FRIENDLY']

for return_col, window_name in time_windows:
    hostile_returns = hostile_data[return_col].dropna()
    friendly_returns = friendly_data[return_col].dropna()

    if len(hostile_returns) >= 3 and len(friendly_returns) >= 3:
        t_stat, p_value = stats.ttest_ind(hostile_returns, friendly_returns)

        print(f"{window_name}:")
        print(f"  HOSTILE mean:   {hostile_returns.mean():>8.3f}%")
        print(f"  FRIENDLY mean:  {friendly_returns.mean():>8.3f}%")
        print(f"  Difference:     {hostile_returns.mean() - friendly_returns.mean():>8.3f}%")
        print(f"  t-statistic:    {t_stat:>8.3f}")
        print(f"  p-value:        {p_value:>8.4f}")

        if p_value < 0.05:
            better = "FRIENDLY" if friendly_returns.mean() > hostile_returns.mean() else "HOSTILE"
            print(f"  ✓ SIGNIFICANT difference ({better} higher)")
        else:
            print(f"  ✗ NO significant difference")
        print()

# ==================== SAVE RESULTS ====================

print("[5/5] Saving results...")
print()

# Detailed returns
returns_df.to_excel('outputs/market_sentiment_returns.xlsx', index=False)
print("  ✓ outputs/market_sentiment_returns.xlsx")

# Summary statistics
summary_df = pd.DataFrame(summary_stats)
summary_df.to_excel('outputs/market_sentiment_summary.xlsx', index=False)
print("  ✓ outputs/market_sentiment_summary.xlsx")

print()
print("="*80)
print("ANALYSIS COMPLETE")
print("="*80)
