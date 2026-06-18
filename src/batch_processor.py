import os

from src.pdf_text_extractor import extract_pdf_text
from src.extractor import extract_invoice_data

def process_folder(folder_path):

    invoices = []

    for file in os.listdir(folder_path):

        if not file.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(
            folder_path,
            file
        )

        text = extract_pdf_text(pdf_path)

        invoice = extract_invoice_data(
            text,
            pdf_path
        )

        invoices.append(invoice)

    return invoices