#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ТЕСТ 1: Загрузка через стандартный парсер (PdfExtractor)
Файл: test2 Соглашение погаш. задолжен. от 25.02.2025 АО QARMET.pdf
"""
import requests
import json
from pathlib import Path
import time

# Конфигурация
DIFY_API_URL = "http://localhost/v1"
DIFY_API_KEY = "dataset-MxZ3Hqnt0uGZMLJjF2CBgpbt"
DIFY_DATASET_ID = "d948bc40-afea-41eb-aa15-480882e7ba98"

file_path = r'C:\Users\Andrey\Downloads\test\test2 Соглашение погаш. задолжен. от 25.02.2025 АО QARMET.pdf'
pdf_path = Path(file_path)

print("="*80)
print("ТЕСТ 1: Стандартный парсер (PdfExtractor без OCR)")
print("="*80)
print(f"\n📄 Файл: {pdf_path.name}")

if not pdf_path.exists():
    print(f"❌ Файл не найден: {file_path}")
    exit(1)

file_size = pdf_path.stat().st_size
print(f"📊 Размер: {file_size:,} байт ({file_size / 1024:.1f} KB)")
print(f"⚙️  Метод: PdfExtractor (pypdfium2)")
print(f"⚙️  UNSTRUCTURED_ENABLED_PDF=false")

url = f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/document/create_by_file"
headers = {'Authorization': f'Bearer {DIFY_API_KEY}'}

print(f"\n📤 Начинаю загрузку...")
start_time = time.time()

try:
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        data = {'data': json.dumps({
            'indexing_technique': 'high_quality',
            'process_rule': {'mode': 'automatic'}
        })}
        
        response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        
    upload_time = time.time() - start_time
    
    print(f"⏱️  Время загрузки: {upload_time:.2f} сек")
    print(f"📡 HTTP Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        doc_id = result.get('document', {}).get('id')
        batch_id = result.get('batch')
        
        print(f"\n✅ Загрузка успешна!")
        print(f"📝 Document ID: {doc_id}")
        print(f"📦 Batch ID: {batch_id}")
        
        print(f"\n" + "="*80)
        print("Проверка логов:")
        print("="*80)
        print(f"\nКоманда для проверки экстрактора:")
        print(f'docker compose -f docker/docker-compose.yaml logs worker --tail=50 | grep -E "PDF extraction|Using extractor"')
        
        print(f"\nОжидается:")
        print(f"  - PDF extraction: UNSTRUCTURED_ENABLED_PDF=False")
        print(f"  - Using extractor: PdfExtractor")
        
        print(f"\n⏳ Подождите ~30 секунд для завершения обработки документа")
        print(f"   Затем проверьте содержимое в веб-интерфейсе Dify")
        
    else:
        print(f"\n❌ Ошибка загрузки!")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"\n❌ Исключение: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
