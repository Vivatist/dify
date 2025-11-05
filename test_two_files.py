#!/usr/bin/env python3
"""
Тест загрузки двух PDF файлов:
1. test1 - через Unstructured API (UNSTRUCTURED_ENABLED_PDF=true)
2. test2 - через обычный парсер (UNSTRUCTURED_ENABLED_PDF=false)
"""
import requests
import json
import time
from pathlib import Path
import sys

# Конфигурация
DIFY_API_URL = "http://localhost/v1"
DIFY_API_KEY = "dataset-MxZ3Hqnt0uGZMLJjF2CBgpbt"
DIFY_DATASET_ID = "d948bc40-afea-41eb-aa15-480882e7ba98"

def upload_pdf_file(file_path: str, test_name: str):
    """Загрузка PDF файла в Dify"""
    
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        print(f"   ❌ Файл не найден: {file_path}")
        return None, None
    
    url = f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/document/create_by_file"
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}'
    }
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    files = {'file': (pdf_path.name, pdf_content, 'application/pdf')}
    
    document_data = {
        'indexing_technique': 'high_quality',
        'process_rule': {
            'mode': 'automatic'
        }
    }
    form_data = {'data': json.dumps(document_data)}
    
    print(f"\n📤 {test_name}")
    print(f"   Файл: {pdf_path.name}")
    print(f"   Размер: {len(pdf_content)} байт")
    
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
            return document_id, batch_id
        else:
            print(f"   ❌ Ошибка: {response.text}")
            return None, None
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return None, None

if __name__ == "__main__":
    print("="*80)
    print("Тест двух методов обработки PDF")
    print("="*80)
    
    # Пути к файлам
    test1_path = r"C:\Users\Andrey\Downloads\test\test1 Соглашение погаш. задолжен. от 25.02.2025 АО QARMET — копия.pdf"
    test2_path = r"C:\Users\Andrey\Downloads\test\test2 Соглашение погаш. задолжен. от 25.02.2025 АО QARMET.pdf"
    
    # Тест 1: Unstructured API (должен быть включен)
    print("\n" + "="*80)
    print("ТЕСТ 1: Через Unstructured API")
    print("Убедитесь что UNSTRUCTURED_ENABLED_PDF=true в .env")
    print("="*80)
    
    input("Нажмите Enter для загрузки test1 через Unstructured API...")
    doc1_id, batch1_id = upload_pdf_file(test1_path, "TEST 1 - Unstructured API")
    
    if doc1_id:
        print("\n📋 Команда для проверки логов TEST 1:")
        print(f"   docker compose -f docker/docker-compose.yaml logs worker --tail=100 | grep -E 'PDF extraction|Using extractor' | tail -20")
        print("   Ожидается: 'Using extractor: UnstructuredPdfExtractor'")
    
    # Пауза для переключения настройки
    print("\n" + "="*80)
    print("ТЕСТ 2: Через обычный парсер")
    print("="*80)
    print("\n⚠️  Сейчас нужно изменить настройку:")
    print("   1. Откройте файл: docker/.env")
    print("   2. Найдите: UNSTRUCTURED_ENABLED_PDF=true")
    print("   3. Измените на: UNSTRUCTURED_ENABLED_PDF=false")
    print("   4. Перезапустите worker: docker compose -f docker/docker-compose.yaml restart worker")
    print()
    
    input("Нажмите Enter когда worker перезапустится и будет готов к тесту 2...")
    
    # Тест 2: Обычный парсер (должен быть выключен)
    doc2_id, batch2_id = upload_pdf_file(test2_path, "TEST 2 - Обычный парсер")
    
    if doc2_id:
        print("\n📋 Команда для проверки логов TEST 2:")
        print(f"   docker compose -f docker/docker-compose.yaml logs worker --tail=100 | grep -E 'PDF extraction|Using extractor' | tail -20")
        print("   Ожидается: 'Using extractor: PdfExtractor'")
    
    # Итоги
    print("\n" + "="*80)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*80)
    
    if doc1_id and doc2_id:
        print("✅ Оба файла успешно загружены!")
        print(f"\nTEST 1 (Unstructured): Document ID = {doc1_id}")
        print(f"TEST 2 (Обычный):      Document ID = {doc2_id}")
        print("\n📋 Проверьте различия в обработке в логах worker")
    elif doc1_id:
        print("⚠️  TEST 1 успешен, TEST 2 не удался")
    elif doc2_id:
        print("⚠️  TEST 2 успешен, TEST 1 не удался")
    else:
        print("❌ Оба теста не удались")
    
    print("="*80)
