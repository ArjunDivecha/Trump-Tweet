"""
=============================================================================
SCRIPT NAME: market_sentiment_classifier_local.py
=============================================================================

Uses LM Studio with qwen3-coder-30b-a3b-instruct local model instead of API.
Much faster and free!

INPUT FILES:
- trump_truth_archive_clean.csv: All cleaned Trump tweets

OUTPUT FILES:
- market_sentiment_classified.json: All tweets with market sentiment classification
- market_sentiment_classified.csv: CSV version
- market_classification_checkpoint.json: Resume capability
- market_classification_log.txt: Processing log

VERSION: 2.0 (Local Model)
LAST UPDATED: 2025-10-20
AUTHOR: Claude Code

USAGE:
python market_sentiment_classifier_local.py [--resume]

NOTES:
- Requires LM Studio running on localhost:1234
- Batch size: 10 tweets per call
- Can resume from checkpoint
=============================================================================
"""

import pandas as pd
import json
import sys
import os
from datetime import datetime
import time
import requests

# ==================== SETUP ====================

RESUME_MODE = '--resume' in sys.argv

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

CHECKPOINT_FILE = 'market_classification_checkpoint.json'
OUTPUT_JSON = 'market_sentiment_classified.json'
OUTPUT_CSV = 'market_sentiment_classified.csv'
LOG_FILE = 'market_classification_log.txt'

BATCH_SIZE = 10

# ==================== LOGGING ====================

def log(message):
    """Write to both console and log file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')

# ==================== LOAD DATA ====================

log("="*80)
log("MARKET SENTIMENT CLASSIFIER - LOCAL MODEL (LM Studio)")
log("="*80)
log("")

log("Loading tweet data...")
tweets_df = pd.read_csv('trump_truth_archive_clean.csv')
log(f"✓ Loaded {len(tweets_df)} tweets")

# Check for valid dates
valid_dates = tweets_df[tweets_df['created_at'].notna() & (tweets_df['created_at'] != '')]
if len(valid_dates) > 0:
    log(f"  Tweets with valid dates: {len(valid_dates)}")
else:
    log(f"  Warning: No valid dates found in created_at column")
log("")

# ==================== RESUME LOGIC ====================

processed_tweets = []
start_index = 0

if RESUME_MODE and os.path.exists(CHECKPOINT_FILE):
    log("Resume mode: Loading checkpoint...")
    with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
        checkpoint = json.load(f)
        processed_tweets = checkpoint['processed_tweets']
        start_index = checkpoint['last_index'] + 1
    log(f"✓ Resuming from index {start_index}")
    log(f"  Already processed: {len(processed_tweets)} tweets")
    log("")

# ==================== CLASSIFICATION PROMPT ====================

SYSTEM_PROMPT = """You are a financial market analyst classifying Trump's tweets by their expected market impact.

CLASSIFICATION CATEGORIES:

1. MARKET_FRIENDLY
- Pro-business policies (tax cuts, deregulation)
- Positive economic announcements (jobs, GDP, stock market gains)
- Trade deal progress or completion
- Infrastructure spending
- Energy independence (domestic production)
- Federal Reserve dovish signals
- Peace/stability in geopolitical conflicts

2. MARKET_HOSTILE
- Trade wars, tariffs, sanctions (ANY country)
- Geopolitical tensions, military threats
- Regulatory crackdowns on corporations
- Federal Reserve criticism (hawkish direction)
- Breaking international agreements
- Immigration crackdowns affecting labor
- Government shutdowns

3. NEUTRAL
- Political commentary (elections, opponents)
- Social/cultural issues (not economic)
- Personal attacks or grievances
- Sports, entertainment, personal life
- Domestic policy without economic impact

IMPORTANT:
- Focus on IMMEDIATE market reaction potential
- Trade/tariff content is ALWAYS market hostile
- Uncertainty and unpredictability are market hostile
- Default to NEUTRAL if ambiguous
- Be consistent across similar tweet types"""

USER_PROMPT_TEMPLATE = """Classify these {count} tweets as MARKET_FRIENDLY, MARKET_HOSTILE, or NEUTRAL.

Return ONLY valid JSON array with this exact structure:
[
  {{
    "index": 0,
    "classification": "MARKET_FRIENDLY",
    "confidence": 85,
    "reasoning": "Brief explanation",
    "key_topics": ["topic1", "topic2"]
  }}
]

Tweets to classify:
{tweets_text}"""

# ==================== BATCH CLASSIFICATION ====================

def classify_batch(batch_tweets):
    """Classify a batch of tweets using LM Studio"""

    # Format tweets for prompt
    tweets_text = ""
    for i, tweet in enumerate(batch_tweets):
        content = tweet.get('content', '')[:500]
        tweets_text += f"\n[{i}] {content}\n"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        count=len(batch_tweets),
        tweets_text=tweets_text
    )

    payload = {
        "model": "qwen3-coder-30b-a3b-instruct",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4000
    }

    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        response_text = result['choices'][0]['message']['content'].strip()

        # Extract JSON from response
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()

        classifications = json.loads(response_text)

        # Merge classifications with original tweets
        results = []
        for i, tweet in enumerate(batch_tweets):
            classification = next((c for c in classifications if c['index'] == i), None)

            if classification:
                result = tweet.copy()
                result['market_sentiment'] = classification['classification']
                result['classification_confidence'] = classification['confidence']
                result['classification_reasoning'] = classification['reasoning']
                result['key_topics'] = classification.get('key_topics', [])
                results.append(result)
            else:
                # Failed to classify this tweet
                result = tweet.copy()
                result['market_sentiment'] = 'NEUTRAL'
                result['classification_confidence'] = 0
                result['classification_reasoning'] = 'ERROR: No classification returned'
                result['key_topics'] = []
                results.append(result)

        return results, None

    except Exception as e:
        error_msg = f"API Error: {str(e)}"
        log(f"  ✗ {error_msg}")
        return None, error_msg

# ==================== MAIN PROCESSING LOOP ====================

log(f"Starting classification from index {start_index}...")
log(f"Total tweets to process: {len(tweets_df) - start_index}")
log("")

tweets_to_process = tweets_df.iloc[start_index:].to_dict('records')
total_batches = (len(tweets_to_process) + BATCH_SIZE - 1) // BATCH_SIZE

for batch_num in range(total_batches):
    batch_start = batch_num * BATCH_SIZE
    batch_end = min(batch_start + BATCH_SIZE, len(tweets_to_process))
    batch = tweets_to_process[batch_start:batch_end]

    actual_index = start_index + batch_start

    log(f"Batch {batch_num + 1}/{total_batches} (tweets {actual_index} to {actual_index + len(batch) - 1})")

    # Classify batch
    results, error = classify_batch(batch)

    if results:
        processed_tweets.extend(results)
        log(f"  ✓ Classified {len(results)} tweets")

        # Show sample classification
        sample = results[0]
        log(f"  Sample: '{sample.get('content', '')[:80]}...'")
        log(f"    → {sample['market_sentiment']} ({sample['classification_confidence']}% confidence)")
    else:
        log(f"  ✗ Batch failed: {error}")
        log(f"  Skipping batch and continuing...")

    # Save checkpoint
    checkpoint = {
        'last_index': actual_index + len(batch) - 1,
        'processed_tweets': processed_tweets,
        'timestamp': datetime.now().isoformat()
    }

    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)

    log(f"  ✓ Checkpoint saved")
    log("")

    # Small delay to avoid overloading local model
    time.sleep(0.1)

# ==================== SAVE FINAL RESULTS ====================

log("="*80)
log("CLASSIFICATION COMPLETE")
log("="*80)
log("")

log(f"Total tweets classified: {len(processed_tweets)}")

# Count by classification
classifications_count = {}
for tweet in processed_tweets:
    classification = tweet.get('market_sentiment', 'UNKNOWN')
    classifications_count[classification] = classifications_count.get(classification, 0) + 1

log("")
log("Classification breakdown:")
for classification, count in sorted(classifications_count.items(), key=lambda x: -x[1]):
    pct = count / len(processed_tweets) * 100
    log(f"  {classification}: {count} ({pct:.1f}%)")

log("")
log("Saving results...")

# Save JSON
with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(processed_tweets, f, indent=2, ensure_ascii=False)
log(f"  ✓ {OUTPUT_JSON}")

# Save CSV
results_df = pd.DataFrame(processed_tweets)
results_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
log(f"  ✓ {OUTPUT_CSV}")

log("")
log("✓ ALL COMPLETE")
log("")
