"""Native PDF extractor for procurement solicitation packets and addenda."""

import re
from pathlib import Path
from typing import Dict, List, Optional
import pypdf


class PdfExtractionError(Exception):
    """Raised when PDF file is invalid, corrupt, or unreadable."""
    pass


class PdfExtractor:
    """Extracts, cleans, and structures text from government solicitation PDFs."""

    PAGE_HEADER_FOOTER_PATTERN = re.compile(
        r"(?:(?:Page\s+[0-9]+(?:\s+of\s+[0-9]+)?)|(?:[0-9]+\s+of\s+[0-9]+))\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    def extract_text_from_file(self, file_path: str) -> str:
        """Extracts and cleans all text content across all pages of a PDF file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found at '{file_path}'")
        if not path.is_file():
            raise PdfExtractionError(f"Target path '{file_path}' is not a regular file")

        try:
            reader = pypdf.PdfReader(str(path))
        except Exception as e:
            raise PdfExtractionError(f"Failed to read PDF '{file_path}': {str(e)}") from e

        if len(reader.pages) == 0:
            raise PdfExtractionError(f"PDF '{file_path}' contains zero pages")

        page_texts: List[str] = []
        for i, page in enumerate(reader.pages):
            raw_text = page.extract_text() or ""
            cleaned = self._clean_page_text(raw_text)
            if cleaned:
                page_texts.append(cleaned)

        return "\n\n".join(page_texts)

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """Extracts and cleans all text content from raw PDF bytes."""
        import io
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        except Exception as e:
            raise PdfExtractionError(f"Failed to read PDF bytes: {str(e)}") from e

        if len(reader.pages) == 0:
            raise PdfExtractionError("PDF contains zero pages")

        page_texts: List[str] = []
        for page in reader.pages:
            raw_text = page.extract_text() or ""
            cleaned = self._clean_page_text(raw_text)
            if cleaned:
                page_texts.append(cleaned)

        return "\n\n".join(page_texts)

    def extract_metadata(self, file_path: str) -> Dict[str, Optional[str]]:
        """Extracts document metadata properties from a PDF."""
        path = Path(file_path)
        reader = pypdf.PdfReader(str(path))
        info = reader.metadata or {}
        return {
            "title": info.title,
            "author": info.author,
            "creator": info.creator,
            "producer": info.producer,
            "page_count": str(len(reader.pages)),
        }

    def _clean_page_text(self, text: str) -> str:
        """Removes page numbers, cleans null bytes and excessive whitespace."""
        text = text.replace("\x00", "")
        # Remove trailing/leading page numbers like 'Page 1 of 40'
        cleaned = self.PAGE_HEADER_FOOTER_PATTERN.sub("", text)
        # Normalize multiple spaces on a line while preserving line breaks
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.splitlines()]
        return "\n".join(lines).strip()
