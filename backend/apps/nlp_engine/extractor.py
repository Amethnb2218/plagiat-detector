import re
from pathlib import Path
import pdfplumber
from docx import Document as DocxDocument


class TextExtractor:
    """Extraction de texte brut depuis PDF et DOCX avec nettoyage."""

    @staticmethod
    def extract_from_pdf(file_path: str) -> dict:
        text_parts = []
        page_count = 0
        metadata = {}

        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            metadata = pdf.metadata or {}
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        raw_text = '\n'.join(text_parts)
        return {
            'raw_text': raw_text,
            'page_count': page_count,
            'metadata': {k: str(v) for k, v in metadata.items() if v},
        }

    @staticmethod
    def extract_from_docx(file_path: str) -> dict:
        doc = DocxDocument(file_path)
        text_parts = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        metadata = {
            'author': doc.core_properties.author or '',
            'title': doc.core_properties.title or '',
            'created': str(doc.core_properties.created) if doc.core_properties.created else '',
        }

        raw_text = '\n'.join(text_parts)
        page_count = max(1, len(raw_text) // 3000)

        return {
            'raw_text': raw_text,
            'page_count': page_count,
            'metadata': {k: v for k, v in metadata.items() if v},
        }

    @classmethod
    def extract(cls, file_path: str, file_type: str) -> dict:
        if file_type == 'pdf':
            return cls.extract_from_pdf(file_path)
        elif file_type == 'docx':
            return cls.extract_from_docx(file_path)
        raise ValueError(f"Type de fichier non supporté: {file_type}")


class TextCleaner:
    """Nettoyage et normalisation du texte académique."""

    @staticmethod
    def clean(text: str) -> str:
        text = re.sub(r'\x0c', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[^\S\n]+', ' ', text)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not re.match(r'^[\d\s\-_=]+$', line):
                cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)
        text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
        return text.strip()
