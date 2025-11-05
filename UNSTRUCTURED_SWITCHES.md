# Инструкция по использованию переключателей Unstructured API

## Описание

Реализована система переключателей для управления использованием Unstructured API для различных типов файлов через переменные окружения. Это позволяет гибко выбирать, какие файлы обрабатывать через внешний Unstructured API, а какие - встроенными парсерами Dify.

## Поддерживаемые типы файлов

| Расширение | Переменная окружения | Unstructured API | Встроенный парсер |
|------------|---------------------|------------------|-------------------|
| `.pdf` | `UNSTRUCTURED_ENABLED_PDF` | UnstructuredPdfExtractor | PdfExtractor |
| `.docx` | `UNSTRUCTURED_ENABLED_DOCX` | UnstructuredDocxExtractor | WordExtractor |
| `.doc` | `UNSTRUCTURED_ENABLED_DOC` | UnstructuredWordExtractor | TextExtractor |
| `.pptx` | `UNSTRUCTURED_ENABLED_PPTX` | UnstructuredPPTXExtractor | TextExtractor |
| `.ppt` | `UNSTRUCTURED_ENABLED_PPT` | UnstructuredPPTExtractor | TextExtractor |

## Как использовать

### 1. Настройка переменных окружения

Отредактируйте файл `docker/.env` и добавьте/измените нужные переменные:

```bash
# Включить Unstructured API для PDF
UNSTRUCTURED_ENABLED_PDF=true

# Выключить Unstructured API для DOCX (использовать встроенный парсер)
UNSTRUCTURED_ENABLED_DOCX=false

# Включить для PowerPoint
UNSTRUCTURED_ENABLED_PPTX=true
UNSTRUCTURED_ENABLED_PPT=true
```

### 2. Применение изменений

После изменения `.env` файла перезапустите контейнеры:

```bash
cd docker
docker compose restart api worker
```

### 3. Проверка настроек

Запустите тестовый скрипт для проверки текущих настроек:

```bash
python custom-build/test_switch.py
```

## Допустимые значения

Переменные распознают следующие значения (регистр не важен):

**Включено (true):**
- `true`
- `1`
- `yes`

**Выключено (false):**
- `false`
- `0`
- `no`
- любое другое значение

**По умолчанию:** `true` (если переменная не задана)

## Примеры использования

### Пример 1: Использовать Unstructured только для PDF

```bash
UNSTRUCTURED_ENABLED_PDF=true
UNSTRUCTURED_ENABLED_DOCX=false
UNSTRUCTURED_ENABLED_DOC=false
UNSTRUCTURED_ENABLED_PPTX=false
UNSTRUCTURED_ENABLED_PPT=false
```

### Пример 2: Использовать встроенные парсеры для всех типов

```bash
UNSTRUCTURED_ENABLED_PDF=false
UNSTRUCTURED_ENABLED_DOCX=false
UNSTRUCTURED_ENABLED_DOC=false
UNSTRUCTURED_ENABLED_PPTX=false
UNSTRUCTURED_ENABLED_PPT=false
```

### Пример 3: Использовать Unstructured для всех типов (по умолчанию)

```bash
UNSTRUCTURED_ENABLED_PDF=true
UNSTRUCTURED_ENABLED_DOCX=true
UNSTRUCTURED_ENABLED_DOC=true
UNSTRUCTURED_ENABLED_PPTX=true
UNSTRUCTURED_ENABLED_PPT=true
```

## Когда использовать встроенные парсеры

Используйте встроенные парсеры (установите `=false`), если:

1. **Unstructured API недоступен** - нет подключения или сервис перегружен
2. **Проблемы с памятью** - Unstructured требует много оперативной памяти
3. **Простые документы** - для документов без сложного форматирования встроенные парсеры могут быть быстрее
4. **Тестирование** - сравнение качества извлечения текста разными методами

## Когда использовать Unstructured API

Используйте Unstructured API (установите `=true`), если:

1. **Сложное форматирование** - документы с таблицами, изображениями, сложной структурой
2. **Высокое качество** - нужно максимально точное извлечение текста
3. **Специфические форматы** - документы с нестандартной структурой

## Технические детали

### Расположение кода

- **Файл обработки:** `api/core/rag/extractor/extract_processor.py`
- **Функция проверки:** `is_unstructured_enabled(file_ext: str) -> bool`
- **Строка логики:** 108-190 в `extract_processor.py`

### Логика работы

```python
def is_unstructured_enabled(file_ext: str) -> bool:
    """Check if Unstructured API should be used for this file type"""
    env_var = f"UNSTRUCTURED_ENABLED_{file_ext.upper().lstrip('.')}"
    value = os.getenv(env_var, "true").lower()
    return value in ("true", "1", "yes")
```

Для каждого типа файла код проверяет соответствующую переменную и выбирает экстрактор:

```python
elif file_extension == ".pdf":
    extractor = (
        UnstructuredPdfExtractor(file_path, unstructured_api_url, unstructured_api_key)
        if is_unstructured_enabled(".pdf")
        else PdfExtractor(file_path)
    )
```

## Troubleshooting

### Проблема: Unstructured возвращает 503 Service Unavailable

**Решение:** Установите переключатель в `false` для временного использования встроенного парсера:

```bash
UNSTRUCTURED_ENABLED_PDF=false
docker compose restart api worker
```

### Проблема: Низкое качество извлечения текста

**Решение:** Попробуйте переключиться на Unstructured API:

```bash
UNSTRUCTURED_ENABLED_PDF=true
docker compose restart api worker
```

### Проблема: Переменная не применяется

**Проверьте:**
1. Переменная добавлена в `docker/.env`
2. Контейнеры перезапущены после изменения
3. Переменная присутствует в контейнере: `docker exec docker-api-1 printenv | grep UNSTRUCTURED_ENABLED`

## Мониторинг

Проверить, какой экстрактор используется, можно в логах worker:

```bash
docker compose logs worker --tail=100 | grep -i "pdf\|extractor"
```

При включенном логировании (в коде есть `logger.info`) вы увидите:
```
PDF extraction: UNSTRUCTURED_ENABLED_PDF=True
Using extractor: UnstructuredPdfExtractor
```

или

```
PDF extraction: UNSTRUCTURED_ENABLED_PDF=False
Using extractor: PdfExtractor
```

## Дополнительная информация

- **Unstructured API документация:** http://localhost:8000/general/docs
- **Требование к памяти Unstructured:** минимум 2048 MB свободной памяти
- **ETL_TYPE:** Должен быть установлен в `Unstructured` для работы переключателей
