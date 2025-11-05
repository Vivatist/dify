#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
from pathlib import Path

file_path = r'C:\Users\Andrey\Downloads\test\test1 Соглашение погаш. задолжен. от 25.02.2025 АО QARMET — копия.pdf'
pdf_path = Path(file_path)

print(f'📤 TEST 1: Загрузка через Unstructured API')
print(f'Файл: {pdf_path.name}')
print(f'Размер: {pdf_path.stat().st_size} байт')

if pdf_path.exists():
    url = 'http://localhost/v1/datasets/d948bc40-afea-41eb-aa15-480882e7ba98/document/create_by_file'
    headers = {'Authorization': 'Bearer dataset-MxZ3Hqnt0uGZMLJjF2CBgpbt'}
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        data = {'data': json.dumps({'indexing_technique': 'high_quality', 'process_rule': {'mode': 'automatic'}})}
        
        response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        print(f'Status: {response.status_code}')
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f'✅ Успешно!')
            print(f"Document ID: {result.get('document', {}).get('id')}")
            print(f"Batch ID: {result.get('batch')}")
        else:
            print(f'❌ Error: {response.text}')
else:
    print(f'❌ File not found')
