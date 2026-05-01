# CV Storage Fix - Testing & Verification Guide

## Changes Made

### 1. **Batch Processing Implementation**
**File**: `runner.py`

**Problem**: CVs were processed individually, which could cause database sync issues.

**Solution**: 
- Created new `process_all_cvs_batch()` function
- Modified `process_all_cvs_sequential()` to use batch processing
- Now ALL CVs from a PDF are processed together in a SINGLE pipeline invocation

**Why This Works**:
- All CVs go through extraction together
- Database storage happens in one transaction
- No CV can be lost or overwritten
- Maintains data consistency

### 2. **Enhanced Logging**
**File**: `runner.py` - database_storage function

**Added**:
- Count of CVs being saved
- Index indicator [N/M] for each CV
- Summary showing how many were successfully stored
- Better error reporting

## Testing Instructions

### Test 1: Extract Multiple CVs from Single PDF

```bash
# First, create a test PDF with 3 different CVs
# (or use your existing PDF with multiple CVs)

# Run the diagnostic script
python debug_cv_extraction.py path/to/your/pdf.pdf

# Expected output:
# - Should show "Total CVs detected: 3"
# - Each CV should have different fingerprint ID
# - First 5 lines of each CV should be different
```

### Test 2: Upload via API and Verify Database Storage

```bash
# Option A: Use curl
curl -X POST http://localhost:8000/upload \
  -F "file=@path/to/pdf.pdf"

# Expected response:
# {
#   "message": "PDF uploaded. 3 CV(s) detected (3 new, 0 already in DB). Processing queued.",
#   "candidates_count": 3,
#   "new_count": 3,
#   "existing_count": 0,
#   "candidates": [
#     {"cv_id": "cv_xxx", "status": "new — will be processed", "preview": "..."},
#     {"cv_id": "cv_yyy", "status": "new — will be processed", "preview": "..."},
#     {"cv_id": "cv_zzz", "status": "new — will be processed", "preview": "..."}
#   ]
# }

# Option B: Use test script
python test_cv_upload.py path/to/pdf.pdf
```

### Test 3: Run Full End-to-End Test

```bash
# Clear database (CAUTION - only in dev!)
# psql -U talash -d talash_db -c "DELETE FROM candidates;"

# Upload PDF with 3 CVs
python test_cv_upload.py path/to/your/pdf.pdf

# Expected output:
# 📊 INITIAL STATE:
#    Total candidates in DB: 0
#
# 🔄 PROCESSING PDF...
# [1/3] Extracting cv_xxxx...
# [2/3] Extracting cv_yyyy...
# [3/3] Extracting cv_zzzz...
#
# DATABASE STORAGE: Saving 3 candidates
# [1/3] ➕ New: John Doe [cv_xxxx]
# [2/3] ➕ New: Jane Smith [cv_yyyy]
# [3/3] ➕ New: Bob Johnson [cv_zzzz]
# ✅ Database commit complete: 3/3 candidates saved
#
# 📊 FINAL STATE:
#    Total candidates in DB: 3
#    - DB ID 1: cv_xxxx: John Doe [NEW]
#    - DB ID 2: cv_yyyy: Jane Smith [NEW]
#    - DB ID 3: cv_zzzz: Bob Johnson [NEW]
#
# 🔍 INTEGRITY CHECK:
#    CVs added to DB: 3
#    CVs extracted from PDF: 3
#    ✅ PASS: All extracted CVs stored correctly
```

### Test 4: Re-upload Same PDF (Should Update, Not Duplicate)

```bash
# After Test 3, upload the SAME PDF again
python test_cv_upload.py path/to/your/pdf.pdf

# Expected output:
# 📊 INITIAL STATE:
#    Total candidates in DB: 3
#    - cv_xxxx: John Doe
#    - cv_yyyy: Jane Smith
#    - cv_zzzz: Bob Johnson
#
# 🔄 PROCESSING PDF...
# DATABASE STORAGE: Saving 3 candidates
# [1/3] 🔄 Update: John Doe [cv_xxxx]
# [2/3] 🔄 Update: Jane Smith [cv_yyyy]
# [3/3] 🔄 Update: Bob Johnson [cv_zzzz]
# ✅ Database commit complete: 3/3 candidates saved
#
# 📊 FINAL STATE:
#    Total candidates in DB: 3  ← SAME as before, not 6!
#    - DB ID 1: cv_xxxx: John Doe [UPDATED]
#    - DB ID 2: cv_yyyy: Jane Smith [UPDATED]
#    - DB ID 3: cv_zzzz: Bob Johnson [UPDATED]
#
# 🔍 INTEGRITY CHECK:
#    CVs added to DB: 0  ← No new additions
#    CVs extracted from PDF: 3
#    ✅ PASS: All extracted CVs handled correctly
```

### Test 5: Upload Different PDF with 2 New CVs

```bash
# Create a new PDF with 2 different CVs (or use different file)
python test_cv_upload.py path/to/new/pdf.pdf

# Expected output:
# 📊 INITIAL STATE:
#    Total candidates in DB: 3
#    - cv_xxxx: John Doe
#    - cv_yyyy: Jane Smith
#    - cv_zzzz: Bob Johnson
#
# 🔄 PROCESSING PDF...
# DATABASE STORAGE: Saving 2 candidates
# [1/2] ➕ New: Alice Brown [cv_aaaa]
# [2/2] ➕ New: Charlie White [cv_bbbb]
# ✅ Database commit complete: 2/2 candidates saved
#
# 📊 FINAL STATE:
#    Total candidates in DB: 5
#    - DB ID 1: cv_xxxx: John Doe [EXISTING]
#    - DB ID 2: cv_yyyy: Jane Smith [EXISTING]
#    - DB ID 3: cv_zzzz: Bob Johnson [EXISTING]
#    - DB ID 4: cv_aaaa: Alice Brown [NEW]
#    - DB ID 5: cv_bbbb: Charlie White [NEW]
#
# 🔍 INTEGRITY CHECK:
#    CVs added to DB: 2
#    CVs extracted from PDF: 2
#    ✅ PASS: New CVs added without overwriting existing ones
```

## Key Points

1. **Batch Processing**: All CVs from a PDF are now processed together, not individually
2. **Stable IDs**: Each CV gets a fingerprint-based ID that doesn't change
3. **Transaction Safety**: All CVs saved in single database transaction
4. **Smart Upsert**: 
   - Same CV in multiple uploads → Updates existing record
   - Different CV → Creates new record
   - No duplicates created

## Troubleshooting

### Problem: Still only storing 1 CV from multi-CV PDF

**Diagnostics**:
```bash
python debug_cv_extraction.py path/to/pdf.pdf
```

**Check**:
1. Does "Total CVs detected" show correct count?
2. Are fingerprints different for each CV?
3. Are first lines different for each CV?

If CVs aren't being detected correctly, the issue is in `detect_cv_boundaries()` function.

### Problem: Uploaded CVs show up in DB but background processing fails

Check the backend logs for scoring module errors:
- Look for `education_analysis`, `research_analysis`, etc. error messages
- These are separate from CV extraction/storage

### Problem: Database shows 2 copies of same candidate

This shouldn't happen with the new code, but if it does:

```bash
# Check for duplicates
psql -U talash -d talash_db -c "
  SELECT candidate_id, COUNT(*) as count 
  FROM candidates 
  GROUP BY candidate_id 
  HAVING COUNT(*) > 1;
"

# If found, investigate the fingerprint logic
python debug_cv_extraction.py path/to/pdf.pdf
```

## Next Steps

1. Run Test 1-3 to verify fix is working
2. If all tests pass, the issue is resolved
3. If tests fail, check troubleshooting section
4. If still issues, provide output from debug script
