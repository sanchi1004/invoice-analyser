import os

from src.pdf_converter import pdf_to_images
from src.ocr_engine import extract_text
from src.extractor import extract_invoice_data
from src.excel_exporter import export_to_excel
from src.pdf_text_extractor import extract_pdf_text
POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"

all_invoices = []

for file in os.listdir("invoices"):

    if file.lower().endswith(".pdf"):

        pdf_path = os.path.join("invoices", file)

        print(f"Processing {file}...")

        full_text = extract_pdf_text(pdf_path)

        if len(full_text.strip()) < 100:

            print("No text found. Using OCR...")
            pages = pdf_to_images(
                pdf_path,
                poppler_path=POPPLER_PATH
            )

            full_text = ""

            for page in pages:
                full_text += extract_text(page)
                full_text += "\n"
        
        invoice = extract_invoice_data(full_text,pdf_path)

        invoice["source_file"] = file

        all_invoices.append(invoice)

print(f"\nProcessed {len(all_invoices)} invoices")

export_to_excel(all_invoices)