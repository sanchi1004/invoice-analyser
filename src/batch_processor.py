import os

from src.pdf_text_extractor import extract_pdf_text
from src.extractor import extract_invoice_data
from database.crud import save_invoice


def process_folder(folder_path):

    invoices = []

    duplicate_files = []
    processed_count = 0

    for filename in os.listdir(folder_path):

        if not filename.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(
            folder_path,
            filename
        )

        try:
            text = extract_pdf_text(pdf_path)
            invoice = extract_invoice_data(
                text,
                pdf_path
            )

            # Save the invoice to PostgreSQL using SQLAlchemy
            db_res = save_invoice(invoice)
            print(f"Database save result for {filename}: {db_res}")

            if isinstance(db_res, dict) and db_res.get("status") == "duplicate":
                duplicate_files.append(filename)
                invoices.append({
                    "File Name": filename,
                    "Result": "Duplicate invoice already exists in the database"
                })
            else:
                processed_count += 1
                invoices.append(invoice)

        except Exception as e:

            invoices.append({
                "File Name": filename,
                "Result": f"Error: {str(e)}"
            })

    return {
        "invoices": invoices,
        "processed_count": processed_count,
        "duplicates": duplicate_files
    }

    return invoices