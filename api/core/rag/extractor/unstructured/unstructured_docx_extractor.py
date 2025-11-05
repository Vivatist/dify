import logging

from core.rag.extractor.extractor_base import BaseExtractor
from core.rag.models.document import Document

logger = logging.getLogger(__name__)


class UnstructuredDocxExtractor(BaseExtractor):
    """Load DOCX files using Unstructured API.

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
        if self._api_url:
            from unstructured.partition.api import partition_via_api

            elements = partition_via_api(
                filename=self._file_path,
                api_url=self._api_url,
                api_key=self._api_key,
                languages=["rus", "eng"]
            )
        else:
            from unstructured.partition.docx import partition_docx

            elements = partition_docx(filename=self._file_path, languages=["rus", "eng"])
        
        # Combine all text into a single document
        text_parts = []
        for element in elements:
            if hasattr(element, 'text') and element.text:
                text_parts.append(element.text)
        
        combined_text = "\n".join(text_parts)
        
        return [Document(page_content=combined_text, metadata={"source": self._file_path})]
