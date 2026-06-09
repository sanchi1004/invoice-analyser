import re

def extract_invoice_number(text):
    match = re.search(
        r"Invoice No\.\s*:\s*(\d+)",
        text
    )

    return match.group(1) if match else None
def extract_invoice_date(text):
    match = re.search(
        r"Invoice Date\s*:\s*([\d\.]+)",
        text
    )

    return match.group(1) if match else None
def extract_gstin(text):
    match = re.search(
        r"GST No:\s*([A-Z0-9]+)",
        text
    )

    return match.group(1) if match else None
def extract_pan(text):
    match = re.search(
        r"Buyer PAN\s*:\s*([A-Z0-9]+)",
        text
    )

    return match.group(1) if match else None
def extract_total(text):
    match = re.search(
        r"Grand Total\s+([\d,]+\.\d+)",
        text
    )

    return match.group(1) if match else None
def extract_invoice_data(text):
    return {
        "invoice_no": extract_invoice_number(text),
        "invoice_date": extract_invoice_date(text),
        "gstin": extract_gstin(text),
        "buyer_pan": extract_pan(text),
        "total": extract_total(text)
    }