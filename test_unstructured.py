#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест Unstructured API с OCR на реальном файле test1
"""
import requests
import json
from pathlib import Path
import time

# Конфигурация
DIFY_API_URL = "http://localhost/v1"
DIFY_API_KEY = "dataset-MxZ3Hqnt0uGZMLJjF2CBgpbt"
DIFY_DATASET_ID = "d948bc40-afea-41eb-aa15-480882e7ba98"

def upload_pdf(file_path: str):
    """Загрузка PDF через Dify API"""
    pdf_path = Path(file_path)
    
    if not pdf_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        return None, None
    
    print("="*61)
    print("ТЕСТ 2: Unstructured API с OCR (UnstructuredPdfExtractor)")
    print("="*61)
    print()
    print(f"📄 Файл: {pdf_path.name}")
    print(f"📊 Размер: {pdf_path.stat().st_size:,} байт ({pdf_path.stat().st_size/1024:.1f} KB)")
    print(f"⚙️  Метод: UnstructuredPdfExtractor (Unstructured API)")
    print(f"⚙️  UNSTRUCTURED_ENABLED_PDF=true")
    print()
    
    url = f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/document/create_by_file"
    headers = {'Authorization': f'Bearer {DIFY_API_KEY}'}
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        data = {'data': json.dumps({
            'indexing_technique': 'high_quality',
            'process_rule': {'mode': 'automatic'}
        })}
        
        print("📤 Начинаю загрузку...")
        start_time = time.time()
        
        try:
            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            elapsed = time.time() - start_time
            
            print(f"⏱️  Время загрузки: {elapsed:.2f} сек")
            print(f"📡 HTTP Status: {response.status_code}")
            print()
            
            if response.status_code in [200, 201]:
                result = response.json()
                doc_id = result.get('document', {}).get('id')
                batch_id = result.get('batch')
                
                print("✅ Загрузка успешна!")
                print(f"📝 Document ID: {doc_id}")
                print(f"📦 Batch ID: {batch_id}")
                print()
                print("="*61)
                print("Проверка логов:")
                print("="*61)
                print()
                print("Команда для проверки экстрактора:")
                print("docker compose -f docker/docker-compose.yaml logs worker --tail=50 | grep -E \"PDF extraction|Using extractor\"")
                print()
                print("Ожидается:")
                print("  - PDF extraction: UNSTRUCTURED_ENABLED_PDF=True")
                print("  - Using extractor: UnstructuredPdfExtractor")
                print()
                print("Команда для проверки Unstructured API:")
                print("docker logs alpaca-unstructured-api --tail=30 | grep POST")
                print()
                print("⏳ OCR обработка может занять 1-2 минуты для больших документов")
                print("   Проверьте результат в веб-интерфейсе Dify")
                print()
                print("="*61)
                
                return doc_id, batch_id
            else:
                print(f"❌ Ошибка загрузки: {response.status_code}")
                print(f"Ответ: {response.text}")
                return None, None
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
            return None, None

if __name__ == "__main__":
    file_path = r'C:\Users\Andrey\Downloads\test\test1 Соглашение погаш. задолжен. от 25.02.2025 АО QARMET — копия.pdf'
    upload_pdf(file_path)
