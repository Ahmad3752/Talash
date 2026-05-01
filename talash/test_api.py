"""
Simple test script to verify the backend API is working correctly
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_list_candidates():
    """Test listing candidates"""
    print("\n=== Listing All Candidates ===")
    response = requests.get(f"{BASE_URL}/candidates")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        candidates = response.json()
        print(f"Found {len(candidates)} candidate(s)")
        for cand in candidates[:3]:  # Show first 3
            print(f"  - ID {cand['id']}: {cand['name']} ({cand['email']})")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def test_upload_pdf(pdf_path):
    """Test uploading a PDF"""
    print(f"\n=== Uploading PDF: {pdf_path} ===")
    
    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        return False
    
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Message: {data['message']}")
        print(f"Candidates detected: {data['candidates_count']}")
        print(f"Status: {data['status']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_candidate_details(candidate_id):
    """Test getting candidate details"""
    print(f"\n=== Getting Candidate {candidate_id} Details ===")
    response = requests.get(f"{BASE_URL}/candidates/{candidate_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        candidate = response.json()
        print(f"Name: {candidate['name']}")
        print(f"Email: {candidate['email']}")
        print(f"Education: {len(candidate['education'])} record(s)")
        print(f"Experience: {len(candidate['experience'])} record(s)")
        print(f"Skills: {len(candidate['skills'])} skill(s)")
        print(f"Publications: {len(candidate['publications'])} publication(s)")
        
        # Show summary if available
        if candidate.get('cv_summary'):
            summary = candidate['cv_summary']
            print(f"\nCV Summary:")
            print(f"  Overall Score: {summary['overall_score']}/100")
            print(f"  Overall Grade: {summary['overall_grade']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_candidate_education(candidate_id):
    """Test getting candidate education"""
    print(f"\n=== Getting Candidate {candidate_id} Education ===")
    response = requests.get(f"{BASE_URL}/candidates/{candidate_id}/education")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        education = response.json()
        print(f"Found {len(education)} education record(s)")
        for edu in education[:2]:
            print(f"  - {edu['degree']} in {edu['field']} from {edu['institution']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("BACKEND API TEST SCRIPT")
    print("="*60)
    
    # Test health
    if not test_health():
        print("\n✗ Backend is not running!")
        exit(1)
    
    # Test list candidates
    test_list_candidates()
    
    # Optional: Test uploading PDF if it exists
    pdf_path = "C:\\Projects\\Talash\\Cvs\\output_first_10_pages.pdf"
    if Path(pdf_path).exists():
        print("\n" + "="*60)
        print("UPLOADING PDF TEST")
        print("="*60)
        if test_upload_pdf(pdf_path):
            print("\n✓ PDF uploaded successfully")
            print("  Processing happens in the background...")
            print("  Check the API logs for processing status")
    
    # Test getting candidate 1 if exists
    print("\n" + "="*60)
    print("CHECKING EXISTING CANDIDATES")
    print("="*60)
    response = requests.get(f"{BASE_URL}/candidates")
    if response.status_code == 200:
        candidates = response.json()
        if candidates:
            first_candidate = candidates[0]
            test_candidate_details(first_candidate['id'])
            test_candidate_education(first_candidate['id'])
    
    print("\n" + "="*60)
    print("TESTS COMPLETED")
    print("="*60)
    print("\nAccess Swagger UI at: http://localhost:8000/docs")
    print("Or ReDoc at: http://localhost:8000/redoc")
