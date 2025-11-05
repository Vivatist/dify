#!/usr/bin/env python3
"""
Тест загрузки PDF для проверки работы Unstructured API
"""
import requests
import json
import time
from pathlib import Path

# Конфигурация
DIFY_API_URL = "http://localhost/v1"
DIFY_API_KEY = "dataset-MxZ3Hqnt0uGZMLJjF2CBgpbt"
DIFY_DATASET_ID = "d948bc40-afea-41eb-aa15-480882e7ba98"

def upload_test_pdf():
    """Загрузка тестового PDF файла"""
    
    # Создаем простой тестовый файл
    test_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources 4 0 R /MediaBox [0 0 612 792] /Contents 5 0 R >>\nendobj\n4 0 obj\n<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >>\nendobj\n5 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 100 700 Td (Test PDF Document) Tj ET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000214 00000 n\n0000000301 00000 n\ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n395\n%%EOF"
    
    url = f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/document/create_by_file"
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}'
    }
    
    timestamp = int(time.time())
    filename = f"test_unstructured_{timestamp}.pdf"
    
    files = {'file': (filename, test_content, 'application/pdf')}
    
    document_data = {
        'indexing_technique': 'high_quality',
        'process_rule': {
            'mode': 'automatic'
        }
    }
    form_data = {'data': json.dumps(document_data)}
    
    print(f"📤 Загрузка файла: {filename}")
    print(f"   URL: {url}")
    
    try:
        response = requests.post(url, headers=headers, files=files, data=form_data, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            document_id = result.get('document', {}).get('id')
            batch_id = result.get('batch')
            print(f"   ✅ Успешно загружен!")
            print(f"   Document ID: {document_id}")
            print(f"   Batch ID: {batch_id}")
            print(f"\nПроверьте логи worker:")
            print(f"   docker compose -f docker/docker-compose.yaml logs worker --tail=50 | grep -i 'PDF extraction\\|Using extractor'")
            return document_id, batch_id
        else:
            print(f"   ❌ Ошибка: {response.text}")
            return None, None
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return None, None

if __name__ == "__main__":
    print("="*80)
    print("Тест загрузки PDF с Unstructured API")
    print("="*80)
    print()
    
    doc_id, batch_id = upload_test_pdf()
    
    if doc_id:
        print("\n" + "="*80)
        print("Тест завершен успешно!")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("Тест не удался")
        print("="*80)
