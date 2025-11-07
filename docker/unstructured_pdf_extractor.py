import logging
import os

from core.rag.extractor.extractor_base import BaseExtractor
from core.rag.models.document import Document

logger = logging.getLogger(__name__)


class UnstructuredPdfExtractor(BaseExtractor):
    """Load PDF files using Unstructured API.

    Args:
        file_path: Path to the file to load.
        api_url: Unstructured API URL.
        api_key: Unstructured API key (optional).
    """

    def __init__(self, file_path: str, api_url: str | None = None, api_key: str = ""):
        """Initialize with file path."""
        self._file_path = file_path
        self._api_url = api_url
        self._api_key = api_key

    def extract(self) -> list[Document]:
        filename = os.path.basename(self._file_path)
        
        if self._api_url:
            from unstructured.partition.api import partition_via_api

            elements = partition_via_api(
                filename=self._file_path,
                api_url=self._api_url,
                api_key=self._api_key,
                languages=["rus", "eng"],
                ocr_languages=["rus", "eng"]
            )
        else:
            from unstructured.partition.pdf import partition_pdf

            elements = partition_pdf(
                filename=self._file_path,
                languages=["rus", "eng"],
                ocr_languages=["rus", "eng"]
            )
        
        text_by_page: dict[int, str] = {}
        for element in elements:
            page = element.metadata.page_number
            text = element.text
            if page is not None:
                if page in text_by_page:
                    text_by_page[page] += "\n" + text
                else:
                    text_by_page[page] = text

        combined_texts = list(text_by_page.values())
        documents = []
        total_chars = 0
        for combined_text in combined_texts:
            text = combined_text.strip()
            total_chars += len(text)
            documents.append(Document(page_content=text))
        
        logger.info(f"[PDF] {filename}: Successfully extracted {total_chars} chars from {len(documents)} pages")
        
        return documents
