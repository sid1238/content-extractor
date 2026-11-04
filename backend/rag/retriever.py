import re

from PyPDF2 import PdfReader
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

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


def _rejoin_wrapped_words(text):
    # PDFs split long words across lines ("tech-\nniques"), which would read as typos.
    return re.sub(r"([a-z])-\n([a-z])", r"\1\2", text)


def _read_docx(stream):
    doc = Document(stream)
    lines, tables = [], 0
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            lines.append(Paragraph(child, doc).text)
        elif child.tag == qn("w:tbl"):
            tables += 1
            for row in Table(child, doc).rows:
                cells = []
                for cell in row.cells:
                    if cell.text not in cells:  # merged cells repeat their text
                        cells.append(cell.text)
                lines.extend(cells)

    # Word stores a modern and a fallback copy of each text box, so de-duplicate them.
    box_texts = []
    for box in doc.element.body.iter(qn("w:txbxContent")):
        box_text = "\n".join("".join(t.text or "" for t in p.iter(qn("w:t"))) for p in box.iter(qn("w:p")))
        if box_text.strip() and box_text not in box_texts:
            box_texts.append(box_text)

    header_footer = []
    for section in doc.sections:
        for part in (section.header, section.footer):
            for line in [p.text for p in part.paragraphs] + [c.text for t in part.tables for r in t.rows for c in r.cells]:
                if line.strip() and line not in header_footer:
                    header_footer.append(line)

    header_text = "\n".join(header_footer)
    return {
        "text": "\n".join(filter(None, [header_text, *lines, *box_texts])),
        "meta": {
            "tables": tables, "text_boxes": len(box_texts), "header_footer_text": header_text,
            "images": len(doc.inline_shapes),
        },
    }


def _read_pdf(stream):
    reader = PdfReader(stream)
    images = 0
    for page in reader.pages:
        try:
            images += len(page.images)
        except Exception:
            pass  # unusual image encodings shouldn't stop the text from being read
    text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    return {"text": _rejoin_wrapped_words(text), "meta": {"pages": len(reader.pages), "images": images}}


def read_resume_upload(file_storage):
    """Reads an uploaded PDF or .docx in memory. Returns its text plus layout details for the ATS scan."""
    if file_storage.filename.lower().endswith(".pdf"):
        return _read_pdf(file_storage.stream)
    return _read_docx(file_storage.stream)
