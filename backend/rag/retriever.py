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

def extract_text_from_upload(file_storage):
    """Same as extract_text_from_file, but reads an uploaded file in memory."""
    name = file_storage.filename.lower()
    if name.endswith(".pdf"):
        reader = PdfReader(file_storage.stream)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

    elif name.endswith(".docx"):
        doc = Document(file_storage.stream)
        return "\n".join(para.text for para in doc.paragraphs)

    elif name.endswith(".txt"):
        return file_storage.stream.read().decode("utf-8", errors="ignore")

    else:
        raise ValueError("Unsupported file format")
