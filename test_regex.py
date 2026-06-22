import re

def clean_text(text):
    return text.replace('\r', '')

def extract_reliance_bp(text):
    is_bp = "BP Exploration" in text
    company = "BP Exploration (Alpha) Limited" if is_bp else "Reliance Industries Limited"
    
    invoice_date = re.search(r"Invoice Date\s*:\s*([\d\.]+)", text)
    invoice_number = re.search(r"Invoice No\.?\s*:\s*([A-Z0-9\-]+)", text)
    due_date = re.search(r"Due date for payment\s*:\s*([\d\.]+)", text)
    ref_no = re.search(r"Reference No\.\s*:\s*([A-Z0-9\-]+)", text)
    
    amount_block = re.search(r"Amount\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)", text)
    item_total = amount_block.group(1) if amount_block else ""
    cst_value = amount_block.group(3) if amount_block else ""
    invoice_total = amount_block.group(4) if amount_block else ""
    
    rate = re.search(r"Rate\s*([\d\.]+)", text)
    quantity = re.search(r"Quantity\s+in MMBTU \(GCV\)\s*([\d,]+\.\d+)", text)
    currency = re.search(r"Currency\s*([A-Z]+)", text)
    
    del_period = re.search(r"Delivery and Billing Period\s*:\s*(.*?)\s*Consignee", text, re.DOTALL)
    
    buyer_address_match = re.search(r"Buyer's Address\s*:\s*(.*?)(?:CST No|TIN No|Buyer PAN)", text, re.DOTALL)
    buyer_address = buyer_address_match.group(1).strip().replace('\n', ' ') if buyer_address_match else ""
    
    name_match = re.search(r"Buyer's Code & Name\s*:\s*\d+\s*(.*?)(?:Buyer's Address)", text, re.DOTALL)
    name = name_match.group(1).strip().replace('\n', ' ') if name_match else ""
    
    seller_pan = re.search(r"Seller PAN\s*:\s*([A-Z0-9]+)", text)
    buyer_pan = re.search(r"Buyer PAN\s*:\s*([A-Z0-9]+)", text)
    supplier_gst = re.search(r"Seller PAN.*?GST No\s*:\s*([A-Z0-9]+)", text, re.DOTALL)
    if not supplier_gst: # Try BP format
        supplier_gst = re.search(r"GST No\s*:\s*([A-Z0-9]+)", text[seller_pan.end():] if seller_pan else text)
        
    buyer_gst = re.search(r"Buyer PAN.*?GST No\.?\s*:\s*([A-Z0-9]+)", text, re.DOTALL)
    
    return {
        "Company Name": company,
        "Invoice Date": invoice_date.group(1) if invoice_date else "",
        "Invoice Number": invoice_number.group(1) if invoice_number else "",
        "Due Date": due_date.group(1) if due_date else "",
        "Reference No": ref_no.group(1) if ref_no else "",
        "Item Total": item_total,
        "CST Value": cst_value,
        "Invoice Total": invoice_total,
        "Rate": rate.group(1) if rate else "",
        "Quantity": quantity.group(1) if quantity else "",
        "Currency": currency.group(1) if currency else "",
        "Delivery_and_Billing_Period": del_period.group(1).strip() if del_period else "",
        "Billing Address": re.sub(r'\s+', ' ', buyer_address),
        "Name": re.sub(r'\s+', ' ', name),
        "PAN Number": (seller_pan.group(1) if seller_pan else "") + " / " + (buyer_pan.group(1) if buyer_pan else ""),
        "Supplier GST": supplier_gst.group(1) if supplier_gst else "",
        "Buyer GST": buyer_gst.group(1) if buyer_gst else "",
        "Contract Number": ""
    }

def extract_gail(text):
    invoice_date = re.search(r"BILLING DATE\s*:\s*([\d\.]+)", text)
    invoice_number = re.search(r"SERIAL NO\.\s*([A-Z0-9]+)", text)
    ref_no = re.search(r"REF1\s*([A-Z0-9]+)", text)
    
    cst_total = re.search(r"%\s*([\d,]+\.\d{2})\s*([\d,]+\.\d{2})\s*GRAND TOTAL", text)
    cst_value = cst_total.group(1) if cst_total else ""
    invoice_total = cst_total.group(2) if cst_total else ""
    
    item_tot = re.search(r"([\d,]+\.\d{2})\s*TAXABLE AMOUNT", text)
    item_total = item_tot.group(1) if item_tot else ""
    
    rate = re.search(r"([\d\.]+)\s*INR / MMBTU", text)
    
    quantity = re.search(r"Quantity\s*UOM\s*([\d,]+\.\d+)", text)
    
    del_period = re.search(r"Delivery & Billing Period from\s*(.*?)\s*PARTICULAR", text, re.DOTALL)
    
    billing_address_match = re.search(r"SHIP TO PARTY / DELIVERY ADDRESS\s*(.*?)(?:CONTRACT NUMBER|EXCHANGE RATE)", text, re.DOTALL)
    billing_address = billing_address_match.group(1).strip() if billing_address_match else ""
    name = billing_address.split('\n')[0].strip() if billing_address else ""
    
    pan_no = re.search(r"PAN No\.\s*([A-Z0-9]+)\s*([A-Z0-9]+)", text)
    gst_no = re.search(r"GST No\.\s*([A-Z0-9]+)\s*([A-Z0-9]+)", text)
    contract_no = re.search(r"CONTRACT NUMBER\s*(\d+)", text)
    
    return {
        "Company Name": "GAIL (India) Ltd",
        "Invoice Date": invoice_date.group(1) if invoice_date else "",
        "Invoice Number": invoice_number.group(1) if invoice_number else "",
        "Due Date": invoice_date.group(1) if invoice_date else "",
        "Reference No": ref_no.group(1) if ref_no else "",
        "Item Total": item_total,
        "CST Value": cst_value,
        "Invoice Total": invoice_total,
        "Rate": rate.group(1) if rate else "",
        "Quantity": quantity.group(1) if quantity else "",
        "Currency": "INR",
        "Delivery_and_Billing_Period": del_period.group(1).strip() if del_period else "",
        "Billing Address": re.sub(r'\s+', ' ', billing_address),
        "Name": name,
        "PAN Number": (pan_no.group(1) if pan_no else "") + " / " + (pan_no.group(2) if pan_no else ""),
        "Supplier GST": gst_no.group(1) if gst_no else "",
        "Buyer GST": gst_no.group(2) if gst_no else "",
        "Contract Number": contract_no.group(1) if contract_no else ""
    }

for f in ["0000050516_3015006421.PDF.txt", "ctr-1246_16022026_28022026_3251203857_ril_ds.pdf.txt", "ctr-1246_16022026_28022026_3255203857_bp_ds.pdf.txt"]:
    with open(f, 'r', encoding='utf-8') as file:
        text = clean_text(file.read())
        print(f"--- {f} ---")
        if "GAIL" in text:
            print(extract_gail(text))
        else:
            print(extract_reliance_bp(text))

