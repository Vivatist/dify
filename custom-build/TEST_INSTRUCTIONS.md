# ИНСТРУКЦИЯ ПО ТЕСТИРОВАНИЮ PDF EXTRACTION

## Подготовка
Файл для тестирования: `C:\Users\Andrey\OneDrive\Документы\Агентские договора\ИП Дубенков\Л-Старт\220602_Агентский договор (1).pdf`

## ТЕСТ 1: С UNSTRUCTURED API (по умолчанию)

### Текущие настройки:
```bash
cd /c/Users/Andrey/dify/docker
grep "UNSTRUCTURED_ENABLED_PDF" .env
# Должно быть: UNSTRUCTURED_ENABLED_PDF=true
```

### Проверка переменной в контейнере:
```bash
docker compose exec api sh -c 'echo $UNSTRUCTURED_ENABLED_PDF'
# Должно вывести: true
```

### Запуск мониторинга:
Откройте отдельный терминал:
```bash
cd /c/Users/Andrey/dify/custom-build
./monitor_extraction.sh
```

### Тестирование:
1. Откройте Dify UI: http://localhost
2. Перейдите в Knowledge Base
3. Загрузите файл, переименовав его в: **test_with_unstructured.pdf**
4. Смотрите в терминал мониторинга

### Ожидаемый результат:
В логах должно появиться:
- `UnstructuredPdfExtractor` - зеленым цветом
- POST запрос к Unstructured API (если включен в логах)

---

## ТЕСТ 2: БЕЗ UNSTRUCTURED API

### Изменение настроек:
```bash
cd /c/Users/Andrey/dify/docker
# Откройте .env в редакторе
# Найдите строку 791: UNSTRUCTURED_ENABLED_PDF=true
# Измените на: UNSTRUCTURED_ENABLED_PDF=false
```

### Перезапуск контейнеров:
```bash
docker compose restart api worker
sleep 10  # Подождать загрузки
```

### Проверка:
```bash
docker compose exec api sh -c 'echo $UNSTRUCTURED_ENABLED_PDF'
# Должно вывести: false
```

### Тестирование:
1. Откройте Dify UI: http://localhost
2. Перейдите в Knowledge Base
3. Загрузите файл, переименовав его в: **test_without_unstructured.pdf**
4. Смотрите в терминал мониторинга

### Ожидаемый результат:
В логах должно появиться:
- `PdfExtractor` - желтым цветом (НЕ UnstructuredPdfExtractor)
- НЕТ POST запросов к Unstructured API

---

## БЫСТРАЯ ПРОВЕРКА ЛОГОВ

### Поиск использования Unstructured:
```bash
docker compose logs api worker --tail=100 | grep -i "unstructured.*pdf"
```

### Поиск использования встроенного парсера:
```bash
docker compose logs api worker --tail=100 | grep -E "PdfExtractor|pdf_extractor" | grep -v "Unstructured"
```

### Проверка всех экстракторов:
```bash
docker compose logs api worker --tail=200 | grep -i "extractor"
```

---

## ВОЗВРАТ К НАСТРОЙКАМ ПО УМОЛЧАНИЮ

```bash
cd /c/Users/Andrey/dify/docker
# Измените в .env:
# UNSTRUCTURED_ENABLED_PDF=true

docker compose restart api worker
```

---

## ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА

### Проверка что файл скопирован:
```bash
docker compose exec api ls -la /app/api/core/rag/extractor/extract_processor.py
docker compose exec api grep -n "is_unstructured_enabled" /app/api/core/rag/extractor/extract_processor.py | head -5
```

### Проверка импортов:
```bash
docker compose exec api grep -n "UnstructuredPdfExtractor" /app/api/core/rag/extractor/extract_processor.py
```

### Проверка синтаксиса в контейнере:
```bash
docker compose exec api python3 -m py_compile /app/api/core/rag/extractor/extract_processor.py
echo "Exit code: $?"
```

---

## TROUBLESHOOTING

### Если не переключается:
1. Проверьте что изменения в .env сохранены
2. Перезапустите контейнеры: `docker compose restart api worker`
3. Проверьте переменную окружения в контейнере
4. Очистите кэш браузера или используйте режим инкогнито

### Если ошибки при загрузке:
1. Проверьте логи: `docker compose logs api --tail=100`
2. Проверьте что Unstructured API доступен (если используется)
3. Проверьте размер файла (должен быть < 15MB)
