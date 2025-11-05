#!/usr/bin/env python3
"""
Простой тест загрузки PDF
"""
import requests
import json
from pathlib import Path

# Конфигурация
DIFY_API_URL = "http://localhost/v1"
DIFY_API_KEY = "dataset-MxZ3Hqnt0uGZMLJjF2CBgpbt"
DIFY_DATASET_ID = "d948bc40-afea-41eb-aa15-480882e7ba98"
TEST_FILE = r"C:\Users\Andrey\OneDrive\Документы\Агентские договора\ИП Дубенков\Л-Старт\220602_Агентский договор тест true.pdf"

def upload_document(test_name: str):
    """Загрузка документа"""
    url = f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/document/create_by_file"
    
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}'
    }
    
    file_path = Path(TEST_FILE)
    new_name = f"{file_path.stem}_{test_name}{file_path.suffix}"
    
    with open(TEST_FILE, 'rb') as f:
        files = {'file': (new_name, f, 'application/pdf')}
        
        document_data = {
            'indexing_technique': 'high_quality',
            'process_rule': {
                'mode': 'automatic'
            }
        }
        form_data = {'data': json.dumps(document_data)}
        
        print(f"📤 Uploading: {new_name}")
        response = requests.post(url, headers=headers, files=files, data=form_data, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            document_id = result.get('document', {}).get('id')
            batch_id = result.get('batch')
            print(f"   ✅ Document ID: {document_id}")
            print(f"   Batch ID: {batch_id}")
            return document_id, batch_id
        else:
            print(f"   ❌ ERROR: {response.text}")
            return None, None

if __name__ == "__main__":
    import sys
    
    test_name = sys.argv[1] if len(sys.argv) > 1 else "test1"
    
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}\n")
    
    doc_id, batch_id = upload_document(test_name)
    
    if doc_id:
        print(f"\n✅ Upload successful!")
        print(f"   Document ID: {doc_id}")
        print(f"   Batch ID: {batch_id}")
        print(f"\nCheck logs with:")
        print(f"   docker compose logs worker --tail=100 | grep -i '{batch_id}\\|pdf\\|unstructured'")
    else:
        print(f"\n❌ Upload failed")
