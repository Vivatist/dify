# Результаты тестирования переключателей Unstructured API

Дата: 5 ноября 2025 г., 10:18-10:20

## Тестовые файлы

1. **test1**: `test1 Соглашение погаш. задолжен. от 25.02.2025 АО QARMET — копия.pdf`
2. **test2**: `test2 Соглашение погаш. задолжен. от 25.02.2025 АО QARMET.pdf`

Оба файла идентичны по содержанию (967270 байт).

## TEST 1: Через Unstructured API

**Конфигурация:**
- `UNSTRUCTURED_ENABLED_PDF=true`
- Worker перезапущен через `docker compose up -d worker`

**Результат:**
- ✅ Успешно загружен
- Document ID: `56dcb45f-9670-4225-8868-36953d8a33d4`
- Batch ID: `20251105101849387452`
- Время: 10:18:49

**Логи обработки:**
```
worker-1 | 2025-11-05 10:18:49.276 INFO - PDF extraction: UNSTRUCTURED_ENABLED_PDF=True
worker-1 | 2025-11-05 10:18:49.277 INFO - Using extractor: UnstructuredPdfExtractor
```

✅ **Подтверждено: файл обработан через Unstructured API**

---

## TEST 2: Через обычный парсер

**Конфигурация:**
- `UNSTRUCTURED_ENABLED_PDF=false`
- Worker перезапущен через `docker compose up -d worker`

**Результат:**
- ✅ Успешно загружен
- Document ID: `b98bb077-b37e-47ed-bfcf-acc7b1172a6c`
- Batch ID: `20251105101934321398`
- Время: 10:19:35

**Логи обработки:**
```
worker-1 | 2025-11-05 10:19:35.212 INFO - PDF extraction: UNSTRUCTURED_ENABLED_PDF=False
worker-1 | 2025-11-05 10:19:35.212 INFO - Using extractor: PdfExtractor
worker-1 | 2025-11-05 10:19:35.216 WARNING - pypdfium2 warning (встроенный парсер)
```

✅ **Подтверждено: файл обработан через встроенный PdfExtractor (pypdfium2)**

---

## Выводы

### ✅ Переключатели работают корректно

1. **При `UNSTRUCTURED_ENABLED_PDF=true`**:
   - Используется `UnstructuredPdfExtractor`
   - Файлы отправляются в Unstructured API
   - Нет предупреждений pypdfium2

2. **При `UNSTRUCTURED_ENABLED_PDF=false`**:
   - Используется встроенный `PdfExtractor`
   - Библиотека pypdfium2 обрабатывает файлы локально
   - Появляются стандартные предупреждения pypdfium2

### Важно: Изменение переменных окружения

После изменения `.env` файла необходимо **пересоздать контейнер**:

```bash
cd docker
docker compose up -d worker  # НЕ restart, а именно up -d
```

Команда `restart` не перечитывает переменные окружения из `.env`!

### Доступные переключатели

В `docker/.env`:
```bash
UNSTRUCTURED_ENABLED_PDF=true    # PDF через Unstructured
UNSTRUCTURED_ENABLED_DOCX=true   # DOCX через Unstructured
UNSTRUCTURED_ENABLED_DOC=true    # DOC через Unstructured
UNSTRUCTURED_ENABLED_PPTX=true   # PPTX через Unstructured
UNSTRUCTURED_ENABLED_PPT=true    # PPT через Unstructured
```

## Практическое применение

### Сценарий 1: Все файлы через Unstructured
```bash
# В docker/.env установить все в true
UNSTRUCTURED_ENABLED_PDF=true
UNSTRUCTURED_ENABLED_DOCX=true
# ... остальные

# Применить
cd docker && docker compose up -d worker
```

### Сценарий 2: Только PDF через Unstructured, остальное локально
```bash
UNSTRUCTURED_ENABLED_PDF=true
UNSTRUCTURED_ENABLED_DOCX=false
UNSTRUCTURED_ENABLED_DOC=false
# ...

cd docker && docker compose up -d worker
```

### Сценарий 3: Все локально (без Unstructured)
```bash
# Все в false
UNSTRUCTURED_ENABLED_PDF=false
UNSTRUCTURED_ENABLED_DOCX=false
# ...

cd docker && docker compose up -d worker
```

## Мониторинг

Проверка какой экстрактор используется:
```bash
cd docker
docker compose logs worker --tail=100 | grep -E "PDF extraction|Using extractor"
```

Ожидаемый вывод:
- `Using extractor: UnstructuredPdfExtractor` — через API
- `Using extractor: PdfExtractor` — локально
