import fitz

def extract_pdf_text(pdf_path):

    text = ""

    pdf = fitz.open(pdf_path)

    for page in pdf:
        text += page.get_text()
        text += "\n"

    pdf.close()

    return text