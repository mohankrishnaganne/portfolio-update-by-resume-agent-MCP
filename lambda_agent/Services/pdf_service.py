from PyPDF2 import PdfReader

def extract_text_from_pdf(file_obj) -> str:
    file_obj.seek(0)
    pdf_reader = PdfReader(file_obj)
    resume_text = ""
    for page in pdf_reader.pages:
        resume_text += page.extract_text() + "\n"
    return resume_text