"""
=============================================================================
SCRIPT NAME: market_sentiment_classifier.py
=============================================================================

INPUT FILES:
- trump_truth_archive_clean.csv: All cleaned Trump tweets

OUTPUT FILES:
- market_sentiment_classified.json: All tweets with market sentiment classification
- market_sentiment_classified.csv: CSV version for easy viewing
- market_classification_checkpoint.json: Resume capability
- market_classification_log.txt: Processing log

VERSION: 1.0
LAST UPDATED: 2025-10-20
AUTHOR: Claude Code

DESCRIPTION:
Classifies ALL Trump tweets as:
- MARKET_FRIENDLY: Pro-business, positive economic news, deal announcements
- MARKET_HOSTILE: Trade wars, sanctions, regulatory threats, geopolitical tensions
- NEUTRAL: Political, social, personal content with no market impact

Uses Claude Sonnet 4.5 API for classification with batch processing.

DEPENDENCIES:
- anthropic
- pandas
- json

USAGE:
python market_sentiment_classifier.py YOUR_ANTHROPIC_API_KEY [--resume]

NOTES:
- Batch size: 10 tweets per API call
- Cost estimate: ~$10-15 for 2,500 tweets
- Checkpoint saves progress every batch
- Can resume interrupted runs
=============================================================================
"""

import anthropic
import pandas as pd
import json
import sys
import os
from datetime import datetime
import time

# ==================== SETUP ====================

if len(sys.argv) < 2:
    print("Usage: python market_sentiment_classifier.py YOUR_API_KEY [--resume]")
    sys.exit(1)

API_KEY = sys.argv[1]
RESUME_MODE = '--resume' in sys.argv

client = anthropic.Anthropic(api_key=API_KEY)

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
log("MARKET SENTIMENT CLASSIFIER - ALL TRUMP TWEETS")
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
- Examples:
  * "Just signed the biggest tax cut in history!"
  * "Stock market hits all-time high!"
  * "Great trade deal with China!"
  * "Unemployment at record lows!"

2. MARKET_HOSTILE
- Trade wars, tariffs, sanctions (ANY country)
- Geopolitical tensions, military threats
- Regulatory crackdowns on corporations
- Federal Reserve criticism (hawkish direction)
- Breaking international agreements
- Immigration crackdowns affecting labor
- Government shutdowns
- Examples:
  * "Imposing 25% tariffs on China effective immediately"
  * "Sanctions on Russia will be severe"
  * "Breaking up big tech monopolies"
  * "Fed is making a terrible mistake raising rates"

3. NEUTRAL
- Political commentary (elections, opponents)
- Social/cultural issues (not economic)
- Personal attacks or grievances
- Sports, entertainment, personal life
- Domestic policy without economic impact
- General announcements
- Examples:
  * "Crooked Hillary should be in jail"
  * "Fake news media is the enemy of the people"
  * "Congratulations to Tom Brady!"
  * "Happy Thanksgiving to all Americans!"

IMPORTANT:
- Focus on IMMEDIATE market reaction potential
- Trade/tariff content is ALWAYS market hostile (even if "reciprocal" or "fair")
- Uncertainty and unpredictability are market hostile
- Default to NEUTRAL if ambiguous
- Be consistent across similar tweet types"""

USER_PROMPT_TEMPLATE = """Classify these {count} tweets as MARKET_FRIENDLY, MARKET_HOSTILE, or NEUTRAL.

Return ONLY valid JSON array with this exact structure:
[
  {{
    "index": 0,
    "classification": "MARKET_FRIENDLY or MARKET_HOSTILE or NEUTRAL",
    "confidence": 85,
    "reasoning": "Brief explanation of classification",
    "key_topics": ["topic1", "topic2"]
  }},
  ...
]

Tweets to classify:
{tweets_text}"""

# ==================== BATCH CLASSIFICATION ====================

def classify_batch(batch_tweets):
    """Classify a batch of tweets using Claude API"""

    # Format tweets for prompt
    tweets_text = ""
    for i, tweet in enumerate(batch_tweets):
        content = tweet.get('content', '')[:500]  # Truncate very long tweets
        tweets_text += f"\n[{i}] {content}\n"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        count=len(batch_tweets),
        tweets_text=tweets_text
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": user_prompt
            }]
        )

        response_text = message.content[0].text.strip()

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
                result['key_topics'] = classification['key_topics']
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

    # Rate limiting
    if batch_num < total_batches - 1:
        time.sleep(1)

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
