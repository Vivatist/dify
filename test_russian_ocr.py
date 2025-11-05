#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Повторный тест с поддержкой русского языка в OCR
"""
import requests
import json
from pathlib import Path
import time

# Конфигурация
DIFY_API_URL = "http://localhost/v1"
DIFY_API_KEY = "dataset-MxZ3Hqnt0uGZMLJjF2CBgpbt"
DIFY_DATASET_ID = "d948bc40-afea-41eb-aa15-480882e7ba98"

# ID старого документа для удаления
OLD_DOC_ID = "56dcb45f-9670-4225-8868-36953d8a33d4"

print("="*61)
print("ТЕСТ: Unstructured API с русским языком OCR")
print("="*61)
print()

# Удаляем старый документ
print(f"🗑️  Удаление старого документа {OLD_DOC_ID}...")
delete_url = f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/documents/{OLD_DOC_ID}"
headers = {'Authorization': f'Bearer {DIFY_API_KEY}'}

try:
    response = requests.delete(delete_url, headers=headers, timeout=10)
    if response.status_code in [200, 204]:
        print("   ✅ Документ удален")
    else:
        print(f"   ⚠️  Статус: {response.status_code}")
except Exception as e:
    print(f"   ⚠️  Ошибка: {e}")

print()

# Загружаем заново с русским языком
file_path = r'C:\Users\Andrey\Downloads\test\test1 Соглашение погаш. задолжен. от 25.02.2025 АО QARMET — копия.pdf'
pdf_path = Path(file_path)

if not pdf_path.exists():
    print(f"❌ Файл не найден")
    exit(1)

print("📤 Загрузка test1 с поддержкой русского языка...")
print(f"   Файл: {pdf_path.name}")
print(f"   Размер: {pdf_path.stat().st_size:,} байт")
print(f"   Языки OCR: rus + eng")
print()

url = f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/document/create_by_file"

with open(pdf_path, 'rb') as f:
    files = {'file': (pdf_path.name, f, 'application/pdf')}
    data = {'data': json.dumps({
        'indexing_technique': 'high_quality',
        'process_rule': {'mode': 'automatic'}
    })}
    
    start_time = time.time()
    response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    elapsed = time.time() - start_time
    
    print(f"⏱️  Время: {elapsed:.2f} сек")
    print(f"📡 Status: {response.status_code}")
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
        print("docker compose -f docker/docker-compose.yaml logs worker --tail=30 | grep 'Using extractor'")
        print()
        print("⏳ Подождите 1-2 минуты для OCR обработки")
        print("   Затем проверьте текст в веб-интерфейсе - должна быть кириллица!")
        print()
        print("="*61)
    else:
        print(f"❌ Ошибка: {response.text}")
