#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Повторная загрузка test2 через Unstructured API с OCR
"""
import requests
import json
from pathlib import Path

# Конфигурация
DIFY_API_URL = "http://localhost/v1"
DIFY_API_KEY = "dataset-MxZ3Hqnt0uGZMLJjF2CBgpbt"
DIFY_DATASET_ID = "d948bc40-afea-41eb-aa15-480882e7ba98"

# Сначала удалим старый документ test2
OLD_DOC_ID = "b98bb077-b37e-47ed-bfcf-acc7b1172a6c"

print("="*80)
print("Повторная загрузка test2 через Unstructured API (с OCR)")
print("="*80)

# Шаг 1: Удаление старого документа
print(f"\n🗑️  Удаление старого документа {OLD_DOC_ID}...")
delete_url = f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/documents/{OLD_DOC_ID}"
headers = {'Authorization': f'Bearer {DIFY_API_KEY}'}

try:
    response = requests.delete(delete_url, headers=headers, timeout=10)
    if response.status_code in [200, 204]:
        print(f"   ✅ Документ удален")
    else:
        print(f"   ⚠️  Статус удаления: {response.status_code}")
except Exception as e:
    print(f"   ⚠️  Ошибка удаления: {e}")

# Шаг 2: Загрузка нового документа
print(f"\n📤 Загрузка test2 заново через Unstructured API с OCR...")

file_path = r'C:\Users\Andrey\Downloads\test\test2 Соглашение погаш. задолжен. от 25.02.2025 АО QARMET.pdf'
pdf_path = Path(file_path)

if not pdf_path.exists():
    print(f"❌ Файл не найден: {file_path}")
    exit(1)

print(f"   Файл: {pdf_path.name}")
print(f"   Размер: {pdf_path.stat().st_size} байт")

url = f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/document/create_by_file"

with open(pdf_path, 'rb') as f:
    files = {'file': (pdf_path.name, f, 'application/pdf')}
    data = {'data': json.dumps({
        'indexing_technique': 'high_quality',
        'process_rule': {'mode': 'automatic'}
    })}
    
    response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    print(f"   Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"   ✅ Успешно загружен через Unstructured с OCR!")
        print(f"   Document ID: {result.get('document', {}).get('id')}")
        print(f"   Batch ID: {result.get('batch')}")
    else:
        print(f"   ❌ Error: {response.text}")

print("\n" + "="*80)
print("Проверьте логи:")
print("docker compose -f docker/docker-compose.yaml logs worker --tail=50 | grep 'Using extractor'")
print("="*80)
