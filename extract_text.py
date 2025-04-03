import pdfplumber
import PyPDF2
from docx import Document



def extract_text(file_path):
    try:
        if file_path.endswith('.pdf'):
            text = ""
            # Try pdfplumber first for better accuracy
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted_text = page.extract_text()
                    if extracted_text:
                        text += extracted_text + "\n"

            # If pdfplumber fails to extract text, fallback to PyPDF2
            if not text.strip():
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() or ""

            return text.strip()

        elif file_path.endswith('.docx'):
            doc = Document(file_path)
            return '\n'.join([paragraph.text for paragraph in doc.paragraphs])

        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

        else:
            return "Unsupported file format"

    except Exception as e:
        return f"Error extracting text: {str(e)}"
