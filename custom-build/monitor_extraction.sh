#!/bin/bash
# Monitor Docker logs for extractor usage

echo "======================================================================"
echo "PDF EXTRACTION MONITORING"
echo "======================================================================"
echo ""
echo "Instructions:"
echo "1. Keep this terminal open"
echo "2. Open Dify UI in browser (http://localhost)"
echo "3. Go to Knowledge Base"
echo "4. Upload PDF file: 220602_Агentский договор (1).pdf"
echo "5. Watch this terminal for extractor being used"
echo ""
echo "======================================================================"
echo "Current UNSTRUCTURED_ENABLED_PDF setting:"
docker compose exec -T api sh -c 'echo $UNSTRUCTURED_ENABLED_PDF' 2>/dev/null || echo "Unable to check (container not running)"
echo ""
echo "======================================================================"
echo "Monitoring logs (Ctrl+C to stop)..."
echo "======================================================================"
echo ""

# Follow logs and highlight extractor usage
docker compose logs -f api worker 2>&1 | grep --line-buffered -i "extractor\|extract_processor" | while read line; do
    if echo "$line" | grep -qi "UnstructuredPdf"; then
        echo -e "\033[1;32m[UNSTRUCTURED PDF] $line\033[0m"
    elif echo "$line" | grep -qi "PdfExtractor"; then
        echo -e "\033[1;33m[BUILT-IN PDF] $line\033[0m"
    elif echo "$line" | grep -qi "UnstructuredDocx"; then
        echo -e "\033[1;36m[UNSTRUCTURED DOCX] $line\033[0m"
    elif echo "$line" | grep -qi "WordExtractor"; then
        echo -e "\033[1;35m[BUILT-IN DOCX] $line\033[0m"
    else
        echo "$line"
    fi
done
