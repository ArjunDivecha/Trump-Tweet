#!/usr/bin/env python3
"""
Clean Trump Truth Archive JSON
=============================

INPUT FILES:
- trump_truth_archive.json: Raw scraped data with concatenated posts

OUTPUT FILES:
- trump_truth_archive_clean.json: Cleaned individual posts
- trump_truth_archive_clean.csv: Cleaned CSV format
- cleaning_log.txt: Cleaning process log

This script cleans the Trump Truth archive JSON file by:
1. Parsing concatenated posts into individual entries
2. Removing duplicate content
3. Extracting proper post content
4. Filtering out navigation elements

Version: 1.0
Last Updated: 2025-10-18
"""

import json
import csv
import re
from datetime import datetime
from collections import OrderedDict

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

def extract_individual_posts(json_data):
    """Extract individual posts from the JSON data"""
    individual_posts = []
    seen_content = set()
    
    for entry in json_data:
        content = entry.get('content', '')
        timestamp = entry.get('timestamp', '')
        created_at = entry.get('created_at', '')
        date = entry.get('date', '')
        username = entry.get('username', '@realDonaldTrump')
        
        # Clean the content to extract individual posts
        cleaned_posts = clean_content(content)
        
        for i, post_content in enumerate(cleaned_posts):
            # Skip duplicates
            if post_content in seen_content:
                continue
            seen_content.add(post_content)
            
            # Create individual post entry
            individual_post = {
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
            
            individual_posts.append(individual_post)
    
    return individual_posts

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

def main():
    print("Cleaning Trump Truth Archive JSON")
    print("=" * 40)
    
    input_file = "trump_truth_archive.json"
    output_json = "trump_truth_archive_clean.json"
    output_csv = "trump_truth_archive_clean.csv"
    log_file = "cleaning_log.txt"
    
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
    
    # Extract individual posts
    log("Extracting individual posts...")
    individual_posts = extract_individual_posts(original_data)
    log(f"Extracted {len(individual_posts)} individual posts")
    
    # Remove duplicates based on content
    log("Removing duplicates...")
    unique_posts = []
    seen_content = set()
    
    for post in individual_posts:
        content = post['content']
        if content not in seen_content:
            seen_content.add(content)
            unique_posts.append(post)
    
    log(f"After deduplication: {len(unique_posts)} unique posts")
    
    # Sort by date
    log("Sorting posts by date...")
    unique_posts.sort(key=lambda x: x.get('created_at', ''))
    
    # Show sample posts
    log("Sample cleaned posts:")
    for i, post in enumerate(unique_posts[:3]):
        log(f"  {i+1}. {post['date']}: {post['content'][:100]}...")
    
    # Save cleaned data
    log("Saving cleaned data...")
    save_cleaned_data(unique_posts, output_json, output_csv)
    
    # Save log
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("Trump Truth Archive Cleaning Log\n")
        f.write("=" * 40 + "\n\n")
        for entry in log_entries:
            f.write(entry + "\n")
    
    log(f"✓ Cleaning complete!")
    log(f"✓ Original entries: {len(original_data)}")
    log(f"✓ Individual posts: {len(individual_posts)}")
    log(f"✓ Unique posts: {len(unique_posts)}")
    log(f"✓ Saved to: {output_json} and {output_csv}")
    
    # Show date range
    if unique_posts:
        dates = [post['date'] for post in unique_posts if post['date']]
        if dates:
            log(f"✓ Date range: {min(dates)} to {max(dates)}")

if __name__ == "__main__":
    main()

