#!/usr/bin/env python3
"""
Clean Trump Truth Archive JSON - FIXED VERSION
===============================================

INPUT FILES:
- trump_truth_archive.json: Raw scraped data with concatenated posts

OUTPUT FILES:
- trump_truth_archive_clean.json: Cleaned individual posts
- trump_truth_archive_clean.csv: Cleaned CSV format
- cleaning_log.txt: Cleaning process log
- duplicate_dates_report.txt: Report of posts with multiple dates

This script cleans the Trump Truth archive JSON file by:
1. Parsing concatenated posts into individual entries
2. Removing duplicate content (KEEPING EARLIEST DATE)
3. Extracting proper post content
4. Filtering out navigation elements
5. Validating and normalizing dates

Version: 2.0 (FIXED)
Last Updated: 2025-10-20

FIXES APPLIED:
- ✅ Bug #1: Now keeps EARLIEST date for duplicate posts
- ✅ Bug #2: Removed redundant deduplication
- ✅ Bug #3: Added date validation
- ✅ Bug #4: Post IDs use earliest kept date
"""

import json
import csv
import re
from datetime import datetime
from collections import OrderedDict

def validate_and_parse_date(date_str):
    """
    Validate and parse date string, return datetime object or None

    Handles multiple formats:
    - ISO format: 2025-10-18T18:57:00
    - Date only: 2025-10-18
    - Empty/invalid: returns None
    """
    if not date_str or date_str.strip() == '':
        return None

    try:
        # Try ISO format first
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # Try date-only format
            return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        # If all parsing fails, return None
        return None

def clean_content(content):
    """Clean and extract individual posts from concatenated content"""
    if not content:
        return []

    # Split by "Donald J. Trump" to separate individual posts
    posts = re.split(r'Donald J\. Trump', content)

    cleaned_posts = []
    for post in posts:
        post = post.strip()
        if not post:
            continue

        # Skip navigation elements
        if any(skip in post.lower() for skip in [
            'search the archive', 'about the site', 'faq', 'items per page',
            'prev. page', 'next page', 'trump\'s truth is an archive',
            'defending democracy together', 'start date:', 'end date:',
            'filter', 'sort by:', 'per page'
        ]):
            continue

        # Skip very short posts (likely navigation)
        if len(post) < 50:
            continue

        # Skip posts that are mostly URLs
        if post.count('http') > len(post.split()) * 0.3:
            continue

        # Clean up the post content
        post = re.sub(r'\s+', ' ', post)  # Normalize whitespace
        post = post.strip()

        if post:
            cleaned_posts.append(post)

    return cleaned_posts

def extract_individual_posts(json_data, log_func):
    """
    Extract individual posts from the JSON data

    FIXED VERSION: Keeps EARLIEST date for duplicate posts
    """
    # Dictionary to track posts: {content: post_data_dict}
    seen_posts = {}
    duplicate_date_log = []

    for entry_idx, entry in enumerate(json_data):
        content = entry.get('content', '')
        timestamp = entry.get('timestamp', '')
        created_at = entry.get('created_at', '')
        date = entry.get('date', '')
        username = entry.get('username', '@realDonaldTrump')

        # Clean the content to extract individual posts
        cleaned_posts = clean_content(content)

        for i, post_content in enumerate(cleaned_posts):
            # Check if we've seen this content before
            if post_content in seen_posts:
                # DUPLICATE FOUND - Compare dates to keep earliest
                existing_post = seen_posts[post_content]
                existing_date_obj = validate_and_parse_date(existing_post.get('created_at', ''))
                current_date_obj = validate_and_parse_date(created_at)

                # Determine which date to keep
                should_replace = False

                if current_date_obj and existing_date_obj:
                    # Both have valid dates - keep earlier one
                    if current_date_obj < existing_date_obj:
                        should_replace = True
                        duplicate_date_log.append({
                            'content_preview': post_content[:100],
                            'old_date': existing_post.get('created_at'),
                            'new_date': created_at,
                            'action': 'REPLACED (new is earlier)'
                        })
                elif current_date_obj and not existing_date_obj:
                    # Current has valid date, existing doesn't - use current
                    should_replace = True
                    duplicate_date_log.append({
                        'content_preview': post_content[:100],
                        'old_date': existing_post.get('created_at', 'INVALID'),
                        'new_date': created_at,
                        'action': 'REPLACED (new has valid date)'
                    })
                else:
                    # Keep existing
                    duplicate_date_log.append({
                        'content_preview': post_content[:100],
                        'kept_date': existing_post.get('created_at'),
                        'rejected_date': created_at,
                        'action': 'KEPT EXISTING'
                    })

                if should_replace:
                    # Replace with current (earlier) version
                    seen_posts[post_content] = {
                        'post_id': f"{entry.get('post_id', '')}_{i}" if entry.get('post_id') else f"{date}_{i}",
                        'content': post_content,
                        'timestamp': timestamp,
                        'created_at': created_at,
                        'date': date,
                        'username': username,
                        'platform': 'Truth Social',
                        'scraped_at': entry.get('scraped_at', ''),
                        'url': entry.get('url', ''),
                        'likes': entry.get('likes', 0),
                        'retweets': entry.get('retweets', 0)
                    }
                # else: keep existing entry (already in seen_posts)

            else:
                # NEW POST - Add to seen_posts
                seen_posts[post_content] = {
                    'post_id': f"{entry.get('post_id', '')}_{i}" if entry.get('post_id') else f"{date}_{i}",
                    'content': post_content,
                    'timestamp': timestamp,
                    'created_at': created_at,
                    'date': date,
                    'username': username,
                    'platform': 'Truth Social',
                    'scraped_at': entry.get('scraped_at', ''),
                    'url': entry.get('url', ''),
                    'likes': entry.get('likes', 0),
                    'retweets': entry.get('retweets', 0)
                }

    # Convert dictionary back to list
    individual_posts = list(seen_posts.values())

    # Log duplicate date handling
    if duplicate_date_log:
        log_func(f"Found {len(duplicate_date_log)} duplicate posts with different dates")
        log_func("See duplicate_dates_report.txt for details")

    return individual_posts, duplicate_date_log

def save_cleaned_data(posts, json_filename, csv_filename):
    """Save cleaned data to JSON and CSV files"""

    # Save JSON
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    # Save CSV
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        if posts:
            writer = csv.DictWriter(f, fieldnames=posts[0].keys())
            writer.writeheader()
            writer.writerows(posts)

def save_duplicate_report(duplicate_log, filename):
    """Save duplicate date report to file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("Duplicate Date Handling Report\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total duplicates with different dates: {len(duplicate_log)}\n\n")

        for i, dup in enumerate(duplicate_log, 1):
            f.write(f"Duplicate #{i}:\n")
            f.write(f"  Content: {dup.get('content_preview', 'N/A')}...\n")
            if 'old_date' in dup:
                f.write(f"  Old date: {dup['old_date']}\n")
                f.write(f"  New date: {dup['new_date']}\n")
            else:
                f.write(f"  Kept date: {dup['kept_date']}\n")
                f.write(f"  Rejected date: {dup['rejected_date']}\n")
            f.write(f"  Action: {dup['action']}\n")
            f.write("-" * 80 + "\n")

def main():
    print("Cleaning Trump Truth Archive JSON (FIXED VERSION)")
    print("=" * 50)
    print("✅ Bug fixes applied:")
    print("  - Keeps EARLIEST date for duplicate posts")
    print("  - Date validation added")
    print("  - Redundant deduplication removed")
    print("=" * 50)
    print()

    input_file = "trump_truth_archive.json"
    output_json = "trump_truth_archive_clean.json"
    output_csv = "trump_truth_archive_clean.csv"
    log_file = "cleaning_log.txt"
    duplicate_report_file = "duplicate_dates_report.txt"

    log_entries = []

    def log(message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        log_entries.append(log_entry)

    # Load original data
    log("Loading original JSON file...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        log(f"Loaded {len(original_data)} entries from original file")
    except Exception as e:
        log(f"Error loading file: {e}")
        return

    # Extract individual posts (with deduplication and earliest-date logic)
    log("Extracting individual posts (keeping earliest dates for duplicates)...")
    individual_posts, duplicate_log = extract_individual_posts(original_data, log)
    log(f"Extracted {len(individual_posts)} unique posts")

    # Sort by date
    log("Sorting posts by date...")
    individual_posts.sort(key=lambda x: x.get('created_at', ''))

    # Show sample posts
    log("Sample cleaned posts:")
    for i, post in enumerate(individual_posts[:3]):
        log(f"  {i+1}. {post['date']}: {post['content'][:100]}...")

    # Save cleaned data
    log("Saving cleaned data...")
    save_cleaned_data(individual_posts, output_json, output_csv)

    # Save duplicate report
    if duplicate_log:
        log(f"Saving duplicate date report ({len(duplicate_log)} entries)...")
        save_duplicate_report(duplicate_log, duplicate_report_file)

    # Save log
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("Trump Truth Archive Cleaning Log (FIXED VERSION)\n")
        f.write("=" * 50 + "\n\n")
        for entry in log_entries:
            f.write(entry + "\n")

    log(f"✓ Cleaning complete!")
    log(f"✓ Original entries: {len(original_data)}")
    log(f"✓ Unique posts: {len(individual_posts)}")
    log(f"✓ Duplicates with different dates: {len(duplicate_log)}")
    log(f"✓ Saved to: {output_json} and {output_csv}")

    # Show date range
    if individual_posts:
        dates = [post['date'] for post in individual_posts if post['date']]
        if dates:
            log(f"✓ Date range: {min(dates)} to {max(dates)}")

    print()
    print("="*50)
    print("IMPORTANT:")
    print("  1. Review duplicate_dates_report.txt for date changes")
    print("  2. Re-run tariff_classifier_optimized.py to update analysis")
    print("  3. Delete checkpoint.json before re-running classifier")
    print("="*50)

if __name__ == "__main__":
    main()
