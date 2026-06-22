import os
import sys
sys.path.append(os.path.abspath('.'))

from src.pdf_text_extractor import extract_pdf_text
from src.pdf_converter import pdf_to_images
from src.ocr_engine import extract_text

POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"

files = [
    r"invoices\0000050516_3015006421.PDF", # GAIL
    r"invoices\ctr-1246_16022026_28022026_3251203857_ril_ds.pdf", # RIL
    r"invoices\ctr-1246_16022026_28022026_3255203857_bp_ds.pdf" # BP
]

for file in files:
    print(f"--- TEXT FOR {file} ---")
    full_text = extract_pdf_text(file)
    if len(full_text.strip()) < 100:
        pages = pdf_to_images(file, poppler_path=POPPLER_PATH)
        full_text = ""
        for page in pages:
            full_text += extract_text(page) + "\n"
    
    with open(f"{os.path.basename(file)}.txt", "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"Saved {os.path.basename(file)}.txt")
