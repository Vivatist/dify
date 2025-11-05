#!/usr/bin/env python3
"""
Test script to verify PDF extraction with Unstructured API on/off
"""
import os
import time
import requests
from pathlib import Path

# Configuration
DIFY_API_URL = "http://localhost/v1"
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "your-api-key-here")
PDF_FILE_PATH = r"C:\Users\Andrey\OneDrive\Документы\Агентские договора\ИП Дубенков\Л-Старт\220602_Агентский договор (1).pdf"

def upload_file_to_knowledge(file_path: str, rename_as: str):
    """Upload file to Dify knowledge base"""
    
    # Step 1: Upload file
    print(f"\n{'='*60}")
    print(f"Uploading: {rename_as}")
    print(f"{'='*60}")
    
    with open(file_path, 'rb') as f:
        files = {
            'file': (rename_as, f, 'application/pdf')
        }
        headers = {
            'Authorization': f'Bearer {DIFY_API_KEY}'
        }
        
        upload_response = requests.post(
            f"{DIFY_API_URL}/files/upload",
            files=files,
            headers=headers,
            data={'user': 'test-user'}
        )
        
    if upload_response.status_code == 201:
        upload_data = upload_response.json()
        file_id = upload_data.get('id')
        print(f"✓ File uploaded successfully")
        print(f"  File ID: {file_id}")
        return file_id
    else:
        print(f"✗ Upload failed: {upload_response.status_code}")
        print(f"  Response: {upload_response.text}")
        return None

def check_docker_logs(keyword: str):
    """Check Docker logs for specific keyword"""
    print(f"\nChecking Docker logs for '{keyword}'...")
    os.system(f'docker compose logs api --tail=50 2>&1 | grep -i "{keyword}" | tail -5')

def main():
    if not Path(PDF_FILE_PATH).exists():
        print(f"Error: File not found: {PDF_FILE_PATH}")
        return
    
    print("PDF Extraction Test - Unstructured API Toggle")
    print("=" * 60)
    
    # Test 1: With Unstructured API enabled (default)
    print("\n\n### TEST 1: Unstructured API ENABLED (UNSTRUCTURED_ENABLED_PDF=true)")
    file_id_1 = upload_file_to_knowledge(PDF_FILE_PATH, "test_with_unstructured.pdf")
    
    if file_id_1:
        time.sleep(2)
        check_docker_logs("UnstructuredPdfExtractor")
        check_docker_logs("PdfExtractor")
    
    # Wait before test 2
    print("\n\n" + "="*60)
    print("Waiting 5 seconds before Test 2...")
    time.sleep(5)
    
    # Inform user to change env var
    print("\n\n### TEST 2: Unstructured API DISABLED")
    print("=" * 60)
    print("MANUAL STEP REQUIRED:")
    print("1. Edit docker/.env file")
    print("2. Change: UNSTRUCTURED_ENABLED_PDF=false")
    print("3. Run: docker compose restart api worker")
    print("4. Press ENTER to continue...")
    input()
    
    # Test 2: With Unstructured API disabled
    file_id_2 = upload_file_to_knowledge(PDF_FILE_PATH, "test_without_unstructured.pdf")
    
    if file_id_2:
        time.sleep(2)
        check_docker_logs("UnstructuredPdfExtractor")
        check_docker_logs("PdfExtractor")
    
    print("\n\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("\nFile IDs created:")
    if file_id_1:
        print(f"  With Unstructured:    {file_id_1}")
    if file_id_2:
        print(f"  Without Unstructured: {file_id_2}")
    
    print("\nExpected behavior:")
    print("  Test 1: Should see 'UnstructuredPdfExtractor' in logs")
    print("  Test 2: Should see 'PdfExtractor' (not Unstructured) in logs")

if __name__ == "__main__":
    main()
