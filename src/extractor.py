import re

def get_match(pattern, text):
    match = re.search(
        pattern,
        text,
        re.IGNORECASE | re.DOTALL
    )

    return match.group(1).strip() if match else ""


def extract_invoice_data(text, file_path):

    invoice_number = get_match(
        r"Invoice No\.\s*:\s*([A-Z0-9\-]+)",
        text
    )

    invoice_date = get_match(
        r"Invoice Date\s*:\s*([0-9\.]+)",
        text
    )

    reference_no = get_match(
        r"Reference No\.\s*:\s*([A-Z0-9\-]+)",
        text
    )

    delivery_period = get_match(
        r"Delivery and Billing Period\s*:\s*(.*?)\n",
        text
    )

    due_date = get_match(
        r"Due date for payment\s*:\s*([0-9\.]+)",
        text
    )

    invoice_total = get_match(
        r"Grand Total\s*([0-9,]+\.[0-9]+)",
        text
    )

    consignee_name = get_match(
        r"Consignee Code & Name\s*:\s*\d+\s*(.*?)\s*Reference No",
        text
    )

    billing_address = get_match(
        r"Consignee Address\s*:\s*(.*?)\s*CST No",
        text
    )

    quantity = get_match(
        r"Quantity\s*in MMBTU \(GCV\)\s*([0-9,]+\.[0-9]+)",
        text
    )

    rate = get_match(
        r"Rate\s*([0-9]+\.[0-9]+)",
        text
    )

    currency = get_match(
        r"Currency\s*(USD|INR|EUR|GBP)",
        text
    )

    amounts = re.findall(
        r"\d[\d,]*\.\d+",
        text
    )

    subtotal = ""
    cst_value = ""

    if len(amounts) >= 4:
        subtotal = amounts[0]
        cst_value = amounts[2]

    return {
        "Invoice Date": invoice_date,
        "Invoice Number": invoice_number,
        "Invoice Total": invoice_total,
        "Billing Address": billing_address.replace("\n", " "),
        "Due Date": due_date,
        "Name": consignee_name.replace("\n", " "),
        "Referene No.": reference_no,
        "Rate": rate,
        "CST value": cst_value,
        "Currency": currency,
        "Delivery_and_Billing_Period": delivery_period,
        "Item Total": subtotal,
        "Quantity": quantity,
        "Result": "Success",
        "File Path": file_path
    }