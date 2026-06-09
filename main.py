from src.pdf_converter import pdf_to_images
from src.ocr_engine import extract_text
from src.extractor import extract_invoice_data

pages = pdf_to_images(
    "invoices/sample1.pdf",
    poppler_path=r"C:\poppler-26.02.0\Library\bin"
)

text = extract_text(pages[0])

invoice = extract_invoice_data(text)

print(invoice)