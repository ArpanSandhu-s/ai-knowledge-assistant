from pypdf import PdfReader
from docx import Document

def extract_text(uploaded_file):

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):

        pdf = PdfReader(uploaded_file)

        text = ""

        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text

    elif file_name.endswith(".docx"):

        doc = Document(uploaded_file)

        return "\n".join(
            para.text for para in doc.paragraphs
        )

    elif file_name.endswith(".txt"):

        return uploaded_file.read().decode("utf-8")

    return ""