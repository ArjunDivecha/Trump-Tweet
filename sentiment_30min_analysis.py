"""
=============================================================================
SCRIPT NAME: sentiment_30min_analysis.py
=============================================================================

INPUT FILES:
- SPY_5min_history.xlsx: S&P 500 ETF 5-minute price data
- Data Collection and Cleaning/tariff_classified_tweets_full_v5.json: All tariff tweets

OUTPUT FILES:
- outputs/sentiment_30min_results.xlsx: Detailed 30-min reactions by sentiment
- outputs/sentiment_30min_summary.xlsx: Aggregate statistics by sentiment type

VERSION: 1.0
LAST UPDATED: 2025-10-20
AUTHOR: Claude Code

DESCRIPTION:
Simple analysis of ALL tariff-related tweets, segmented by sentiment type:
- Aggressive: Hostile, threatening language
- Defensive: Justifying or explaining tariffs
- Informational: Factual statements about tariffs

Measures 30-minute market reaction for each sentiment category.

HYPOTHESIS:
- Aggressive tweets cause market drops
- Defensive/Informational tweets have neutral/positive reactions

DEPENDENCIES:
- pandas
- numpy
- openpyxl
- json
- datetime
- scipy

USAGE:
python sentiment_30min_analysis.py

NOTES:
- No filters: ALL tariff tweets included
- No date restrictions
- No country restrictions
- Simple 30-minute window only
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
print("SENTIMENT-BASED 30-MINUTE REACTION ANALYSIS")
print("ALL Tariff Tweets by Sentiment Type")
print("="*80)
print()

os.makedirs('outputs', exist_ok=True)

# ==================== LOAD DATA ====================

print("[1/4] Loading market data...")

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
print()

# ==================== LOAD TARIFF TWEETS ====================

print("[2/4] Loading ALL tariff tweets...")

with open('Data Collection and Cleaning/tariff_classified_tweets_full_v5.json', 'r') as f:
    tweets_data = json.load(f)

tweets_df = pd.DataFrame(tweets_data)

# Filter to tariff-related only
tariff_tweets = tweets_df[tweets_df['is_tariff_related'] == True].copy()
print(f"  ✓ Total tariff-related tweets: {len(tariff_tweets)}")

# Parse timestamps
tariff_events = []

for idx, tweet in tariff_tweets.iterrows():
    try:
        if pd.notna(tweet.get('created_at')) and tweet.get('created_at'):
            ts = pd.to_datetime(tweet['created_at'])
        elif pd.notna(tweet.get('timestamp')) and tweet.get('timestamp'):
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
        })
    except:
        continue

tariff_df = pd.DataFrame(tariff_events)
tariff_df = tariff_df.sort_values('datetime').reset_index(drop=True)

print(f"  ✓ Tweets with valid timestamps: {len(tariff_df)}")
print(f"    Date range: {tariff_df['datetime'].min()} to {tariff_df['datetime'].max()}")
print()

# Show sentiment breakdown
print("  Sentiment breakdown:")
for sentiment, count in tariff_df['sentiment'].value_counts().items():
    print(f"    {sentiment}: {count}")
print()

# ==================== CALCULATE 30-MIN REACTIONS ====================

print("[3/4] Calculating 30-minute reactions for all events...")

def calculate_30min_reaction(event_time, market_data):
    """
    Calculate 30-minute cumulative return after event

    Args:
        event_time: datetime of tweet
        market_data: DataFrame with 5-minute bars

    Returns:
        dict with 30-min return and baseline
    """
    result = {
        'event_time': event_time,
        'baseline_return': np.nan,
        'cumulative_30min': np.nan,
        'has_data': False,
    }

    # Get baseline: 30 minutes before event
    baseline_start = event_time - timedelta(minutes=35)
    baseline_end = event_time - timedelta(minutes=5)
    baseline_data = market_data[(market_data.index >= baseline_start) &
                                (market_data.index < baseline_end)]

    if len(baseline_data) > 1:
        baseline_returns = baseline_data['Close'].pct_change().dropna()
        if len(baseline_returns) > 0:
            result['baseline_return'] = baseline_returns.mean() * 100

    # Get post-event data (next 35 minutes)
    post_start = event_time
    post_end = event_time + timedelta(minutes=35)
    post_data = market_data[(market_data.index >= post_start) &
                            (market_data.index <= post_end)]

    if len(post_data) < 2:
        return result

    # Get starting price
    start_price = post_data.iloc[0]['Close']

    # Calculate 30-minute cumulative return
    target_time = event_time + timedelta(minutes=30)
    nearby_data = post_data[(post_data.index >= target_time - timedelta(minutes=2)) &
                            (post_data.index <= target_time + timedelta(minutes=3))]

    if len(nearby_data) > 0:
        end_price = nearby_data.iloc[0]['Close']
        cumulative_return = ((end_price / start_price) - 1) * 100
        result['cumulative_30min'] = cumulative_return
        result['has_data'] = True

    return result

# Calculate for all events
all_reactions = []

for idx, event in tariff_df.iterrows():
    reaction = calculate_30min_reaction(event['datetime'], spy_data)
    reaction.update({
        'post_id': event['post_id'],
        'sentiment': event['sentiment'],
        'content_preview': event['content'][:100],
        'tariff_action_type': event['tariff_action_type'],
        'tariff_type': event['tariff_type'],
        'countries': str(event['countries_mentioned'])[:50],
        'tariff_percentage': event['tariff_percentage'],
        'confidence': event['confidence'],
    })
    all_reactions.append(reaction)

    if (idx + 1) % 50 == 0:
        print(f"    Processed: {idx+1}/{len(tariff_df)}")

reactions_df = pd.DataFrame(all_reactions)
print(f"  ✓ All events processed: {len(reactions_df)}")

# Filter to events with market data
reactions_with_data = reactions_df[reactions_df['has_data'] == True].copy()
print(f"  ✓ Events with 30-min market data: {len(reactions_with_data)}")
print()

# ==================== ANALYZE BY SENTIMENT ====================

print("[4/4] Analyzing by sentiment type...")
print()

# Get the three main sentiment types
sentiments = ['Aggressive', 'Defensive', 'Informational']

print("="*80)
print("RESULTS BY SENTIMENT TYPE")
print("="*80)
print()

summary_stats = []

for sentiment in sentiments:
    sentiment_data = reactions_with_data[reactions_with_data['sentiment'] == sentiment]

    if len(sentiment_data) == 0:
        print(f"{sentiment.upper()}: No data")
        print()
        continue

    returns = sentiment_data['cumulative_30min'].dropna()

    if len(returns) == 0:
        print(f"{sentiment.upper()}: No valid returns")
        print()
        continue

    print(f"{sentiment.upper()} (N={len(returns)})")
    print("-"*80)

    mean_return = returns.mean()
    median_return = returns.median()
    std_return = returns.std()
    pct_negative = (returns < 0).sum() / len(returns) * 100
    pct_positive = (returns > 0).sum() / len(returns) * 100

    print(f"  Mean return:       {mean_return:>8.3f}%")
    print(f"  Median return:     {median_return:>8.3f}%")
    print(f"  Std deviation:     {std_return:>8.3f}%")
    print(f"  % Negative:        {pct_negative:>8.1f}%")
    print(f"  % Positive:        {pct_positive:>8.1f}%")
    print(f"  Min return:        {returns.min():>8.3f}%")
    print(f"  Max return:        {returns.max():>8.3f}%")

    # One-sample t-test: Is mean significantly different from 0?
    if len(returns) >= 3:
        t_stat, p_value = stats.ttest_1samp(returns, 0)

        print(f"\n  Hypothesis Test (H0: mean = 0):")
        print(f"  t-statistic:       {t_stat:>8.3f}")
        print(f"  p-value (2-sided): {p_value:>8.4f}")

        if p_value < 0.05:
            direction = "POSITIVE" if mean_return > 0 else "NEGATIVE"
            print(f"  Result:            ✓ SIGNIFICANT {direction} reaction (α=0.05)")
        else:
            print(f"  Result:            ✗ NOT significant (α=0.05)")

        # One-sided test for negative
        if t_stat < 0:
            p_value_negative = p_value / 2
        else:
            p_value_negative = 1 - (p_value / 2)

        print(f"\n  One-sided test (H1: mean < 0):")
        print(f"  p-value:           {p_value_negative:>8.4f}")

        if p_value_negative < 0.05:
            print(f"  Result:            ✓ SIGNIFICANT negative reaction (α=0.05)")
        else:
            print(f"  Result:            ✗ NOT significant (α=0.05)")

    print()

    # Save summary stats
    summary_stats.append({
        'Sentiment': sentiment,
        'N': len(returns),
        'Mean_Return': mean_return,
        'Median_Return': median_return,
        'Std_Dev': std_return,
        'Pct_Negative': pct_negative,
        'Pct_Positive': pct_positive,
        'Min_Return': returns.min(),
        'Max_Return': returns.max(),
    })

# ==================== PAIRWISE COMPARISONS ====================

print("="*80)
print("PAIRWISE COMPARISONS")
print("="*80)
print()

comparisons = [
    ('Aggressive', 'Defensive'),
    ('Aggressive', 'Informational'),
    ('Defensive', 'Informational'),
]

for sent1, sent2 in comparisons:
    data1 = reactions_with_data[reactions_with_data['sentiment'] == sent1]['cumulative_30min'].dropna()
    data2 = reactions_with_data[reactions_with_data['sentiment'] == sent2]['cumulative_30min'].dropna()

    if len(data1) >= 3 and len(data2) >= 3:
        t_stat, p_value = stats.ttest_ind(data1, data2)

        print(f"{sent1} vs {sent2}:")
        print(f"  {sent1} mean:      {data1.mean():>8.3f}%")
        print(f"  {sent2} mean:      {data2.mean():>8.3f}%")
        print(f"  Difference:        {data1.mean() - data2.mean():>8.3f}%")
        print(f"  t-statistic:       {t_stat:>8.3f}")
        print(f"  p-value:           {p_value:>8.4f}")

        if p_value < 0.05:
            better = sent1 if data1.mean() > data2.mean() else sent2
            print(f"  Result:            ✓ SIGNIFICANT difference (α=0.05) - {better} higher")
        else:
            print(f"  Result:            ✗ NO significant difference (α=0.05)")
        print()

# ==================== SAVE RESULTS ====================

print("Saving results to Excel...")

# Detailed reactions
reactions_with_data.to_excel('outputs/sentiment_30min_results.xlsx', index=False)

# Summary statistics
summary_df = pd.DataFrame(summary_stats)
summary_df.to_excel('outputs/sentiment_30min_summary.xlsx', index=False)

print("  ✓ outputs/sentiment_30min_results.xlsx")
print("  ✓ outputs/sentiment_30min_summary.xlsx")
print()

print("="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print()

# Print quick summary
print("QUICK SUMMARY:")
for stat in summary_stats:
    print(f"  {stat['Sentiment']:15s} (N={stat['N']:>3}): Mean = {stat['Mean_Return']:>7.3f}%, Negative = {stat['Pct_Negative']:>5.1f}%")
