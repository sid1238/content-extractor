from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_file(filepath):
    if filepath.endswith(".pdf"):
        reader = PdfReader(filepath)
        return " ".join(page.extract_text() for page in reader.pages if page.extract_text())

    elif filepath.endswith(".docx"):
        doc = Document(filepath)
        return " ".join([para.text for para in doc.paragraphs])

    elif filepath.endswith(".txt"):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    else:
        raise ValueError("Unsupported file format")