#backend/services/resume_parser.py
import pdfplumber
import docx2txt
from io import BytesIO

def extract_text(file):
    """Extract text from PDF or DOCX file."""
    # Read the file content into a BytesIO object
    content = file.file.read()
    file_obj = BytesIO(content)
    
    if file.filename.endswith('.pdf'):
        with pdfplumber.open(file_obj) as pdf:
            return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    elif file.filename.endswith('.docx'):
        return docx2txt.process(file_obj)
    return ""
