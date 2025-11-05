#!/usr/bin/env python3
"""
Тест сравнения обработки PDF с включенным и выключенным Unstructured API
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import time
import os
from pathlib import Path
from datetime import datetime

# Конфигурация
DIFY_API_URL = "http://localhost/v1"
DIFY_API_KEY = "dataset-MxZ3Hqnt0uGZMLJjF2CBgpbt"
DIFY_DATASET_ID = "d948bc40-afea-41eb-aa15-480882e7ba98"
TEST_FILE = r"C:\Users\Andrey\OneDrive\Документы\Агентские договора\ИП Дубенков\Л-Старт\220602_Агентский договор тест true.pdf"

# Настройка HTTP сессии с retry
def create_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

SESSION = create_session()

def upload_document(file_path: str, test_name: str):
    """Загрузка документа"""
    url = f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/document/create_by_file"
    
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}'
    }
    
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        print(f"❌ ERROR: File not found: {file_path}")
        return None
    
    # Добавляем тестовое имя к имени файла
    original_name = file_path_obj.stem
    extension = file_path_obj.suffix
    new_name = f"{original_name}_{test_name}{extension}"
    
    document_data = {
        'indexing_technique': 'high_quality',
        'process_rule': {
            'mode': 'custom',
            'rules': {
                'pre_processing_rules': [
                    {'id': 'remove_extra_spaces', 'enabled': False},
                    {'id': 'remove_urls_emails', 'enabled': False}
                ],
                'segmentation': {
                    'separator': '\\n\\n',
                    'max_tokens': 1024,
                    'chunk_overlap': 128
                }
            }
        }
    }
    
    with open(file_path, 'rb') as f:
        files = {
            'file': (new_name, f, 'application/pdf')
        }
        form_data = {'data': json.dumps(document_data)}
        
        print(f"📤 Uploading: {new_name}")
        print(f"   URL: {url}")
        
        start_time = time.time()
        response = SESSION.post(url, headers=headers, files=files, data=form_data)
        upload_time = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Upload time: {upload_time:.2f}s")
        
        if response.status_code in [200, 201]:
            result = response.json()
            document_id = result.get('document', {}).get('id')
            batch_id = result.get('batch')
            print(f"   ✅ SUCCESS! Document ID: {document_id}")
            print(f"   Batch ID: {batch_id}")
            return {
                'result': result,
                'upload_time': upload_time,
                'document_id': document_id,
                'test_name': test_name
            }
        else:
            print(f"   ❌ ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

def check_document(document_id: str, max_wait: int = 60):
    """Проверка статуса документа с ожиданием завершения"""
    url = f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/documents/{document_id}"
    
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}'
    }
    
    start_time = time.time()
    status = None
    
    print(f"⏳ Waiting for processing (max {max_wait}s)...")
    
    while time.time() - start_time < max_wait:
        try:
            response = SESSION.get(url, headers=headers, timeout=10)
        except Exception as e:
            print(f"   ⚠️ Request failed: {e}, retrying...")
            time.sleep(2)
            continue
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('indexing_status')
            
            if status == 'completed':
                processing_time = time.time() - start_time
                print(f"✅ Processing completed in {processing_time:.2f}s")
                print(f"   Name: {result.get('name')}")
                print(f"   Segments: {result.get('segment_count', 0)}")
                print(f"   Tokens: {result.get('tokens', 0)}")
                print(f"   Characters: {result.get('character_count', 0)}")
                return {
                    'status': 'completed',
                    'processing_time': processing_time,
                    'segments': result.get('segment_count', 0),
                    'tokens': result.get('tokens', 0),
                    'characters': result.get('character_count', 0),
                    'name': result.get('name')
                }
            elif status == 'error':
                print(f"❌ Processing failed")
                print(f"   Error: {result.get('error')}")
                return {
                    'status': 'error',
                    'error': result.get('error')
                }
            else:
                print(f"   Status: {status}...", end='\r')
                time.sleep(2)
        else:
            print(f"❌ ERROR checking status: {response.status_code}")
            return None
    
    print(f"\n⏰ Timeout after {max_wait}s")
    return {
        'status': 'timeout',
        'last_status': status
    }

def check_env_var(var_name: str):
    """Проверка переменной окружения в контейнере"""
    cmd = f'docker exec docker-api-1 sh -c "printenv {var_name}"'
    result = os.popen(cmd).read().strip()
    return result if result else "not_set"

def run_test(test_name: str, env_value: str):
    """Запуск одного теста"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"UNSTRUCTURED_ENABLED_PDF={env_value}")
    print(f"{'='*80}")
    
    # Загрузка документа
    upload_result = upload_document(TEST_FILE, test_name)
    
    if not upload_result:
        return None
    
    # Ожидание обработки
    check_result = check_document(upload_result['document_id'], max_wait=120)
    
    if check_result:
        return {
            'test_name': test_name,
            'env_value': env_value,
            'upload_time': upload_result['upload_time'],
            'processing_time': check_result.get('processing_time', 0),
            'total_time': upload_result['upload_time'] + check_result.get('processing_time', 0),
            'status': check_result['status'],
            'segments': check_result.get('segments', 0),
            'tokens': check_result.get('tokens', 0),
            'characters': check_result.get('characters', 0),
            'document_id': upload_result['document_id']
        }
    
    return None

def print_comparison(results: list):
    """Вывод сравнительной таблицы"""
    print(f"\n{'='*80}")
    print("COMPARISON RESULTS")
    print(f"{'='*80}\n")
    
    print(f"{'Metric':<30} {'WITH Unstructured':<20} {'WITHOUT Unstructured':<20}")
    print(f"{'-'*70}")
    
    if len(results) >= 2:
        with_unstr = results[0]
        without_unstr = results[1]
        
        metrics = [
            ('Upload Time', 'upload_time', 's'),
            ('Processing Time', 'processing_time', 's'),
            ('Total Time', 'total_time', 's'),
            ('Segments', 'segments', ''),
            ('Tokens', 'tokens', ''),
            ('Characters', 'characters', ''),
            ('Status', 'status', ''),
        ]
        
        for label, key, unit in metrics:
            val_with = with_unstr.get(key, 'N/A')
            val_without = without_unstr.get(key, 'N/A')
            
            if isinstance(val_with, (int, float)) and isinstance(val_without, (int, float)):
                val_with_str = f"{val_with:.2f}{unit}" if isinstance(val_with, float) else f"{val_with}{unit}"
                val_without_str = f"{val_without:.2f}{unit}" if isinstance(val_without, float) else f"{val_without}{unit}"
            else:
                val_with_str = str(val_with)
                val_without_str = str(val_without)
            
            print(f"{label:<30} {val_with_str:<20} {val_without_str:<20}")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    print(f"\n{'='*80}")
    print("PDF Processing Comparison Test")
    print(f"File: {Path(TEST_FILE).name}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    # Проверка текущего значения env var
    current_value = check_env_var('UNSTRUCTURED_ENABLED_PDF')
    print(f"\nℹ️  Current UNSTRUCTURED_ENABLED_PDF in container: {current_value}")
    
    results = []
    
    # Тест 1: С Unstructured API (если включено)
    if current_value.lower() in ('true', '1', 'yes', ''):
        print("\n⚠️  Note: Current setting suggests Unstructured is ENABLED")
        print("   First test will use Unstructured API")
        result1 = run_test("with_unstructured", "true")
        if result1:
            results.append(result1)
    
    # Просим пользователя изменить настройку
    print(f"\n{'='*80}")
    print("⚠️  ACTION REQUIRED:")
    print("1. Open docker/.env file")
    print("2. Change: UNSTRUCTURED_ENABLED_PDF=false")
    print("3. Run: docker compose restart api worker")
    print("4. Wait 10 seconds for restart")
    print(f"{'='*80}")
    
    input("\nPress ENTER when ready to continue with second test...")
    
    # Проверка нового значения
    new_value = check_env_var('UNSTRUCTURED_ENABLED_PDF')
    print(f"\nℹ️  New UNSTRUCTURED_ENABLED_PDF value: {new_value}")
    
    # Тест 2: Без Unstructured API
    result2 = run_test("without_unstructured", "false")
    if result2:
        results.append(result2)
    
    # Вывод сравнения
    if len(results) >= 2:
        print_comparison(results)
        
        # Сохранение результатов
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"test_results_{timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {result_file}")
    else:
        print("\n❌ Not enough test results for comparison")
    
    print(f"\n{'='*80}")
    print("Test completed!")
    print(f"{'='*80}\n")
