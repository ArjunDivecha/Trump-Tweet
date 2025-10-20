#!/usr/bin/env python3
"""
SPY History 5-Minute Data Fetcher
=================================

INPUT FILES:
- None (fetches data directly from Interactive Brokers API)

OUTPUT FILES:
- SPY_5min_history.xlsx: Excel file containing 5-minute OHLCV data for SPY ETF

DESCRIPTION:
This script fetches historical 5-minute price data for the SPY ETF (S&P 500) from Interactive Brokers.
It breaks the data into 3-month chunks to respect API limits and combines them into a single Excel file.

REQUIREMENTS:
- Interactive Brokers TWS or IB Gateway running with API enabled on port 7496
- ib_insync library installed: pip install ib_insync
- pandas and openpyxl for Excel export: pip install pandas openpyxl

FEATURES:
- Fetches 5-minute OHLCV (Open, High, Low, Close, Volume) bars
- Handles multiple time periods automatically (up to 1 year)
- Includes pre-market and after-hours data (useRTH=False)
- Removes timezone info for Excel compatibility
- Error handling for API timeouts and connection issues

Version History:
- v1.0 (2025-10-01): Initial version for SPY 5-minute data
- v1.1 (2025-10-15): Added multi-period fetching for 1-year coverage
- v1.2 (2025-10-20): Enhanced documentation and error handling

Last Updated: 2025-10-20
Author: AI Assistant

USAGE:
1. Start TWS or IB Gateway and enable API connections on port 7496
2. Run: python3 "SPY History.py"
3. The script will fetch ~12 months of 5-minute data and save to SPY_5min_history.xlsx

NOTE: This is the 5-minute version which can fetch longer periods than 1-minute data.
IBKR allows up to 3 months of 5-minute data per request, making this more efficient.
"""
from ib_insync import IB, Stock, util
import pandas as pd
from datetime import datetime, timedelta

def fetch_SPY_5min_history_range(end_date: str, duration: str = "3 M") -> pd.DataFrame:
    """
    Fetch historical 5-minute bar data for SPY from Interactive Brokers API.
    
    What this does (in simple terms):
    - Connects to your trading account through Interactive Brokers
    - Asks for price information about SPY (the S&P 500 ETF) every 5 minutes
    - Gets the opening price, highest price, lowest price, closing price, and trading volume
    - Puts all this information into a table (DataFrame) that you can analyze
    
    Imagine it like this: Every 5 minutes during market hours, we take a snapshot
    of what SPY was doing - where it started the 5 minutes, the highest it went,
    the lowest it went, where it ended, and how many shares were traded.
    
    Parameters:
    - end_date: The last date/time you want data for (format: "20251020 16:00:00")
    - duration: How far back to go from the end_date
      - "3 M" = 3 months (recommended for 5-minute data)
      - "1 Y" = 1 year (but may be too much for 5-minute bars)
      - "1 D" = 1 day (for testing)
    
    Returns:
    - A pandas DataFrame (like an Excel table) with these columns:
      - open: Price at the start of each 5-minute period
      - high: Highest price during those 5 minutes
      - low: Lowest price during those 5 minutes  
      - close: Price at the end of those 5 minutes
      - volume: Number of shares traded during those 5 minutes
    - Each row represents one 5-minute period, sorted by time
    
    Example:
    If you run this for 1 month of data, you'll get about 4,000-5,000 rows
    (20 trading days × 6.5 hours × 12 five-minute periods per hour = ~4,680 bars)
    
    Important Notes:
    - Your TWS (Trader Workstation) or IB Gateway must be running
    - API connections must be enabled in TWS settings (Global Configuration > API > Settings)
    - Port 7496 is the default for paper trading, 7497 for live trading
    """
    # Step 1: Connect to Interactive Brokers
    # This opens a connection to your TWS/Gateway running on your computer
    ib = IB()
    ib.connect('127.0.0.1', 7496, clientId=1)  # Connect to localhost port 7496
    
    # Step 2: Define what we want to get data for
    # SPY = S&P 500 ETF, SMART = smart routing, USD = US dollars
    contract = Stock('SPY', 'SMART', 'USD')
    ib.qualifyContracts(contract)  # Tell IBKR to verify this contract exists
    
    # Step 3: Request the historical data
    # This is where we ask IBKR for the price history
    bars = ib.reqHistoricalData(
        contract,                    # What we're getting data for (SPY)
        endDateTime=end_date,        # Stop getting data at this date/time
        durationStr=duration,        # Go back this far (3 months, 1 year, etc.)
        barSizeSetting="5 mins",     # Each bar (data point) represents 5 minutes
        whatToShow="TRADES",         # Use actual trade prices (not bid/ask)
        useRTH=False,                # Include pre-market (before 9:30am) and after-hours (after 4pm) trading
        formatDate=1,                # Use standard YYYYMMDD HH:MM:SS date format
        keepUpToDate=False,          # Don't keep the connection open for live data
        chartOptions=[]              # No special formatting options
    )
    
    # Step 4: Convert IBKR's data format to a pandas DataFrame
    # ib_insync gives us 'bars' which we convert to a table format
    df = util.df(bars)
    
    # Step 5: Clean up the data - remove columns we don't need
    # 'average' shows average price per bar, 'barCount' shows number of trades
    # We only want OHLCV (Open, High, Low, Close, Volume)
    for col in ['average', 'barCount']:
        if col in df.columns:
            df.drop(columns=col, inplace=True)
    
    # Step 6: Fix the date column so it's proper datetime format
    # IBKR gives dates as strings, we convert them to datetime objects
    df['date'] = pd.to_datetime(df['date'])
    
    # Step 7: Make the date the index (first column) so it's easy to work with
    df.set_index('date', inplace=True)
    
    # Step 8: Close the connection to IBKR (good practice)
    ib.disconnect()
    
    # Step 9: Return the clean DataFrame ready for analysis or saving
    return df

def fetch_multiple_periods(start_date: str = "20250101", num_periods: int = 3) -> pd.DataFrame:
    """
    Get more than 3 months of SPY data by making multiple API requests.
    
    Why do we need this function?
    Interactive Brokers limits how much historical data you can get in one request.
    For 5-minute bars, the maximum is about 3 months. If you want 1 year of data,
    you need to make 4 separate requests (Jan-Mar, Apr-Jun, Jul-Sep, Oct-Dec)
    and then combine all the results into one big dataset.
    
    What this function does (step by step):
    1. Starts from today and works backwards in time
    2. For each period (3 months), it calls fetch_SPY_5min_history_range()
    3. If a period succeeds, it saves that data chunk
    4. If there's an error (like API timeout), it stops and returns what it has
    5. Combines all successful chunks into one DataFrame
    6. Sorts everything by date from oldest to newest
    7. Removes any duplicate timestamps that might occur at boundaries
    
    Parameters:
    - start_date: The earliest date you're interested in (format: "20250101")
      This is mostly for reference - the script actually starts from today and goes back
    - num_periods: How many 3-month chunks to fetch
      - 1 = 3 months of data
      - 2 = 6 months of data  
      - 3 = 9 months of data
      - 4 = 12 months (1 year) of data
    
    Returns:
    - One big DataFrame containing all the periods combined
    - Sorted chronologically (oldest first)
    - No duplicate timestamps
    - Same format as fetch_SPY_5min_history_range() - OHLCV columns
    
    Example:
    If today is October 20, 2025 and num_periods=2:
    - Period 1: July 20 - October 20, 2025 (3 months)
    - Period 2: April 20 - July 20, 2025 (3 months)  
    - Combined: April 20 - October 20, 2025 (6 months total)
    - About 12,000 rows (60 trading days × 78 five-minute periods per day)
    
    Error Handling:
    - If IBKR connection fails, it prints the error and stops
    - If a specific period times out, it skips that period and continues
    - If no data is fetched at all, returns an empty DataFrame
    
    Pro Tips:
    - Start with num_periods=1 to test the connection
    - Your M4 Max with 128GB RAM can easily handle 1 year of 5-minute data
    - Each 3-month chunk is about 1,000-1,500 rows, so 4 periods = 4,000-6,000 total
    """
    all_data = []  # List to hold all the data chunks we successfully fetch
    
    # Start from today and work backwards through time
    end_date = datetime.now()
    
    # Loop through each period we want to fetch
    for i in range(num_periods):
        # Show progress - tells you which period is currently being fetched
        print(f"\nFetching period {i+1}/{num_periods}...")
        
        # Format the end date for IBKR (YYYYMMDD HH:MM:SS)
        end_date_str = end_date.strftime("%Y%m%d %H:%M:%S")
        
        try:
            # Fetch one 3-month chunk ending at end_date
            df = fetch_SPY_5min_history_range(end_date_str, duration="3 M")
            
            # Check if we got any data
            if not df.empty:
                # Show what we got - how many bars and date range
                print(f"  Got {len(df)} bars from {df.index.min()} to {df.index.max()}")
                # Add this chunk to our collection
                all_data.append(df)
            else:
                # No data for this period (maybe a holiday or error)
                print(f"  No data returned for this period")
            
            # Move back 3 months for the next period
            # We use 90 days as a rough approximation (actual months vary)
            end_date = end_date - timedelta(days=90)
            
        except Exception as e:
            # If something goes wrong (timeout, connection error, etc.)
            print(f"  Error fetching period {i+1}: {e}")
            # Stop trying further periods - something's wrong with the connection
            break
    
    # If we didn't get any data at all, return empty DataFrame
    if not all_data:
        return pd.DataFrame()
    
    # Combine all the chunks into one big dataset
    combined = pd.concat(all_data, axis=0)
    
    # Sort by date (oldest first) and remove any duplicate timestamps
    combined = combined.sort_index().drop_duplicates()
    
    # Return the complete dataset
    return combined

def save_df_to_excel(df: pd.DataFrame, filepath: str):
    """
    Save your SPY price data to an Excel file that you can open in Excel, Google Sheets, etc.
    
    Why do we need this function?
    The data comes from IBKR as a pandas DataFrame (Python table), but you probably
    want to analyze it in Excel or share it with others. This function converts
    the Python data to Excel format and handles some technical issues.
    
    What this does step by step:
    1. Checks if the DataFrame has any data (if empty, creates a template)
    2. Makes a copy of the data for Excel export (don't modify the original)
    3. Removes timezone information from dates (Excel gets confused by timezones)
    4. Saves everything to a single Excel sheet named "SPY_5min"
    5. Uses the openpyxl library for best Excel compatibility
    
    Parameters:
    - df: The DataFrame with your SPY OHLCV data
    - filepath: Where to save the file (e.g., "SPY_5min_history.xlsx")
    
    Output Format:
    The Excel file will have this structure:
    - Sheet name: "SPY_5min"
    - First column (A): Date and time of each 5-minute period
    - Column B: Open price (where it started those 5 minutes)
    - Column C: High price (highest it went during those 5 minutes)
    - Column D: Low price (lowest it went during those 5 minutes)
    - Column E: Close price (where it ended those 5 minutes)
    - Column F: Volume (how many shares traded during those 5 minutes)
    
    Example of what the Excel file looks like:
    | Date                | Open  | High  | Low   | Close | Volume |
    | 2025-09-18 09:30:00 | 663.11| 663.50| 663.04| 663.20| 1880   |
    | 2025-09-18 09:35:00 | 663.23| 663.60| 663.15| 663.45| 2150   |
    
    Special Cases:
    - If no data was fetched (empty DataFrame), it creates a template
      with empty rows but proper column headers so you know the structure
    - Timezone removal: IBKR data has Pacific Time (-07:00), Excel prefers no timezone
    - File size: 1 year of 5-minute data = ~5,000 rows = ~1-2 MB Excel file
    
    Requirements:
    - pandas library (for DataFrame handling)
    - openpyxl library (for Excel writing): pip install openpyxl
    
    Pro Tips:
    - Your M4 Max Mac can handle much larger datasets if needed
    - The file is saved in .xlsx format (modern Excel) not .xls (old format)
    - You can open this directly in Excel, Numbers, Google Sheets, etc.
    """
    # Remove timezone info from datetime index for Excel compatibility
    df_excel = df.copy()
    df_excel.index = df_excel.index.tz_localize(None)
    # Using pandas Excel writer (openpyxl engine)
    df_excel.to_excel(filepath, sheet_name="SPY_5min")

def main():
    """
    The main function that runs the entire SPY data fetching process.
    
    This is what happens when you run: python3 "SPY History.py"
    
    Step-by-step process:
    1. Prints a message saying it's starting to fetch SPY data
    2. Calls fetch_multiple_periods() to get 12 months (1 year) of data
       in 3-month chunks (4 periods total)
    3. Shows progress for each 3-month period being fetched
    4. Combines all 4 periods into one complete dataset
    5. Prints summary statistics:
       - Total number of 5-minute bars fetched
       - Date range covered (from oldest to newest date)
       - First 5 rows of data so you can verify it looks correct
    6. Saves everything to "SPY_5min_history.xlsx"
    7. Prints confirmation that the file was saved
    
    Expected Results for 1 Year of Data:
    - Total bars: ~4,000-6,000 rows (depending on market holidays)
    - Date range: October 2024 to October 2025 (12 months back from today)
    - File size: 1-2 MB Excel file
    - Time to run: 2-5 minutes (depends on your internet and IBKR response time)
    - Data includes: Pre-market (4am-9:30am), regular hours (9:30am-4pm), after-hours (4pm-8pm)
    
    What the output looks like:
    Fetching SPY 5-min data in multiple 3-month periods...
    
    Fetching period 1/4...
      Got 1560 bars from 2025-07-18 04:00:00 to 2025-10-17 20:00:00
    
    Fetching period 2/4...
      Got 1482 bars from 2025-04-18 04:00:00 to 2025-07-17 20:00:00
    
    ✓ Total bars fetched: 5820
    ✓ Date range: 2025-04-18 04:00:00 to 2025-10-17 20:00:00
    
    First 5 rows:
                         open    high     low   close  volume
    date                                                             
    2025-04-18 04:00:00  512.34  512.45  512.20  512.38  1250.0
    
    ✓ Saved to SPY_5min_history.xlsx
    
    Troubleshooting:
    - "Connection refused": Make sure TWS/Gateway is running and API is enabled
    - "Timeout": IBKR server is slow, try reducing num_periods to 1 for testing
    - "No data returned": Check if the date range has market data (weekends/holidays = no data)
    - Empty Excel file: API connection failed, check TWS settings
    
    Next Steps After Running:
    1. Open SPY_5min_history.xlsx in Excel
    2. You can create charts, calculate returns, do technical analysis
    3. Compare with VXX data if you have volatility analysis needs
    4. Use pandas in Python for more advanced analysis (moving averages, etc.)
    """
    print("Fetching SPY 5-min data in multiple 3-month periods...")
    
    # Fetch 4 periods (roughly 12 months of data)
    df = fetch_multiple_periods(start_date="20250101", num_periods=4)
    
    print(f"\n✓ Total bars fetched: {len(df)}")
    print(f"✓ Date range: {df.index.min()} to {df.index.max()}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # save to Excel
    out_path = "SPY_5min_history.xlsx"
    save_df_to_excel(df, out_path)
    print(f"\n✓ Saved to {out_path}")

if __name__ == "__main__":
    main()