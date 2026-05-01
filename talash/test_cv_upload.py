#!/usr/bin/env python3
"""
Quick test to verify CV extraction and storage works correctly.
Tests:
  1. Parse PDF with multiple CVs
  2. Check database storage
  3. Verify no duplicates
"""
import asyncio
from runner import process_all_cvs_sequential
from db_connect import get_session
from db_models import Candidate

async def test_cv_upload(pdf_path: str):
    """Test CV upload end-to-end"""
    print(f"\n{'='*70}")
    print(f"TESTING CV UPLOAD: {pdf_path}")
    print(f"{'='*70}\n")
    
    # Get initial database state
    session = get_session()
    initial_count = session.query(Candidate).count()
    initial_candidates = {c.candidate_id: c.name for c in session.query(Candidate).all()}
    session.close()
    
    print(f"📊 INITIAL STATE:")
    print(f"   Total candidates in DB: {initial_count}")
    if initial_candidates:
        for cid, name in initial_candidates.items():
            print(f"   - {cid}: {name}")
    
    # Process PDF
    print(f"\n🔄 PROCESSING PDF...")
    results = await process_all_cvs_sequential(pdf_path)
    
    print(f"\n✅ PROCESSING RESULTS:")
    print(f"   Total results returned: {len(results)}")
    for i, result in enumerate(results, 1):
        if "error" in result:
            print(f"   [{i}] ERROR: {result.get('error')}")
        else:
            cid = result.get("_candidate_id", "unknown")
            name = result.get("personal_info", {}).get("name", "N/A")
            print(f"   [{i}] {cid}: {name}")
    
    # Get final database state
    print(f"\n📊 FINAL STATE:")
    session = get_session()
    final_count = session.query(Candidate).count()
    final_candidates = [(c.id, c.candidate_id, c.name) for c in session.query(Candidate).all()]
    session.close()
    
    print(f"   Total candidates in DB: {final_count}")
    for db_id, cid, name in final_candidates:
        status = "NEW" if cid not in initial_candidates else "UPDATED"
        print(f"   - DB ID {db_id}: {cid}: {name} [{status}]")
    
    # Verify integrity
    print(f"\n🔍 INTEGRITY CHECK:")
    added = final_count - initial_count
    print(f"   CVs added to DB: {added}")
    print(f"   CVs extracted from PDF: {len([r for r in results if 'error' not in r])}")
    
    if len([r for r in results if 'error' not in r]) == added:
        print(f"   ✅ PASS: All extracted CVs stored correctly")
    else:
        print(f"   ❌ FAIL: Mismatch between extracted and stored CVs")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_cv_upload.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    asyncio.run(test_cv_upload(pdf_path))
