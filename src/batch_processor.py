import os

from src.pdf_text_extractor import extract_pdf_text
from src.extractor import extract_invoice_data


def process_folder(folder_path):

    invoices = []

    for filename in os.listdir(folder_path):

        if not filename.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(
            folder_path,
            filename
        )

        try:

            text = extract_pdf_text(pdf_path)
            
            print("\n" + "="*100)
            print(filename)
            print("="*100)
            print(text)
            print("="*100 + "\n")

            invoice = extract_invoice_data(
                text,
                pdf_path
            )

            invoices.append(invoice)

        except Exception as e:

            invoices.append({
                "File Name": filename,
                "Result": f"Error: {str(e)}"
            })

    return invoices