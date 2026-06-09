import os

from src.pdf_converter import pdf_to_images
from src.ocr_engine import extract_text
from src.extractor import extract_invoice_data
from src.excel_exporter import export_to_excel

POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"

all_invoices = []

for file in os.listdir("invoices"):

    if file.lower().endswith(".pdf"):

        pdf_path = os.path.join("invoices", file)

        print(f"Processing {file}...")

        pages = pdf_to_images(
            pdf_path,
            poppler_path=POPPLER_PATH
        )

        text = extract_text(pages[0])

        invoice = extract_invoice_data(text)

        invoice["source_file"] = file

        all_invoices.append(invoice)

print(f"\nProcessed {len(all_invoices)} invoices")

export_to_excel(all_invoices)