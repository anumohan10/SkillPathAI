import pdfplumber
import docx2txt

def extract_text(file):
    """Extract text from PDF or DOCX file."""
    if file.name.endswith('.pdf'):
        with pdfplumber.open(file) as pdf:
            return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    elif file.name.endswith('.docx'):
        return docx2txt.process(file)
    return ""
