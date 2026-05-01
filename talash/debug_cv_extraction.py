#!/usr/bin/env python3
"""
Debug script to diagnose CV extraction and storage issues.
"""
import os
import sys
import fitz
from runner import detect_cv_boundaries, _cv_fingerprint

def debug_pdf_parsing(pdf_path: str):
    """
    Test how the PDF is being parsed and split into CVs.
    """
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"DEBUG: Testing PDF Parsing")
    print(f"{'='*70}")
    print(f"\n📄 PDF Path: {pdf_path}")
    print(f"📊 File Size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    
    # Step 1: Open PDF and extract pages
    print(f"\n--- STEP 1: Extracting pages from PDF ---")
    doc = fitz.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    
    print(f"✓ Total pages: {len(pages)}")
    for i, page_text in enumerate(pages, 1):
        chars = len(page_text.strip())
        lines = len(page_text.strip().split('\n'))
        print(f"  Page {i}: {chars} chars, {lines} lines")
    
    # Step 2: Detect CV boundaries
    print(f"\n--- STEP 2: Detecting CV boundaries ---")
    cvs = detect_cv_boundaries(pages)
    print(f"✓ Total CVs detected: {len(cvs)}")
    
    for i, cv_text in enumerate(cvs, 1):
        fingerprint = _cv_fingerprint(cv_text)
        cv_id = f"cv_{fingerprint}"
        lines = len(cv_text.strip().split('\n'))
        chars = len(cv_text.strip())
        first_lines = cv_text.strip().split('\n')[:5]
        
        print(f"\n  CV {i}:")
        print(f"    ID:    {cv_id}")
        print(f"    Chars: {chars}")
        print(f"    Lines: {lines}")
        print(f"    First 5 lines:")
        for line in first_lines:
            print(f"      > {line[:70]}")
    
    # Step 3: Check database for existing CVs
    print(f"\n--- STEP 3: Checking database for existing CVs ---")
    try:
        from db_connect import get_session
        from db_models import Candidate
        
        session = get_session()
        candidates = session.query(Candidate).all()
        session.close()
        
        print(f"✓ Total candidates in DB: {len(candidates)}")
        for cand in candidates:
            print(f"  - {cand.candidate_id}: {cand.name} ({cand.email})")
        
        # Check for duplicates
        duplicate_count = {}
        for cand in candidates:
            duplicate_count[cand.candidate_id] = duplicate_count.get(cand.candidate_id, 0) + 1
        
        duplicates = {k: v for k, v in duplicate_count.items() if v > 1}
        if duplicates:
            print(f"\n⚠️  DUPLICATES FOUND:")
            for cid, count in duplicates.items():
                print(f"  - {cid}: appears {count} times")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_cv_extraction.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    debug_pdf_parsing(pdf_path)
