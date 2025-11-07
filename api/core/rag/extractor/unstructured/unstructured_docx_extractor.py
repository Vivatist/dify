import logging
import os
import tempfile
from pathlib import Path
from PIL import Image

from core.rag.extractor.extractor_base import BaseExtractor
from core.rag.models.document import Document

logger = logging.getLogger(__name__)

try:
    from docx import Document as DocxDocument
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False
    logger.warning("python-docx not available, image extraction from DOCX will be disabled")


class UnstructuredDocxExtractor(BaseExtractor):
    """Load DOCX files using Unstructured API with OCR support for embedded images.

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
        
        # Шаг 1: Извлечь основной текст через Unstructured API
        if self._api_url:
            from unstructured.partition.api import partition_via_api

            logger.debug(f"[DOCX] {filename}: Extracting text via Unstructured API")
            elements = partition_via_api(
                filename=self._file_path,
                api_url=self._api_url,
                api_key=self._api_key,
                languages=["rus", "eng"],
                ocr_languages=["rus", "eng"],
                strategy="hi_res"
            )
        else:
            from unstructured.partition.docx import partition_docx

            logger.debug(f"[DOCX] {filename}: Extracting text via local partition_docx")
            elements = partition_docx(
                filename=self._file_path,
                languages=["rus", "eng"],
                ocr_languages=["rus", "eng"]
            )
        
        logger.debug(f"[DOCX] {filename}: Got {len(elements)} text elements from Unstructured")
        
        # Собираем текст из элементов
        text_parts = []
        for element in elements:
            if hasattr(element, 'text') and element.text:
                text_parts.append(element.text)
        
        combined_text = "\n".join(text_parts)
        
        # Шаг 2: Извлечь и обработать изображения через OCR
        images_text = self._extract_and_ocr_images()
        
        if images_text:
            logger.debug(f"[DOCX] {filename}: Added OCR text from images: {len(images_text)} chars")
            combined_text += "\n\n" + images_text
        
        # Финальный лог успеха
        logger.info(f"[DOCX] {filename}: Successfully extracted {len(combined_text)} chars total")
        
        if not combined_text.strip():
            logger.error(f"[DOCX] {filename}: EMPTY RESULT from extraction!")
        
        return [Document(page_content=combined_text, metadata={"source": self._file_path})]
    
    def _extract_and_ocr_images(self) -> str:
        """Извлечь изображения из DOCX и обработать их через OCR"""
        filename = os.path.basename(self._file_path)
        
        if not PYTHON_DOCX_AVAILABLE:
            logger.warning(f"[DOCX] {filename}: python-docx not available, skipping image OCR")
            return ""
        
        try:
            doc = DocxDocument(self._file_path)
            temp_dir = tempfile.mkdtemp(prefix="dify_docx_images_")
            
            logger.debug(f"[DOCX] {filename}: Extracting images from document")
            
            images = []
            image_idx = 0
            
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    image_idx += 1
                    
                    try:
                        image_data = rel.target_part.blob
                        
                        if not image_data:
                            continue
                        
                        content_type = rel.target_part.content_type
                        ext = self._get_image_extension(content_type)
                        
                        logger.debug(f"[DOCX] {filename}: Image {image_idx}: content_type={content_type}, ext={ext}")
                        
                        image_path = os.path.join(temp_dir, f"image_{image_idx}{ext}")
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        
                        if os.path.exists(image_path):
                            images.append({
                                'index': image_idx,
                                'path': image_path,
                                'size': len(image_data),
                                'type': content_type,
                                'ext': ext
                            })
                            logger.debug(f"[DOCX] Extracted image {image_idx}: {len(image_data)} bytes")
                    
                    except Exception as e:
                        logger.error(f"[DOCX] {filename}: Failed to extract image {image_idx}: {e}")
            
            if not images:
                logger.debug(f"[DOCX] {filename}: No images found in document")
                return ""
            
            logger.debug(f"[DOCX] {filename}: Found {len(images)} images, processing with OCR")
            
            # Обработать изображения через OCR локально
            ocr_texts = []
            for img in images:
                try:
                    logger.debug(f"[DOCX] {filename}: OCR processing image {img['index']}: {img['path']}")
                    
                    # Конвертировать EMF/WMF в PNG если нужно
                    img_path = img['path']
                    if img['ext'].lower() in ['.emf', '.wmf']:
                        converted = self._convert_wmf_to_png(img_path, img['index'], temp_dir)
                        if converted:
                            img_path = converted
                            logger.debug(f"[DOCX] {filename}: Converted EMF/WMF to PNG: {img_path}")
                    
                    from unstructured.partition.image import partition_image
                    
                    elements = partition_image(
                        filename=img_path,
                        strategy="auto",
                        infer_table_structure=True,
                        languages=["rus", "eng"]
                    )
                    
                    if elements:
                        image_text = "\n\n".join([str(el) for el in elements if str(el).strip()])
                        if image_text.strip():
                            ocr_texts.append(image_text)
                            logger.debug(f"[DOCX] {filename}: OCR extracted {len(image_text)} chars from image {img['index']}")
                    
                except Exception as e:
                    logger.error(f"[DOCX] {filename}: OCR failed for image {img['index']}: {e}")
                
                finally:
                    try:
                        if os.path.exists(img['path']):
                            os.remove(img['path'])
                    except:
                        pass
            
            # Cleanup temp directory
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
            
            return "\n\n".join(ocr_texts)
        
        except Exception as e:
            logger.error(f"[DOCX] {filename}: Image extraction failed: {e}")
            return ""
    
    def _convert_wmf_to_png(self, wmf_path: str, image_idx: int, temp_dir: str) -> str | None:
        """
        Конвертация WMF/EMF в PNG для OCR
        """
        filename = os.path.basename(self._file_path)
        png_path = os.path.join(temp_dir, f"image_{image_idx}_converted.png")
        
        try:
            # Попытка 1: LibreOffice (лучше всего работает с EMF/WMF)
            import subprocess
            
            logger.debug(f"[DOCX] {filename}: Attempting LibreOffice conversion for image {image_idx}")
            result = subprocess.run(
                ['soffice', '--headless', '--convert-to', 'png', '--outdir', temp_dir, wmf_path],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            # soffice создаёт файл с оригинальным именем но расширением .png
            base_name = os.path.splitext(os.path.basename(wmf_path))[0]
            soffice_png = os.path.join(temp_dir, f"{base_name}.png")
            
            if result.returncode == 0 and os.path.exists(soffice_png):
                # Переименуем в ожидаемое имя
                if soffice_png != png_path:
                    os.rename(soffice_png, png_path)
                logger.debug(f"[DOCX] {filename}: LibreOffice conversion OK for image {image_idx}")
                return png_path
            else:
                logger.warning(f"[DOCX] {filename}: LibreOffice failed: returncode={result.returncode}, stderr={result.stderr}")
        except Exception as e:
            logger.warning(f"[DOCX] {filename}: LibreOffice exception: {e}")
        
        try:
            # Попытка 2: ImageMagick
            import subprocess
            
            logger.debug(f"[DOCX] {filename}: Attempting ImageMagick conversion for image {image_idx}")
            try:
                result = subprocess.run(
                    ['magick', wmf_path, png_path],
                    capture_output=True,
                    timeout=30,
                    text=True
                )
            except FileNotFoundError:
                result = subprocess.run(
                    ['convert', wmf_path, png_path],
                    capture_output=True,
                    timeout=30,
                    text=True
                )
            
            if result.returncode == 0 and os.path.exists(png_path):
                logger.debug(f"[DOCX] {filename}: ImageMagick conversion OK for image {image_idx}")
                return png_path
            else:
                logger.warning(f"[DOCX] {filename}: ImageMagick failed: returncode={result.returncode}, stderr={result.stderr}")
        except Exception as e:
            logger.warning(f"[DOCX] {filename}: ImageMagick exception: {e}")
        
        try:
            # Попытка 3: PIL напрямую (некоторые WMF - обычные растровые изображения)
            from PIL import Image
            img = Image.open(wmf_path)
            img.save(png_path, 'PNG')
            logger.debug(f"[DOCX] {filename}: PIL conversion OK for image {image_idx}")
            return png_path
        except Exception as e:
            logger.warning(f"[DOCX] {filename}: PIL conversion failed: {e}")
        
        return None
    
    def _get_image_extension(self, content_type: str) -> str:
        """Get file extension from MIME type"""
        extensions = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/tiff': '.tiff',
            'image/webp': '.webp',
            'image/x-wmf': '.wmf',
            'image/x-emf': '.emf'
        }
        return extensions.get(content_type, '.jpg')
