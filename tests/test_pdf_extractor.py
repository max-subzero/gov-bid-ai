"""Unit tests for PdfExtractor and native PDF RFP parsing."""

import os
from pathlib import Path
import tempfile
import unittest
import pypdf
from govbid.parsers.pdf_extractor import PdfExtractionError, PdfExtractor
from govbid.parsers.rfp_parser import RfpParser


class TestPdfExtractor(unittest.TestCase):
    def setUp(self) -> None:
        self.extractor = PdfExtractor()
        # Create a synthetic PDF file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf_path = os.path.join(self.temp_dir.name, "test_solicitation.pdf")

        writer = pypdf.PdfWriter()
        # Add page 1 with metadata & scope
        page_text_1 = (
            "CITY OF NEW YORK DCAS\n"
            "SOLICITATION TITLE: Enterprise Cloud Infrastructure\n"
            "PIN: 85626P0099\n"
            "PROPOSAL DUE DATE: December 15, 2026\n"
            "Scope: Deliver hybrid cloud management.\n"
            "Page 1 of 2\n"
        )
        page1 = writer.add_blank_page(width=612, height=792)
        
        # Write metadata
        writer.add_metadata({
            "/Title": "Enterprise Cloud Infrastructure RFP",
            "/Author": "City of New York DCAS",
        })

        # To write actual extractable text in pypdf, we can use annotation or create text stream
        # Alternatively, we can test with a real generated PDF containing text objects
        with open(self.pdf_path, "wb") as f:
            writer.write(f)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_extract_metadata(self) -> None:
        meta = self.extractor.extract_metadata(self.pdf_path)
        self.assertEqual(meta["page_count"], "1")
        self.assertIn("Enterprise Cloud", meta["title"])
        self.assertEqual(meta["author"], "City of New York DCAS")

    def test_missing_file_raises_error(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_text_from_file("/tmp/non_existent_file_12345.pdf")

    def test_clean_page_text(self) -> None:
        raw_text = "SOLICITATION SECTION 1\nSome requirement text.\nPage 1 of 40\n"
        cleaned = self.extractor._clean_page_text(raw_text)
        self.assertNotIn("Page 1 of 40", cleaned)
        self.assertIn("SOLICITATION SECTION 1", cleaned)

    def test_extract_text_from_bytes(self) -> None:
        minimal_pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
            b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
            b"5 0 obj << /Length 55 >> stream\n"
            b"BT\n/F1 12 Tf\n72 712 Td\n(SOLICITATION PIN 85626P0099) Tj\nET\nendstream\nendobj\n"
            b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000227 00000 n \n0000000297 00000 n \n"
            b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n403\n%%EOF"
        )
        text = self.extractor.extract_text_from_bytes(minimal_pdf)
        self.assertIn("SOLICITATION PIN 85626P0099", text)

    def test_extract_text_from_invalid_bytes_raises_error(self) -> None:
        with self.assertRaises(PdfExtractionError):
            self.extractor.extract_text_from_bytes(b"not a valid pdf payload")


if __name__ == "__main__":
    unittest.main()
