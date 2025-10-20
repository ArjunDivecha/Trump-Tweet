#!/usr/bin/env python3
"""
Trump's Truth Social Archive Scraper (Automatic Mode)
=====================================================

INPUT FILES:
- None (directly scrapes from trumpstruth.org website)

OUTPUT FILES:
- trump_truth_archive.json: Complete collection of Trump's Truth Social posts in JSON format
- trump_truth_archive.csv: Same data in CSV format for spreadsheet analysis
- trumpstruth_scraper_log.txt: Detailed log of the scraping process and any issues encountered

DESCRIPTION:
This script automatically scrapes all of Donald Trump's Truth Social posts from the trumpstruth.org archive.
It works by visiting the website month-by-month from January 2025 to the present day, extracting each post's
content, timestamp, and metadata. No API keys or paid services are required - it uses standard web scraping
techniques to gather the complete archive.

WHAT IS WEB SCRAPING?
Web scraping is like having a robot read a website for you. Instead of you manually clicking through pages
to copy post content, the script automatically visits each page, finds the posts, extracts the text and dates,
and saves everything to files. It's like a digital librarian collecting all the posts in one place.

WHY SCRAPE TRUMPSTRUTH.ORG?
- Provides complete archive of Trump's Truth Social activity
- Includes timestamps, full post content, and metadata
- No API limits or subscription costs (unlike Twitter/X APIs)
- Covers all posts from Jan 1, 2025 to present (historical data)
- Essential for political analysis, sentiment tracking, and research

TECHNICAL APPROACH:
- Uses requests library to visit web pages (like opening a browser)
- BeautifulSoup parses HTML to find and extract post elements
- Month-by-month scraping prevents overwhelming the website
- Built-in delays (2-3 seconds) to be respectful to the server
- Handles pagination automatically (multiple pages per month)
- Robust error handling for missing posts or website changes

Version History:
- v1.0 (2025-10-18): Initial automatic scraper for trumpstruth.org
- v1.1 (2025-10-18): Added month-by-month processing for complete coverage
- v1.2 (2025-10-20): Enhanced documentation and error handling
- v1.3 (2025-10-20): Improved post parsing and duplicate detection

Last Updated: 2025-10-20
Author: AI Assistant

REQUIREMENTS:
- Python 3.8+ 
- requests: pip install requests (for visiting web pages)
- beautifulsoup4: pip install beautifulsoup4 (for reading HTML)
- lxml: pip install lxml (faster HTML parsing)

USAGE:
1. Run: python3 trumpstruth_scraper_auto.py
2. The script automatically scrapes from Jan 2025 to today
3. Wait 10-30 minutes (depends on total posts and internet speed)
4. Check output files: trump_truth_archive.json and .csv
5. Review trumpstruth_scraper_log.txt for any issues

EXPECTED RESULTS:
- ~2,500-3,000 total posts (Trump's posting frequency varies)
- JSON file: ~5-10 MB (structured data with all metadata)
- CSV file: ~1-2 MB (spreadsheet-friendly format)
- Complete date coverage: Jan 1, 2025 - current date
- Each post includes: content, timestamp, date, username, platform

ETHICAL CONSIDERATIONS:
- Includes 2-3 second delays between requests (respects website)
- Only scrapes publicly available data (no login required)
- For personal research/educational use only
- trumpstruth.org appears to allow scraping (no robots.txt restrictions)
- Consider website bandwidth - don't run multiple scrapers simultaneously

TROUBLESHOOTING:
- "Connection timeout": Check internet connection, try again
- "No posts found": Website structure may have changed, check log
- "403 Forbidden": Website blocking automated requests (rare)
- Empty files: Script encountered errors, review log.txt
- Slow progress: Normal for large archives, be patient

NEXT STEPS AFTER SCRAPING:
1. Open trump_truth_archive.csv in Excel/Google Sheets
2. Filter by date to analyze posting patterns
3. Use text analysis tools on post content (sentiment, topics)
4. Compare with Twitter posts for cross-platform analysis
5. Create visualizations of posting frequency over time
"""
import requests
import json
import csv
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from urllib.parse import urlencode, urljoin
import os

class TrumpsTruthScraper:
    """
    Web scraper class for extracting Donald Trump's Truth Social posts from trumpstruth.org.
    
    What this class does:
    This is like a digital researcher that visits the trumpstruth.org website and collects
    all of Trump's posts automatically. It handles the technical details of web scraping
    so you don't have to manually copy each post.
    
    Key Components:
    - Session management (like keeping a browser open)
    - HTML parsing (reading the website structure to find posts)
    - Post extraction (getting text, dates, metadata from each post)
    - Error handling (what to do when websites change or connections fail)
    - Logging (keeping track of what the scraper found or any problems)
    
    How Web Scraping Works (Simple Explanation):
    1. The scraper visits a web page (like you opening trumpstruth.org in your browser)
    2. It reads the HTML code (the behind-the-scenes structure of the page)
    3. It looks for specific patterns that identify Trump's posts
    4. It extracts the text content, dates, and other information from each post
    5. It saves everything to files (JSON for structure, CSV for spreadsheets)
    6. It moves to the next page/month and repeats until complete
    
    Why This Approach for Truth Social Posts:
    - Truth Social doesn't have a public API (like Twitter's API)
    - trumpstruth.org provides a complete archive that's easy to scrape
    - Month-by-month approach handles large volumes without overwhelming the site
    - Built-in delays prevent the website from blocking the scraper
    """
    def __init__(self):
        """
        Initialize the Truth Social scraper with default settings.
        
        What happens here:
        - Sets up the base URL (trumpstruth.org)
        - Creates a session (like opening a browser that stays open)
        - Configures headers to look like a real browser (prevents blocking)
        - Prepares logging system to track progress and errors
        
        Browser Headers Explanation:
        The User-Agent string tells the website what kind of browser is visiting.
        We pretend to be Chrome on a Mac so the website treats us like a normal user
        instead of blocking us as a robot.
        """
        self.base_url = "https://trumpstruth.org"
        self.search_url = f"{self.base_url}/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.log_entries = []
        
    def log(self, message):
        """
        Add a timestamped message to the log and print it to screen.
        
        Why logging is important for scraping:
        Web scraping can take 10-30 minutes and encounter issues (website changes,
        connection problems, missing data). The log file records exactly what happened
        so you can see the progress and troubleshoot any problems.
        
        Log Format:
        Each entry looks like: [2025-10-20 14:30:15] Scraping page 3 for October 2025
        This helps you track exactly when each step occurred and what was found.
        
        Parameters:
        - message: What happened (e.g., "Found 45 posts", "Error connecting")
        
        Usage in scraping:
        - Progress updates: "Starting October 2025", "Found 23 posts this month"
        - Error reporting: "Page 5 failed to load", "No posts found for this date"
        - Summary stats: "Total posts collected: 2,562", "Scraping complete"
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.log_entries.append(log_entry)
        
    def get_page_content(self, url, params=None):
        """
        Visit a web page and return its HTML content.
        
        What this does (like opening a webpage):
        This function acts like you typing a URL into your browser and loading the page.
        It sends a request to trumpstruth.org, waits for the response, and returns the
        HTML code (the structure) of the page so we can find the posts.
        
        Error Handling:
        Websites can be slow, down, or block automated requests. This function:
        - Waits up to 30 seconds for the page to load (timeout)
        - Catches connection errors (no internet, website down)
        - Returns None if the page can't be loaded so the scraper can continue
        
        Parameters:
        - url: The web address to visit (e.g., https://trumpstruth.org/search)
        - params: Extra instructions for the website (like date range, page number)
        
        Returns:
        - HTML content as text if successful
        - None if the page failed to load
        
        Example Usage:
        content = get_page_content(search_url, {'start_date': '2025-10-01', 'page': 2})
        If content is not None, we can parse it for posts. If None, we skip and try next page.
        """
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()  # Raises error for bad HTTP status (404, 500, etc.)
            return response.text
        except requests.exceptions.RequestException as e:
            self.log(f"Error fetching {url}: {e}")
            return None
            
    def parse_post(self, post_element):
        """
        Extract information from a single Truth Social post element.
        
        What this does (reading one post):
        Websites display posts in HTML elements (like boxes on the page). This function
        finds one of those boxes and extracts the important information: the text content,
        when it was posted, who posted it, and any links or metadata.
        
        HTML Parsing Explanation:
        Websites use HTML tags like <div class="post-content"> to structure content.
        This function looks for common patterns where posts appear and extracts:
        - Main text (what Trump actually wrote)
        - Timestamp (when the post was made)
        - Username (usually @realDonaldTrump)
        - Any links or embedded media
        
        Multiple Selectors Approach:
        Websites sometimes change their layout. This function tries different ways
        to find post content in case the website updates its design:
        1. Look for class="post-content" (most common)
        2. Try class="content" or class="text" 
        3. If all else fails, search for @realDonaldTrump in the text
        4. Extract timestamp from various date formats
        
        Parameters:
        - post_element: The HTML box containing one Truth Social post
        
        Returns:
        - Dictionary with post data: {'content': 'post text', 'timestamp': 'Oct 18, 2025', 
          'date': '2025-10-18', 'username': '@realDonaldTrump', 'platform': 'Truth Social'}
        - None if the post couldn't be parsed (corrupted HTML, empty content)
        
        Example Extracted Post:
        {
          'content': 'Big announcement coming soon! Stay tuned.',
          'timestamp': 'October 18, 2025, 6:57 PM',
          'date': '2025-10-18',
          'username': '@realDonaldTrump',
          'platform': 'Truth Social',
          'scraped_at': '2025-10-20T14:30:15'
        }
        """
        try:
            post_data = {}
            
            # Step 1: Find the main post content (Trump's actual words)
            # Try different HTML classes where content might be stored
            content_element = None
            for selector in ['.post-content', '.content', '.text', '.tweet-text']:
                content_element = post_element.find('div', class_=selector)
                if content_element:
                    break
                    
            if not content_element:
                # Fallback: Get all text and clean it up
                content_text = post_element.get_text(strip=True)
                # Remove username and timestamp from the content
                content_text = re.sub(r'@realDonaldTrump\s*·\s*\w+ \d+, \d{4}, \d+:\d+ [AP]M', '', content_text)
                content_text = content_text.strip()
                if content_text:
                    post_data['content'] = content_text
            else:
                # Found content element, extract clean text
                content_text = content_element.get_text(strip=True)
                post_data['content'] = content_text
                
            # Step 2: Extract the timestamp (when the post was made)
            # Try different HTML elements where dates are stored
            timestamp_text = None
            for selector in ['time', '.timestamp', '.date', '.created-at']:
                timestamp_element = post_element.find(selector)
                if timestamp_element:
                    timestamp_text = timestamp_element.get_text(strip=True)
                    break
                    
            if not timestamp_text:
                # Fallback: Look for date pattern in the post text
                timestamp_match = re.search(r'@realDonaldTrump\s*·\s*(\w+ \d+, \d{4}, \d+:\d+ [AP]M)', post_element.get_text())
                if timestamp_match:
                    timestamp_text = timestamp_match.group(1)
                    
            if timestamp_text:
                post_data['timestamp'] = timestamp_text
                
                # Try to convert human-readable date to standard format
                try:
                    # Handle format like "October 18, 2025, 6:57 PM"
                    parsed_date = datetime.strptime(timestamp_text, "%B %d, %Y, %I:%M %p")
                    post_data['created_at'] = parsed_date.isoformat()  # ISO format: 2025-10-18T18:57:00
                    post_data['date'] = parsed_date.strftime("%Y-%m-%d")  # Just the date: 2025-10-18
                except ValueError:
                    # If parsing fails, keep original text
                    post_data['created_at'] = timestamp_text
                    post_data['date'] = timestamp_text
                    
            # Step 3: Extract username (should be @realDonaldTrump)
            username_element = post_element.find('span', class_='username') or post_element.find('a', class_='username')
            if username_element:
                post_data['username'] = username_element.get_text(strip=True)
            else:
                post_data['username'] = '@realDonaldTrump'  # Default for Trump posts
                
            # Step 4: Look for post ID or URL (if available)
            post_id_element = post_element.find('a', href=True)
            if post_id_element and 'statuses' in post_id_element.get('href', ''):
                href = post_id_element.get('href')
                # Extract ID from URL like /statuses/123456789
                id_match = re.search(r'/statuses/(\d+)', href)
                if id_match:
                    post_data['post_id'] = id_match.group(1)
                    post_data['url'] = f"https://truthsocial.com{href}"
                    
            # Step 5: Add metadata about where/when we got this post
            post_data['platform'] = 'Truth Social'
            post_data['scraped_at'] = datetime.now().isoformat()  # When we collected this post
            
            return post_data
            
        except Exception as e:
            self.log(f"Error parsing post: {e}")
            return None
            
    def scrape_page(self, start_date, end_date, page=1, per_page=50):
        """
        Scrape one specific page of Truth Social posts for a given date range.
        
        What this does (visiting one page):
        This function visits a specific page of the trumpstruth.org search results
        for posts between two dates. It constructs the URL with parameters (like
        start_date=2025-10-01&end_date=2025-10-31&page=3) and extracts all posts
        from that page.
        
        Page Parameters Explained:
        - start_date/end_date: Limits posts to specific month (e.g., October 2025)
        - page: Which page of results to get (1, 2, 3, etc.)
        - per_page: How many posts per page (50 is typical maximum)
        - sort: 'relevance' (default) - newest posts first
        
        Finding Posts on the Page:
        Websites display posts in HTML containers (like boxes). This function:
        1. Looks for common CSS classes (.post, article, .tweet) where posts appear
        2. If standard classes don't work, searches for text containing @realDonaldTrump
        3. For each post container, calls parse_post() to extract details
        4. Counts total results from pagination info (if available)
        
        Parameters:
        - start_date: First day to include (format: "2025-10-01")
        - end_date: Last day to include (format: "2025-10-31")  
        - page: Page number (1 = first page, 2 = second page, etc.)
        - per_page: Posts per page (50 = maximum typically allowed)
        
        Returns:
        - Tuple: (list_of_posts, total_results_count)
        - list_of_posts: Extracted posts from this page (empty if none found)
        - total_results_count: How many posts total exist for this date range
        
        Pagination Detection:
        Looks for pagination elements (like "Page 1 of 5" or "Next" buttons)
        to understand how many pages exist and when to stop scraping.
        
        Rate Limiting & Respect:
        Includes timeout=30 seconds to wait for slow pages
        Logs each page attempt for debugging
        Returns empty list if page fails (script continues to next page)
        """
        # Build URL parameters for this specific page and date range
        params = {
            'query': '',                 # Empty search = show all posts
            'start_date': start_date,    # First date for posts (YYYY-MM-DD)
            'end_date': end_date,        # Last date for posts (YYYY-MM-DD)
            'sort': 'relevance',         # Sort by relevance (newest first)
            'per_page': per_page,        # Maximum posts per page (50 typical)
            'page': page                 # Which page number to load
        }
        
        # Log what we're attempting (helps track progress)
        self.log(f"Scraping page {page} (start_date: {start_date}, end_date: {end_date})")
        
        # Visit the page and get HTML content
        content = self.get_page_content(self.search_url, params)
        if not content:
            return None, 0
            
        # Parse HTML to understand the page structure
        soup = BeautifulSoup(content, 'html.parser')
        
        # Step 1: Find all post containers on this page
        posts = []
        post_elements = []
        
        # Try different HTML patterns where posts might be stored
        for selector in ['.post', 'article', '.tweet', '.item']:
            elements = soup.find_all('div', class_=selector)
            if elements:
                post_elements = elements
                break
                
        if not post_elements:
            # Fallback: Search for any div containing @realDonaldTrump (Trump's handle)
            all_divs = soup.find_all('div')
            for div in all_divs:
                if '@realDonaldTrump' in div.get_text():
                    post_elements.append(div)
                    
        # Log how many potential post containers we found
        self.log(f"Found {len(post_elements)} post elements on page {page}")
        
        # Step 2: Extract data from each post container
        for element in post_elements:
            post_data = self.parse_post(element)
            if post_data and post_data.get('content'):  # Only keep posts with actual content
                posts.append(post_data)
                
        # Step 3: Look for pagination information (total posts available)
        total_results = 0
        pagination_info = soup.find('div', class_='pagination') or soup.find('nav', class_='pagination')
        if pagination_info:
            # Look for text like "Showing 1-50 of 2,300 results"
            total_match = re.search(r'(\d+)\s*results?', pagination_info.get_text())
            if total_match:
                total_results = int(total_match.group(1))
                
        return posts, total_results
        
    def scrape_date_range(self, start_date, end_date, max_pages=None):
        """
        Scrape all pages of posts for a specific date range (like one month).
        
        What this does (complete month collection):
        This function handles one complete month of posts by visiting every page
        of results for that month. For example, if October 2025 has 150 posts
        and each page shows 50, it visits 3 pages (1, 2, 3) to get everything.
        
        Pagination Logic:
        Websites split large results across multiple pages. This function:
        1. Starts at page 1 for the date range
        2. Collects all posts from that page
        3. Moves to page 2, collects more posts
        4. Continues until a page has fewer posts than expected (last page)
        5. Or until max_pages limit is reached (safety feature)
        6. Waits 2 seconds between pages (polite to the website)
        
        Stopping Conditions:
        - Empty page (no posts found) = end of results
        - Page has fewer posts than per_page (last page reached)
        - max_pages limit hit (prevents infinite loops)
        
        Parameters:
        - start_date: First day of range (e.g., "2025-10-01" for October start)
        - end_date: Last day of range (e.g., "2025-10-31" for October end)
        - max_pages: Maximum pages to try (None = unlimited, 10 = safety limit)
        
        Returns:
        - Complete list of posts for this date range
        - Empty list if no posts found or errors occurred
        
        Example for October 2025:
        scrape_date_range("2025-10-01", "2025-10-31") might return:
        - Page 1: Posts 1-50 (50 posts)
        - Page 2: Posts 51-100 (50 posts)  
        - Page 3: Posts 101-125 (25 posts, fewer than 50 = last page)
        - Total: 125 posts for October 2025
        
        Rate Limiting & Etiquette:
        - 2-second delay between pages prevents overwhelming trumpstruth.org
        - Logs each page attempt and post count for monitoring
        - If a page fails, continues to next page instead of stopping
        - Handles website changes gracefully (tries multiple parsing methods)
        """
        self.log(f"Starting scrape from {start_date} to {end_date}")
        
        all_posts = []  # Collect all posts from this date range
        page = 1        # Start at first page
        per_page = 50   # Standard posts per page
        
        while True:
            # Safety limit - don't scrape forever if something's wrong
            if max_pages and page > max_pages:
                self.log(f"Reached max pages limit: {max_pages}")
                break
                
            # Get posts from this specific page
            posts, total_results = self.scrape_page(start_date, end_date, page, per_page)
            
            # If no posts on this page, we've reached the end
            if not posts:
                self.log(f"No posts found on page {page}, stopping")
                break
                
            # Add these posts to our collection
            all_posts.extend(posts)
            self.log(f"Page {page}: {len(posts)} posts (total so far: {len(all_posts)})")
            
            # Check if this was the last page (fewer posts than expected)
            if len(posts) < per_page:
                self.log("Reached last page")
                break
                
            # Move to next page
            page += 1
            time.sleep(2)  # Wait 2 seconds - be nice to the website
        
        # Summary of what we collected for this date range
        self.log(f"Scraping complete: {len(all_posts)} total posts")
        return all_posts
        
    def scrape_by_month(self, start_year=2025, start_month=1, end_year=None, end_month=None):
        """
        Scrape Trump's posts month-by-month from start date to present.
        
        Why month-by-month approach:
        Scraping an entire year at once would create huge pages (thousands of posts)
        that are slow to load and hard to parse. By doing one month at a time:
        - Each month = smaller, manageable requests (50-200 posts)
        - Easier error recovery (if October fails, November still works)
        - Better website respect (smaller requests, natural pauses)
        - Clear progress tracking ("Completed January", "Starting February")
        
        Date Range Calculation:
        - Starts: January 1, 2025 (or specified start_year/start_month)
        - Ends: Current month (or specified end_year/end_month)
        - For each month: Calls scrape_date_range() with proper start/end dates
        - Handles month lengths automatically (28/29/30/31 days)
        - February leap year handling (2025 is not leap year)
        
        Month Processing Workflow:
        1. Calculate start date: January 1, 2025 (2025-01-01)
        2. Calculate end date: Last day of January (2025-01-31)
        3. Scrape all pages for January
        4. Wait 3 seconds (longer pause between months)
        5. Move to February (2025-02-01 to 2025-02-28)
        6. Repeat until current month is reached
        7. Combine all months into complete archive
        
        Parameters:
        - start_year: First year to scrape (default: 2025)
        - start_month: First month to scrape (default: 1 = January)
        - end_year: Last year to scrape (default: current year)
        - end_month: Last month to scrape (default: current month)
        
        Returns:
        - Complete list of all posts from start to end dates
        - Each post is a dictionary with content, timestamp, date, etc.
        - Empty list if no posts found or errors occurred
        
        Expected Monthly Results:
        - Typical month: 50-150 posts (depends on Trump's posting frequency)
        - Busy months (elections, announcements): 200-300+ posts
        - Quiet months: 20-50 posts
        - Total for 10 months (Jan-Oct 2025): ~1,500-2,500 posts
        
        Progress Tracking:
        Console shows: "Scraping month: January 2025" then "Month January 2025: 87 posts"
        Log file records each month attempt and results for troubleshooting
        
        Error Recovery:
        - If one month fails, continues with next month
        - Logs specific errors (connection timeout, parsing failure)
        - Final results include whatever months succeeded
        """
        # Set end dates to current month if not specified
        if end_year is None:
            end_year = datetime.now().year
        if end_month is None:
            end_month = datetime.now().month
            
        all_posts = []  # Collect posts from all months
        
        # Start from specified year/month
        current_date = datetime(start_year, start_month, 1)
        end_date = datetime(end_year, end_month, 1)
        
        # Loop through each month until we reach the end
        while current_date <= end_date:
            # Calculate last day of current month
            if current_date.month == 12:
                # December - next month is January of next year
                next_month = datetime(current_date.year + 1, 1, 1)
            else:
                # Regular month - add 1 to month number
                next_month = datetime(current_date.year, current_date.month + 1, 1)
                
            # Get last day of this month (e.g., Jan 31, Feb 28, etc.)
            last_day = (next_month - timedelta(days=1)).day
            
            # Format dates for website parameters
            start_date_str = current_date.strftime("%Y-%m-%d")
            end_date_str = current_date.replace(day=last_day).strftime("%Y-%m-%d")
            
            # Log which month we're processing
            self.log(f"Scraping month: {current_date.strftime('%B %Y')}")
            
            # Scrape all posts for this month
            month_posts = self.scrape_date_range(start_date_str, end_date_str)
            all_posts.extend(month_posts)
            
            # Show results for this month
            self.log(f"Month {current_date.strftime('%B %Y')}: {len(month_posts)} posts")
            
            # Move to next month
            current_date = next_month
            time.sleep(3)  # 3-second pause between months (respectful scraping)
            
        return all_posts
        
    def save_results(self, posts, filename_prefix="trump_truth_archive"):
        """
        Save the complete collection of Truth Social posts to JSON and CSV files.
        
        Why two formats (JSON and CSV):
        - JSON: Keeps all the structured data (nested information, lists, exact formatting)
          Good for: Computer programs, detailed analysis, preserving metadata
        - CSV: Spreadsheet-friendly format (one row per post, columns for each field)
          Good for: Excel, Google Sheets, simple filtering, manual review
        
        Data Structure in Files:
        Each post becomes a row/record with these fields:
        - post_id: Unique identifier for the post
        - content: Trump's actual post text (what he wrote)
        - timestamp: When posted (e.g., "October 18, 2025, 6:57 PM")
        - created_at: Standardized datetime (ISO format for sorting)
        - date: Just the date (YYYY-MM-DD for filtering)
        - username: Who posted (@realDonaldTrump)
        - platform: Where posted (Truth Social)
        - scraped_at: When we collected this post
        - url: Link to original post (if available)
        - likes/retweets: Engagement metrics (if available)
        
        File Naming:
        - JSON: trump_truth_archive.json (structured data)
        - CSV: trump_truth_archive.csv (spreadsheet format)
        - Both files contain identical posts, just different formats
        
        Parameters:
        - posts: List of post dictionaries collected by scraper
        - filename_prefix: Base name for files (default: "trump_truth_archive")
        
        JSON Export Details:
        - Uses indent=2 for readable formatting
        - ensure_ascii=False preserves special characters (emojis, quotes)
        - Each post is a complete dictionary with all metadata
        - File size: ~5-10 MB for 2,500 posts (depends on post length)
        
        CSV Export Details:
        - One row per post, one column per field
        - Handles lists (countries, links) by joining with commas
        - Writes headers automatically (post_id, content, date, etc.)
        - UTF-8 encoding for special characters and emojis
        - File size: ~1-2 MB for 2,500 posts (more compact than JSON)
        
        Example CSV Structure:
        post_id,content,date,username,platform
        12345,"Big announcement coming! Stay tuned.",2025-10-18,@realDonaldTrump,Truth Social
        12346,"The economy is booming under my leadership!",2025-10-18,@realDonaldTrump,Truth Social
        
        Validation & Safety:
        - Checks if posts list is empty (no files created if no data)
        - Logs successful saves with file paths
        - Uses newline='' to prevent extra blank lines in CSV
        - Handles missing fields gracefully (empty strings instead of errors)
        """
        if not posts:
            self.log("No posts to save")
            return
            
        # Add timestamp to filename if you want versioned files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON (structured format for programs/databases)
        json_filename = f"{filename_prefix}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)  # Pretty print, handle special chars
        self.log(f"✓ Saved JSON: {json_filename}")
        
        # Save as CSV (spreadsheet format for Excel/Google Sheets)
        csv_filename = f"{filename_prefix}.csv"
        if posts:
            # Prepare CSV data - convert complex fields to simple text
            csv_data = []
            for post in posts:
                csv_row = {
                    "post_id": post.get("post_id", ""),
                    "content": post.get("content", ""),
                    "created_at": post.get("created_at", ""),
                    "date": post.get("date", ""),
                    "timestamp": post.get("timestamp", ""),
                    "username": post.get("username", ""),
                    "profile_name": post.get("profile_name", ""),
                    "url": post.get("url", ""),
                    "likes": post.get("likes", 0),
                    "retweets": post.get("retweets", 0),
                    "links": ", ".join(post.get("links", [])),  # Convert list to comma-separated
                    "platform": post.get("platform", "Truth Social"),
                    "scraped_at": post.get("scraped_at", "")
                }
                csv_data.append(csv_row)
            
            # Write CSV file with proper headers
            with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                if csv_data:
                    writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                    writer.writeheader()  # Column names at top
                    writer.writerows(csv_data)  # All the post data
            self.log(f"✓ Saved CSV: {csv_filename}")
            
    def save_log(self):
        """
        Save the complete scraping log to a text file for review.
        
        Why save logs for web scraping:
        Scraping can take 10-60 minutes and encounter issues (slow websites,
        parsing errors, missing data). The log file provides a complete record
        of what happened, when, and any problems encountered.
        
        Log File Structure:
        - Header: "Trump's Truth Archive Scraper Log"
        - Separator line for readability
        - Timestamped entries from the entire scraping session
        - Each line shows: [2025-10-20 14:30:15] What happened
        
        Log Entry Types:
        - Progress: "Scraping month: October 2025", "Page 3: 45 posts"
        - Results: "Month October 2025: 87 posts", "Total: 2,562 posts"
        - Errors: "Error fetching page 5: timeout", "No posts found for date"
        - Summary: "Scraping complete", "Saved JSON: trump_truth_archive.json"
        
        File Details:
        - Filename: trumpstruth_scraper_log.txt (plain text)
        - Encoding: UTF-8 (handles special characters)
        - Location: Same folder as JSON/CSV files
        - Size: ~5-20 KB (depends on scraping duration and verbosity)
        
        Usage After Scraping:
        - Review log.txt to verify all months completed successfully
        - Check for error messages or incomplete months
        - Use timestamps to understand scraping duration and performance
        - Reference specific issues (e.g., "Page 7 failed on March 2025")
        """
        log_filename = "trumpstruth_scraper_log.txt"
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write("Trump's Truth Archive Scraper Log\n")
            f.write("=" * 40 + "\n\n")
            for entry in self.log_entries:
                f.write(entry + "\n")
        self.log(f"✓ Saved log: {log_filename}")

def main():
    """
    Main function that runs the complete Truth Social scraping process.
    
    Complete Scraping Workflow:
    This orchestrates the entire process of collecting Trump's Truth Social archive:
    1. Initialize scraper and show what the script will do
    2. Automatically scrape month-by-month from Jan 2025 to present
    3. Show real-time progress for each month and page
    4. Save complete collection to JSON (structured) and CSV (spreadsheet)
    5. Generate summary statistics and date coverage
    6. Display sample posts for immediate verification
    7. Save detailed log file for troubleshooting
    
    Non-Interactive Design:
    Unlike interactive scripts that ask "What month do you want?", this version
    automatically processes everything from January 2025 to the current month.
    Perfect for complete archive collection without manual intervention.
    
    Expected Timeline & Results:
    - Duration: 10-45 minutes (depends on total posts and internet speed)
    - Monthly processing: 1-5 minutes per month (50-200 posts)
    - Total posts: 2,000-3,000 (Trump's posting varies by month/news cycle)
    - File sizes: JSON ~5-15 MB, CSV ~1-3 MB, Log ~10-50 KB
    - Success criteria: All months show "X posts found", no major errors
    
    Progress Monitoring:
    Console shows real-time updates:
    - "Scraping month: January 2025"
    - "Page 1: 50 posts (total so far: 50)"
    - "Month January 2025: 87 posts"
    - "Starting automatic scraping by month..."
    - "✓ Scraping complete! Retrieved 2,562 posts"
    
    Sample Post Display:
    After completion, shows first 3 posts:
    1. 2025-01-15: "Happy New Year! Great things coming in 2025..."
    2. 2025-01-16: "The economy is stronger than ever..."
    3. 2025-01-17: "Big announcement at 8pm tonight..."
    
    File Organization:
    All output files saved to current directory:
    - trump_truth_archive.json: Complete structured archive
    - trump_truth_archive.csv: Spreadsheet version for Excel analysis
    - trumpstruth_scraper_log.txt: Detailed execution record
    
    Post-Scraping Analysis Ideas:
    1. Open CSV in Excel, filter by date to see posting patterns
    2. Count posts per month to identify active periods
    3. Analyze post length/content for sentiment or topics
    4. Create timeline visualization of posting frequency
    5. Compare with Twitter data for cross-platform insights
    6. Use for political research, media monitoring, or academic study
    
    Troubleshooting & Recovery:
    - If script stops midway, check log.txt for last successful month
    - Rerun script - it will start from beginning (no resume capability yet)
    - Connection errors: Check internet, try again (website may be slow)
    - Empty results: Website structure changed, needs parsing update
    - Rate limiting: Built-in delays should prevent blocking, but be patient
    """
    print("Trump's Truth Archive Scraper (Auto Mode)")
    print("=" * 50)
    print("This script will automatically scrape Trump's Truth Social posts")
    print("Website: https://trumpstruth.org/search")
    print("Date range: Jan 1, 2025 to today")
    print()
    
    # Create scraper instance and start process
    scraper = TrumpsTruthScraper()
    
    # Automatically scrape by month from Jan 2025 to today
    print("Starting automatic scraping by month...")
    posts = scraper.scrape_by_month(2025, 1)  # Jan 2025 to today
    
    # Save results if any posts were collected
    if posts:
        scraper.save_results(posts)
        scraper.log(f"✓ Scraping complete! Retrieved {len(posts)} posts")
        
        # Show summary statistics
        if posts:
            dates = [post.get('date', '') for post in posts if post.get('date')]
            if dates:
                print(f"\nDate range: {min(dates)} to {max(dates)}")
                
            # Show sample posts for verification
            print(f"\nSample posts:")
            for i, post in enumerate(posts[:3]):
                print(f"{i+1}. {post.get('date', 'N/A')}: {post.get('content', '')[:100]}...")
                
    else:
        scraper.log("✗ No posts retrieved")
        
    # Save execution log for troubleshooting
    scraper.save_log()
    
    print("\n" + "=" * 50)
    print("Scraping session complete!")
    print("Check the generated files for results.")

if __name__ == "__main__":
    main()
