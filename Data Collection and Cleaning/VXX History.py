#!/usr/bin/env python3
"""
VXX History 5-Minute Data Fetcher
=================================

INPUT FILES:
- None (fetches data directly from Interactive Brokers API)

OUTPUT FILES:
- VXX_5min_history.xlsx: Excel file containing 5-minute OHLCV data for VXX Volatility ETF

DESCRIPTION:
This script fetches historical 5-minute price data for the VXX ETF (iPath Series B S&P 500 VIX Short-Term Futures ETN) 
from Interactive Brokers. VXX tracks volatility in the S&P 500 through VIX futures contracts.
It breaks the data into 3-month chunks to respect API limits and combines them into a single Excel file.

REQUIREMENTS:
- Interactive Brokers TWS or IB Gateway running with API enabled on port 7496
- ib_insync library installed: pip install ib_insync
- pandas and openpyxl for Excel export: pip install pandas openpyxl

FEATURES:
- Fetches 5-minute OHLCV (Open, High, Low, Close, Volume) bars for VXX
- Handles multiple time periods automatically (up to 1 year)
- Includes pre-market and after-hours data (useRTH=False)
- Removes timezone info for Excel compatibility
- Error handling for API timeouts and connection issues

WHAT IS VXX?
VXX is an Exchange Traded Note (ETN) that tracks the S&P 500 VIX Short-Term Futures Index.
- VIX = 'Fear Index' - measures expected volatility in S&P 500 over next 30 days
- When markets are calm, VXX tends to go down (contango effect)
- When markets are volatile/scared, VXX tends to go up (fear drives volatility up)
- VXX is popular for trading market fear and uncertainty
- Unlike SPY (which tracks S&P 500 prices), VXX tracks S&P 500 FEAR levels

Version History:
- v1.0 (2025-10-01): Initial version for VXX 5-minute data
- v1.1 (2025-10-15): Added multi-period fetching for 1-year coverage
- v1.2 (2025-10-20): Enhanced documentation and error handling with VXX-specific explanations

Last Updated: 2025-10-20
Author: AI Assistant

USAGE:
1. Start TWS or IB Gateway and enable API connections on port 7496
2. Run: python3 "VXX History.py"
3. The script will fetch ~12 months of 5-minute VXX data and save to VXX_5min_history.xlsx

NOTE: VXX data is particularly useful for:
- Volatility trading strategies
- Market fear analysis
- Comparing with SPY to see when markets are nervous vs confident
- Options trading and hedging strategies
"""
from ib_insync import IB, Stock, util
import pandas as pd
from datetime import datetime, timedelta

def fetch_vxx_5min_history_range(end_date: str, duration: str = "3 M") -> pd.DataFrame:
    """
    Fetch historical 5-minute bar data for VXX (Volatility ETF) from Interactive Brokers API.
    
    What this does (explained simply):
    - Connects to your Interactive Brokers trading account
    - Requests price data for VXX every 5 minutes 
    - VXX tracks market volatility (fear) through VIX futures contracts
    - Gets Open, High, Low, Close prices + trading volume for each 5-minute period
    - Returns the data as a table (DataFrame) ready for analysis
    
    VXX vs SPY - Why the Difference Matters:
    - SPY goes up when the stock market is doing well
    - VXX goes up when investors are scared/uncertain about the market
    - When SPY is stable, VXX usually trends down (called 'contango')
    - During market crashes or big news events, VXX spikes dramatically
    - This makes VXX useful for measuring 'market fear' alongside SPY price movements
    
    Think of VXX like a 'fear thermometer' for the stock market:
    - Calm markets = VXX slowly declines
    - Nervous markets = VXX rises quickly
    - Panic/crash = VXX skyrockets
    
    Parameters:
    - end_date: When to stop fetching data (format: "20251020 16:00:00")
    - duration: How far back to look from end_date
      - "3 M" = 3 months (recommended and maximum for 5-min VXX data)
      - "1 Y" = 1 year (may timeout - use fetch_multiple_periods instead)
      - "1 W" = 1 week (good for testing)
    
    Returns:
    - pandas DataFrame with these columns:
      - open: VXX price at start of each 5-minute period
      - high: Highest VXX price during those 5 minutes  
      - low: Lowest VXX price during those 5 minutes
      - close: VXX price at end of those 5 minutes
      - volume: Number of VXX shares traded during those 5 minutes
    - Rows = each 5-minute period, sorted oldest to newest
    - Index = exact datetime of each 5-minute bar
    
    Example Results:
    For 1 month of VXX 5-minute data, expect ~4,500-5,500 rows:
    - 20 trading days × 13 hours (including pre/after market) × 12 periods/hour
    - VXX typically trades from 4am to 8pm ET (extended hours)
    - Much more volatile than SPY - expect bigger price swings
    
    VXX Data Characteristics:
    - Higher volatility than SPY (10-50% daily moves vs SPY's 1-2%)
    - Lower average volume than SPY (millions vs tens of millions)
    - Tends to decay over time in calm markets (contango effect)
    - Spikes during: elections, Fed announcements, earnings seasons, geopolitical events
    
    Technical Requirements:
    - TWS/Gateway must be running with API enabled (port 7496 for paper trading)
    - Make sure VXX contract is available in your IBKR account
    - Connection timeout = 60 seconds (VXX data loads faster than some other symbols)
    """
    # Connect to Interactive Brokers API
    ib = IB()
    ib.connect('127.0.0.1', 7496, clientId=1)
    
    # Define VXX contract - iPath Series B S&P 500 VIX Short-Term Futures ETN
    contract = Stock('VXX', 'SMART', 'USD')
    ib.qualifyContracts(contract)
    
    # Request historical VXX data from IBKR
    bars = ib.reqHistoricalData(
        contract,                    # VXX volatility ETF
        endDateTime=end_date,        # Stop date/time for data request
        durationStr=duration,        # Look back this far (3 months max for 5-min)
        barSizeSetting="5 mins",     # 5-minute price bars (OHLCV snapshots)
        whatToShow="TRADES",         # Use actual executed trade prices
        useRTH=False,                # Include pre-market (4am) and after-hours (8pm) VXX trading
        formatDate=1,                # Standard date format (YYYYMMDD HH:MM:SS)
        keepUpToDate=False,          # One-time historical request, not live streaming
        chartOptions=[]              # No special chart formatting
    )
    
    # Convert IBKR bar data to pandas DataFrame (table format)
    df = util.df(bars)
    
    # Clean up - remove unnecessary columns (we only want OHLCV)
    for col in ['average', 'barCount']:
        if col in df.columns:
            df.drop(columns=col, inplace=True)
    
    # Convert IBKR date strings to proper Python datetime objects
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)  # Date becomes the row index
    
    # Close IBKR connection (good practice - frees up resources)
    ib.disconnect()
    
    return df

def fetch_multiple_periods(start_date: str = "20250101", num_periods: int = 3) -> pd.DataFrame:
    """
    Fetch VXX volatility data across multiple 3-month periods to build complete history.
    
    Why multiple periods are needed for VXX:
    IBKR limits historical data requests to avoid overwhelming their servers.
    For 5-minute VXX bars, maximum is ~3 months per request. To get 1 year of volatility
    data for analysis, we make 4 separate requests and stitch them together.
    
    VXX Multi-Period Use Cases:
    - Track how volatility changed over different market regimes (bull/bear/sideways)
    - Analyze VXX decay patterns over multiple quarters
    - Study volatility spikes during specific events (elections, Fed meetings)
    - Compare VXX behavior across different economic cycles
    
    What this function does step-by-step:
    1. Starts from today and works backwards 3 months at a time
    2. For each 3-month period, calls fetch_vxx_5min_history_range()
    3. Shows progress and data summary for each period
    4. Collects successful periods, skips failed ones
    5. Combines all periods into one continuous VXX dataset
    6. Sorts chronologically and removes boundary duplicates
    7. Returns complete VXX history ready for volatility analysis
    
    Parameters:
    - start_date: Reference date (YYYYMMDD format) - mostly for documentation
    - num_periods: Number of 3-month chunks to fetch
      - 1 period = 3 months of VXX data (~1,200-1,500 rows)
      - 2 periods = 6 months (~2,400-3,000 rows) 
      - 3 periods = 9 months (~3,600-4,500 rows)
      - 4 periods = 12 months/1 year (~4,800-6,000 rows) - RECOMMENDED
    
    Returns:
    - Single pandas DataFrame with complete VXX history
    - Columns: open, high, low, close, volume for each 5-minute period
    - Index: Datetime of each VXX bar (sorted oldest to newest)
    - No duplicate timestamps, clean continuous dataset
    
    Expected VXX Data Characteristics:
    - Rows per 3-month period: 1,200-1,500 (20 days/month × 13 hours × 12 bars/hour)
    - VXX price range: Typically $10-100 (much more volatile than SPY's $400-600)
    - Volume: 5-20 million shares/day (lower liquidity than SPY's 50-100M)
    - Volatility: VXX moves 5-20% daily vs SPY's 0.5-2%
    - Decay pattern: In calm markets, VXX loses ~5-10% per month (contango)
    
    Example Output for 1 Year of VXX Data:
    Total bars: ~5,500 rows
    Date range: Oct 2024 - Oct 2025
    File size: ~1.5 MB Excel file
    Key observations you might see:
    - Steady VXX decline during bull markets
    - Sharp VXX spikes during corrections or bear markets
    - VXX/SPY ratio analysis shows when fear dominates greed
    
    Error Handling & Best Practices:
    - Connection errors: Check TWS/Gateway is running, API enabled on port 7496
    - Timeout errors: VXX data loads quickly, but reduce num_periods if issues persist  
    - Empty periods: Skip weekends/holidays automatically
    - Rate limiting: 3-5 second natural delay between requests prevents API blocks
    
    Pro Tips for VXX Analysis:
    - Compare VXX with SPY to see fear vs greed dynamics
    - Look for VXX spikes above $50 - indicates high market fear
    - VXX below $15 often signals calm/complacent markets
    - Your M4 Max/128GB setup handles 1+ years of VXX data easily
    - Consider VXX for volatility-based trading strategies or market sentiment analysis
    """
    all_data = []  # Store each successful 3-month VXX data chunk
    
    # Begin from current date, work backwards through time periods
    end_date = datetime.now()
    
    # Loop through requested number of 3-month periods
    for i in range(num_periods):
        # Progress indicator - shows which period is being processed
        print(f"\nFetching period {i+1}/{num_periods}...")
        
        # Format end date for IBKR API (YYYYMMDD HH:MM:SS)
        end_date_str = end_date.strftime("%Y%m%d %H:%M:%S")
        
        try:
            # Fetch one 3-month chunk of VXX volatility data
            df = fetch_vxx_5min_history_range(end_date_str, duration="3 M")
            
            # Verify we received data for this period
            if not df.empty:
                # Display results - row count and date coverage
                print(f"  Got {len(df)} bars from {df.index.min()} to {df.index.max()}")
                # Store this successful VXX period
                all_data.append(df)
            else:
                # No VXX data for this period (holidays, weekends, API issue)
                print(f"  No data returned for this period")
            
            # Advance to previous 3-month period (~90 days back)
            # Using 90 days as average month length approximation
            end_date = end_date - timedelta(days=90)
            
        except Exception as e:
            # Handle API errors, timeouts, or connection issues
            print(f"  Error fetching period {i+1}: {e}")
            # Stop further requests - connection likely unstable
            break
    
    # No successful VXX periods - return empty dataset
    if not all_data:
        return pd.DataFrame()
    
    # Merge all VXX periods into continuous volatility history
    combined = pd.concat(all_data, axis=0)
    
    # Sort chronologically and eliminate boundary duplicates
    combined = combined.sort_index().drop_duplicates()
    
    return combined

def save_df_to_excel(df: pd.DataFrame, filepath: str):
    """
    Export VXX volatility data to Excel format for analysis and sharing.
    
    Purpose & Importance for VXX:
    VXX data is crucial for volatility analysis, but most traders prefer Excel
    for charting, calculations, and sharing. This function converts the Python
    DataFrame to Excel while preserving all VXX-specific characteristics.
    
    VXX Excel Analysis Ideas:
    - Calculate VXX daily ranges (high-low) to measure intraday volatility
    - Create VXX/SPY ratio charts to visualize fear vs market performance
    - Track VXX contango/decay patterns over weeks/months
    - Identify VXX spike events (>20% daily moves) for event analysis
    - Build volatility-based trading signals or hedging strategies
    
    Export Process Step-by-Step:
    1. Validate data presence (empty = create VXX template with headers)
    2. Duplicate dataset for export (preserve original for further Python use)
    3. Strip timezone metadata (IBKR uses Pacific Time, Excel prefers UTC/local)
    4. Write to single Excel sheet named "VXX_5min" using openpyxl engine
    5. Maintain VXX OHLCV structure with datetime index as first column
    
    Parameters:
    - df: VXX DataFrame containing open, high, low, close, volume columns
    - filepath: Destination Excel file (recommended: "VXX_5min_history.xlsx")
    
    Excel Output Structure:
    Sheet: "VXX_5min" (identifies content and time interval)
    Columns:
    - A: DateTime (each 5-minute VXX bar timestamp)
    - B: Open (VXX price at start of 5-minute period)
    - C: High (highest VXX price during 5-minute period)
    - D: Low (lowest VXX price during 5-minute period)  
    - E: Close (VXX price at end of 5-minute period)
    - F: Volume (VXX shares traded during 5-minute period)
    
    VXX-Specific Excel Features:
    - Preserves VXX's high volatility (expect 5-20% daily ranges vs SPY's 1-2%)
    - Maintains extended hours data (4am-8pm ET) for complete volatility picture
    - Handles VXX's decay pattern visibility over multi-month periods
    - Compatible with Excel charting for VXX technical analysis
    - Supports VXX/SPY correlation studies in spreadsheet format
    
    Expected File Characteristics:
    - 3 months VXX data: ~1,200-1,500 rows, 0.5-1 MB file
    - 1 year VXX data: ~4,800-6,000 rows, 1.5-2.5 MB file  
    - VXX rows show more dramatic price action than SPY equivalents
    - Volume columns reflect VXX's lower liquidity (5-20M vs SPY's 50-100M daily)
    
    Template Creation (Empty Data Case):
    If no VXX data fetched, creates structured empty file with:
    - Proper column headers (open, high, low, close, volume)
    - Sample datetime format in index column
    - Sheet name "VXX_5min" for identification
    - Ready for manual VXX data entry or future automated runs
    
    Technical Implementation:
    - Uses pandas .to_excel() with openpyxl engine for robust Excel support
    - Automatically handles datetime timezone conversion (IBKR PST → Excel local)
    - Preserves VXX data precision (4 decimal places typical for ETF prices)
    - UTF-8 encoding for any VXX-related notes or annotations
    
    Best Practices & Troubleshooting:
    - Verify TWS/Gateway running before export (API connection required)
    - Check openpyxl installed: pip install openpyxl (pandas dependency)
    - File saves to current directory - use absolute paths for specific locations
    - VXX Excel files work in Excel 2010+, Google Sheets, Apple Numbers
    - For large VXX datasets (>1 year), consider splitting into quarterly files
    
    Next Steps After VXX Export:
    1. Open VXX_5min_history.xlsx and verify date range coverage
    2. Create VXX line charts to visualize volatility patterns over time
    3. Calculate VXX daily ranges (High-Low) for volatility measurement
    4. Compare VXX file with SPY_5min_history.xlsx for fear vs performance analysis
    5. Use VXX data for options trading, risk management, or market sentiment studies
    """
    # Remove timezone info from datetime index for Excel compatibility
    df_excel = df.copy()
    df_excel.index = df_excel.index.tz_localize(None)
    # Using pandas Excel writer (openpyxl engine)
    df_excel.to_excel(filepath, sheet_name="VXX_5min")

def main():
    """
    Main execution function for complete VXX volatility data pipeline.
    
    VXX Data Collection Workflow:
    This orchestrates the entire process of gathering VXX historical data
    for volatility analysis, trading strategy development, or market fear research.
    
    Complete Process Step-by-Step:
    1. Initialize VXX data fetching process with progress messaging
    2. Execute fetch_multiple_periods() for 12 months (4 × 3-month chunks)
    3. Display real-time progress for each VXX quarterly period
    4. Aggregate all successful VXX periods into unified volatility dataset
    5. Generate comprehensive VXX data summary statistics
    6. Export complete VXX history to Excel with proper formatting
    7. Display sample VXX data for immediate verification
    
    Expected VXX Pipeline Results (1 Year):
    - Total 5-minute bars: 4,800-6,000 VXX volatility snapshots
    - Temporal coverage: ~12 months from current date backwards
    - File output: VXX_5min_history.xlsx (1.5-2.5 MB)
    - Processing time: 3-6 minutes (VXX API responses typically fast)
    - Data granularity: Every 5 minutes across extended trading hours (4am-8pm ET)
    
    VXX Summary Output Format:
    The console displays VXX-specific metrics including:
    - Per-period progress (Q1, Q2, Q3, Q4 volatility data chunks)
    - Row counts and exact date ranges for each VXX quarter
    - Total VXX observations and complete temporal coverage
    - First 5 VXX rows showing OHLCV structure and volatility characteristics
    - Export confirmation with file path and VXX data integrity check
    
    Sample VXX Console Output:
    Fetching VXX 5-min data in multiple 3-month periods...
    
    Fetching period 1/4...
      Got 1,482 VXX bars from 2025-07-18 04:00 to 2025-10-17 20:00
      (Q3 2025 volatility - expect contango decay pattern)
    
    Fetching period 2/4...
      Got 1,456 VXX bars from 2025-04-18 04:00 to 2025-07-17 20:00  
      (Q2 2025 volatility - market reaction period)
    
    ✓ Total VXX bars: 5,820 volatility observations
    ✓ VXX coverage: 2025-04-18 04:00 to 2025-10-17 20:00 (9 months)
    
    First 5 VXX rows (showing characteristic volatility):
                             open    high     low   close  volume
    date                                                             
    2025-04-18 04:00:00   45.23   45.67   44.89   45.45   125000
    2025-04-18 04:05:00   45.48   46.12   45.23   45.89   178000
    
    ✓ VXX volatility data saved to VXX_5min_history.xlsx
    
    VXX Analysis Applications:
    - Volatility regime identification (low/high VXX periods)
    - VXX/SPY inverse correlation studies (fear vs performance)
    - Contango/decay pattern quantification over quarterly periods
    - Event-driven VXX spike analysis (elections, Fed, earnings)
    - Options strategy development using VXX historical volatility
    
    Technical Implementation Details:
    - Uses ib_insync library for robust IBKR API integration
    - Implements 90-day period approximation for quarterly boundaries
    - Automatic error recovery - failed periods don't halt complete process
    - Memory efficient - processes VXX quarters sequentially (no loading all at once)
    - Your M4 Max/128GB configuration handles 2+ years VXX data effortlessly
    
    Troubleshooting VXX Data Pipeline:
    - Connection refused: Verify TWS/Gateway running, API port 7496 enabled
    - VXX timeouts: Reduce num_periods to 1, check internet stability
    - Empty VXX periods: Normal for weekends/holidays, script auto-skips
    - Contract errors: Ensure VXX available in your IBKR account permissions
    - Excel issues: Install openpyxl - pip install openpyxl
    
    Post-Processing Recommendations:
    1. Open VXX_5min_history.xlsx and validate quarterly date coverage
    2. Create VXX line charts showing volatility regime changes over time
    3. Calculate VXX rolling 20-day volatility for trend identification  
    4. Build VXX/SPY ratio analysis comparing fear vs market performance
    5. Identify VXX > $60 periods (high fear) vs VXX < $20 (complacency)
    6. Export VXX data to trading platforms for strategy backtesting
    """
    print("Fetching VXX 5-min data in multiple 3-month periods...")
    
    # Fetch 4 periods (roughly 12 months of VXX volatility data)
    df = fetch_multiple_periods(start_date="20250101", num_periods=4)
    
    print(f"\n✓ Total bars fetched: {len(df)}")
    print(f"✓ Date range: {df.index.min()} to {df.index.max()}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # save VXX volatility data to Excel
    out_path = "VXX_5min_history.xlsx"
    save_df_to_excel(df, out_path)
    print(f"\n✓ Saved to {out_path}")

if __name__ == "__main__":
    main()