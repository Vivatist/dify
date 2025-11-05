# Unstructured API Feature Toggles

## Overview
This implementation adds granular control over Unstructured API usage for different file types in Dify.

## What Was Done

### 1. Modified Files
- **`api/core/rag/extractor/extract_processor.py`**
  - Added imports for `UnstructuredDocxExtractor` and `UnstructuredPdfExtractor`
  - Added helper function `is_unstructured_enabled(file_ext: str)`
  - Modified all file handlers in the `if etl_type == "Unstructured"` block

### 2. Added Environment Variables
In `docker/.env`:
```bash
UNSTRUCTURED_ENABLED_DOCX=true
UNSTRUCTURED_ENABLED_PDF=true
UNSTRUCTURED_ENABLED_DOC=true
UNSTRUCTURED_ENABLED_PPT=true
UNSTRUCTURED_ENABLED_PPTX=true
UNSTRUCTURED_ENABLED_XML=true
UNSTRUCTURED_ENABLED_EPUB=true
UNSTRUCTURED_ENABLED_MSG=true
UNSTRUCTURED_ENABLED_EML=true
UNSTRUCTURED_ENABLED_MARKDOWN=true
```

## How It Works

### Helper Function
```python
def is_unstructured_enabled(file_ext: str) -> bool:
    """Check if Unstructured API should be used for this file type"""
    env_var = f"UNSTRUCTURED_ENABLED_{file_ext.upper().lstrip('.')}"
    value = os.getenv(env_var, "true").lower()
    return value in ("true", "1", "yes")
```

### Example for PDF
```python
elif file_extension == ".pdf":
    extractor = (
        UnstructuredPdfExtractor(file_path, unstructured_api_url, unstructured_api_key)
        if is_unstructured_enabled(".pdf")
        else PdfExtractor(file_path)
    )
```

## Usage

### Disable Unstructured for DOCX Files
1. Edit `docker/.env`:
   ```bash
   UNSTRUCTURED_ENABLED_DOCX=false
   ```

2. Restart containers:
   ```bash
   cd docker
   docker compose restart api worker
   ```

### Check Logs
To verify which extractor is being used:
```bash
docker compose logs api | grep -i extractor
```

## Testing

### Test Script
Run `custom-build/test_switch.py` to verify the logic:
```bash
cd custom-build
python test_switch.py
```

### Manual Testing
1. Set `UNSTRUCTURED_ENABLED_DOCX=false` in `.env`
2. Upload a DOCX file to Dify
3. Check logs - should NOT see POST requests to Unstructured API
4. File should be processed with built-in WordExtractor

## Fallback Extractors

When Unstructured is disabled, the system uses:

| File Type | Fallback Extractor |
|-----------|-------------------|
| .pdf | PdfExtractor (pypdfium2) |
| .docx | WordExtractor (python-docx) |
| .doc | TextExtractor |
| .ppt | TextExtractor |
| .pptx | TextExtractor |
| .xml | TextExtractor |
| .epub | UnstructuredEpubExtractor (without API) |
| .msg | TextExtractor |
| .eml | TextExtractor |
| .md | MarkdownExtractor |

## Configuration Options

Each variable accepts:
- **Enable:** `true`, `1`, `yes`
- **Disable:** `false`, `0`, `no`
- **Default:** `true` (if not set)

## Rebuilding Images

After modifying `extract_processor.py`:
```bash
cd docker
docker compose build api worker
docker compose up -d api worker
```

## Backup

Original file backed up at:
```
api/core/rag/extractor/extract_processor.py.backup
```

## Troubleshooting

### SyntaxError
If you see SyntaxError after modifications:
1. Restore from backup:
   ```bash
   cp api/core/rag/extractor/extract_processor.py.backup \
      api/core/rag/extractor/extract_processor.py
   ```
2. Rebuild images
3. Check syntax:
   ```bash
   python3 -m py_compile api/core/rag/extractor/extract_processor.py
   ```

### Extractor Not Switching
1. Verify environment variable in container:
   ```bash
   docker exec docker-api-1 env | grep UNSTRUCTURED_ENABLED
   ```
2. Ensure you restarted containers after .env changes
3. Check logs for extractor usage

## Notes

- Changes only affect the Unstructured block (`if etl_type == "Unstructured"`)
- The `else` block (non-Unstructured mode) remains unchanged
- All changes are backward compatible (default = enabled)
- XMLSyntaxError issues with corrupted DOCX files can be worked around by disabling Unstructured for DOCX
