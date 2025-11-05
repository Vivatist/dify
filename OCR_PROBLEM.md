# Проблема с Unstructured API и OCR

## Обнаруженная проблема

**Дата**: 5 ноября 2025, 10:26

### Симптомы
- **test1** (через Unstructured): ✅ Загрузился нормально (первая загрузка)
- **test2** (через PdfExtractor): ❌ Файл пустой внутри

### Причина
PDF файлы являются **отсканированными документами** (изображения страниц, не текстовый слой).

### Детали

**Встроенный PdfExtractor (pypdfium2)**:
- ❌ **НЕ поддерживает OCR**
- Извлекает только текстовый слой PDF
- Для отсканированных PDF возвращает пустой результат

**UnstructuredPdfExtractor через API**:
- ✅ **Поддерживает OCR** автоматически
- Может извлекать текст из изображений
- ❌ **Но требует минимум 2048 MB свободной RAM**

### Текущее состояние Unstructured API

```
$ docker logs alpaca-unstructured-api --tail=5
2025-11-05 10:27:53,997 unstructured_api WARNING Rejecting because free memory is below 2048 MB
2025-11-05 10:27:53,997 unstructured_api ERROR Server is under heavy load. Please try again later.
```

**Статус**: `unhealthy` - недостаточно памяти для обработки OCR

### HTTP ответы
```
POST /general/v0/general - 503 Service Unavailable
```

---

## Решения

### ✅ Решение 1: Увеличить память Docker Desktop

1. Откройте Docker Desktop
2. Settings → Resources → Memory
3. Увеличьте до **8 GB** или больше (сейчас, вероятно, 4 GB)
4. Apply & Restart
5. Перезапустите Unstructured API:
   ```bash
   docker restart alpaca-unstructured-api
   ```

### ✅ Решение 2: Уменьшить требования к памяти

Если не можете выделить больше RAM, уменьшите порог в Unstructured API:

```bash
# Найдите переменную окружения UNSTRUCTURED_MEMORY_FREE_MINIMUM_MB
# Уменьшите с 2048 до 1024 или 512 (но качество OCR может пострадать)
docker stop alpaca-unstructured-api
docker run ... -e UNSTRUCTURED_MEMORY_FREE_MINIMUM_MB=1024 ...
```

### ✅ Решение 3: Использовать внешний Unstructured API

Вместо локального контейнера используйте облачный сервис:
- Unstructured.io API (платно)
- Установить на более мощном сервере

### ⚠️ Решение 4: Предварительная обработка PDF

Конвертируйте отсканированные PDF в текстовые перед загрузкой:
- Используйте Adobe Acrobat OCR
- Tesseract OCR локально
- Online OCR сервисы

---

## Рекомендация

**Для production с отсканированными документами**:

```env
# В docker/.env
UNSTRUCTURED_ENABLED_PDF=true
UNSTRUCTURED_ENABLED_DOCX=true
UNSTRUCTURED_ENABLED_DOC=true
```

И выделите Docker минимум **8 GB RAM**.

---

## Тестирование

### Успешный тест (test1, первая загрузка)
- Document ID: `56dcb45f-9670-4225-8868-36953d8a33d4`
- Метод: `UnstructuredPdfExtractor`
- Результат: ✅ Текст извлечен (OCR сработал)

### Неудачный тест (test2, через PdfExtractor)
- Document ID: `b98bb077-b37e-47ed-bfcf-acc7b1172a6c` (удален)
- Метод: `PdfExtractor` (pypdfium2)
- Результат: ❌ Пустой файл (нет текстового слоя)

### Повторный тест (test2, через Unstructured)
- Document ID: `b2d3fbd3-64b8-4eac-8d6b-5cc2e56bd85f`
- Метод: `UnstructuredPdfExtractor`
- Результат: ❌ Не обработан - 503 от Unstructured API (недостаточно памяти)

---

## Выводы

1. **Для отсканированных PDF обязательно нужен OCR** → Unstructured API
2. **Unstructured API требует достаточно RAM** → минимум 2 GB свободной, рекомендуется 4-8 GB
3. **Встроенный PdfExtractor не подходит для изображений** → только для текстовых PDF

### Немедленные действия

1. Увеличить память Docker до 8 GB
2. Перезапустить Unstructured API
3. Перезагрузить test2 через Unstructured
4. Убедиться что текст извлекся корректно
