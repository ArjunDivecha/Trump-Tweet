# Bug Analysis - Data Collection Pipeline
## Date: 2025-10-20
## Scripts Analyzed: clean_trump_archive.py, tariff_classifier_optimized.py

---

## 🐛 CRITICAL BUGS FOUND

### Bug #1: INCORRECT DATE HANDLING IN DEDUPLICATION (CRITICAL)
**File**: `clean_trump_archive.py`
**Lines**: 86-89
**Severity**: 🔴 CRITICAL - Causes incorrect timestamps in analysis

**Problem**:
When the same post appears multiple times with different dates, the script keeps the FIRST occurrence it encounters, regardless of which date is correct.

**Example**:
```
Post: "China purposefully not buying our Soybeans..."
Appears in raw data:
  - 5 times with date: 2025-10-18 18:57:00
  - 1 time with date: 2025-10-14 15:37:00
  - Actual date (from website): 2025-10-10

Script keeps: 2025-10-18 (wrong!)
Should keep: 2025-10-14 (closer, but still wrong)
```

**Impact on Event Study**:
- T+0, T+1, T+2 windows measure WRONG time periods
- Market reactions are misaligned by days
- Statistical tests compare incorrect timeframes
- Alpha calculations are based on wrong dates

**Current Code** (BUGGY):
```python
for entry in json_data:
    for i, post_content in enumerate(cleaned_posts):
        # Skip duplicates
        if post_content in seen_content:
            continue  # ❌ WRONG: Just skips, keeps first occurrence
        seen_content.add(post_content)
        # Uses whatever date was on first occurrence
```

**Fixed Code**:
```python
# Track duplicates with dates to keep earliest
seen_posts = {}  # {content: {post data}}

for entry in json_data:
    for i, post_content in enumerate(cleaned_posts):
        if post_content in seen_posts:
            # Compare dates, keep EARLIEST
            existing_date = seen_posts[post_content].get('created_at', '')
            current_date = entry.get('created_at', '')

            # Keep whichever is earlier (or non-empty)
            if current_date and (not existing_date or current_date < existing_date):
                seen_posts[post_content] = {full post data with current_date}
        else:
            seen_posts[post_content] = {full post data}
```

---

### Bug #2: REDUNDANT DEDUPLICATION
**File**: `clean_trump_archive.py`
**Lines**: 157-166
**Severity**: 🟡 MODERATE - Inefficient but not breaking

**Problem**:
The script does deduplication TWICE:
1. Lines 86-89: In `extract_individual_posts()`
2. Lines 157-166: In `main()` after extraction

**Impact**:
- Wastes processing time
- Confusing code structure
- Second pass is redundant (first already removed duplicates)

**Recommendation**: Remove lines 157-166 (second deduplication)

---

### Bug #3: NO DATE VALIDATION
**File**: `clean_trump_archive.py`
**Severity**: 🟡 MODERATE - Could cause downstream errors

**Problem**:
The script accepts any date format without validation. If scraper returns malformed dates, they pass through unchecked.

**Examples of potential issues**:
- Empty strings: `created_at: ""`
- Invalid formats: `created_at: "N/A"`
- Future dates: `created_at: "2099-01-01"`
- Timezone issues: `2025-10-18T18:57:00` vs `2025-10-18T18:57:00+00:00`

**Fix**: Add date validation and parsing

---

### Bug #4: POST_ID GENERATION USES WRONG DATE
**File**: `clean_trump_archive.py`
**Line**: 93
**Severity**: 🟡 MODERATE - Inconsistent IDs

**Problem**:
```python
'post_id': f"{entry.get('post_id', '')}_{i}" if entry.get('post_id') else f"{date}_{i}",
```

Uses `date` from current entry, which might not be the earliest date for this content.

**Impact**: Post IDs don't match actual dates after deduplication fix

---

## ✅ CLEAN CODE IN tariff_classifier_optimized.py

### Reviewed Sections:
1. ✅ **CSV Loading** (lines 972-987): Just reads data as-is, no date modification
2. ✅ **Batch Processing**: Correctly groups posts without altering metadata
3. ✅ **Checkpoint/Resume**: Properly tracks processed post_ids
4. ✅ **Error Handling**: Robust try/except blocks
5. ✅ **Output Format**: Preserves original date fields from input CSV

**No bugs found in classifier** - it correctly passes through whatever dates it receives from the cleaning script.

**HOWEVER**: The classifier output will be WRONG because it's working with WRONG dates from the cleaning script!

---

## 🔧 REQUIRED FIXES - PRIORITY ORDER

### Priority 1: Fix Deduplication Date Logic (CRITICAL)
Replace lines 70-108 in `clean_trump_archive.py` with improved version that:
1. Tracks all occurrences of each post with their dates
2. Keeps the EARLIEST valid date for each unique post
3. Validates dates before comparison
4. Logs when multiple dates are found for same post

### Priority 2: Remove Redundant Deduplication
Delete lines 157-166 in `clean_trump_archive.py`

### Priority 3: Add Date Validation
Add function to validate and normalize dates before saving

### Priority 4: Update Post ID Generation
Use the kept (earliest) date for post_id, not the current entry date

---

## 📋 ACTION PLAN

1. ✅ Backup current files:
   - `cp clean_trump_archive.py clean_trump_archive.py.BACKUP`

2. ✅ Apply fixes to `clean_trump_archive.py`

3. ✅ Re-run cleaning script:
   ```bash
   cd "Data Collection and Cleaning"
   python3 clean_trump_archive.py
   ```

4. ✅ Verify output dates:
   - Check known posts (e.g., China Soybean post)
   - Confirm earliest dates are kept
   - Validate no duplicates remain

5. ✅ Re-run tariff classifier:
   ```bash
   python3 tariff_classifier_optimized.py YOUR_API_KEY --resume
   ```
   (Will use checkpoint if available, or start fresh)

6. ✅ Validate timestamps in final output

7. ✅ Re-run event study analysis with corrected dates

---

## 💰 COST IMPLICATIONS

- Re-running cleaner: Free, ~2-3 minutes
- Re-running classifier:
  - If using checkpoint: Free (skips already processed)
  - If starting fresh: ~$7-10, 45-60 minutes
  - **Recommendation**: Delete checkpoint.json to ensure clean analysis with fixed dates

---

## 📊 EXPECTED CHANGES

### Before Fix (Current State):
- China Soybean post: 2025-10-18 18:57:00 ❌
- Multiple posts with shifted dates (last occurrence kept)
- Event study measures wrong T+0, T+1, T+2 periods

### After Fix:
- China Soybean post: 2025-10-14 15:37:00 ✅ (earliest available)
  - Still wrong (actual is Oct 10), but better than Oct 18
  - Scraper issue remains (separate bug)
- All duplicates use earliest date
- Event study windows aligned closer to actual tweet times

---

## 🔍 REMAINING ISSUES (Out of Scope)

### Scraper Timestamp Accuracy
The scraper is capturing posts with wrong dates (e.g., Oct 10 post → Oct 14/18).

**Root cause**: Likely issues in `trumpstruth_scraper_auto.py`:
- Scraping from different pages/views shows different timestamps
- Pagination might be assigning dates based on scrape time, not post time
- Website's timestamp display might be inconsistent

**Recommended**: Separate investigation of scraper timestamp extraction logic

---

Last Updated: 2025-10-20
Analyst: Claude Code
