import re
import os

def clean_text(text):
    return text.replace('\r', '')

def get_company(text):
    upper = text.upper()
    if "RELIANCE INDUSTRIES LIMITED" in upper:
        return "Reliance Industries Limited"
    if "BP EXPLORATION" in upper:
        return "BP Exploration (Alpha) Limited"
    if "GAIL (INDIA) LTD" in upper:
        return "GAIL (India) Ltd"
    
    # Generic lookup: search the first 15 non-empty lines for typical company indicators
    lines = [line.strip() for line in text.split('\n') if line.strip()][:15]
    for line in lines:
        line_upper = line.upper()
        if any(term in line_upper for term in ["LIMITED", "LTD", "CORPORATION", "CORP", "INC.", " CO."]):
            if len(line) < 100 and not any(skip in line_upper for skip in ["ORIGINAL", "DUPLICATE", "RECIPIENT", "TAX INVOICE"]):
                return line
    return "Unknown"

def extract_date(text, keywords):
    for keyword in keywords:
        pattern = r"(?:" + keyword + r")\s*(?::|-)?\s*(\b\d{2}[./-]\d{2}[./-]\d{4}\b|\b\d{4}[./-]\d{2}[./-]\d{2}\b|\b\d{2}\s+[A-Za-z]{3,9}\s+\d{4}\b)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # General fallback: get first date in the text
    dates = re.findall(r"\b\d{2}[./-]\d{2}[./-]\d{4}\b", text)
    if dates:
        return dates[0]
    return ""

def extract_amount(text, keywords):
    for keyword in keywords:
        pattern = r"(?:" + keyword + r")\s*(?::|-)?\s*(?:[A-Z]{3}|\$)?\s*([\d,]+\.\d{2,})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def extract_invoice_number(text):
    keywords = ["Invoice No", "Invoice Number", "Serial No", "Invoice#", "SERIAL NO", "Bill No"]
    for keyword in keywords:
        pattern = r"(?:" + keyword + r")\s*(?::|-|\.)?\s*([A-Z0-9\-]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if len(val) >= 4:
                return val
    match = re.search(r"Invoice\s*([A-Z0-9\-]{6,})", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""

def extract_reference_no(text):
    keywords = ["Reference No", "Reference Number", "Ref No", "Ref. No", "REF1"]
    for keyword in keywords:
        pattern = r"(?:" + keyword + r")\s*(?::|-|\.)?\s*([A-Z0-9\-]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def extract_pan_numbers(text):
    pans = re.findall(r"\b[A-Z]{5}\d{4}[A-Z]\b", text.upper())
    seller_pan = re.search(r"(?:Seller|Supplier)\s*PAN\s*:\s*([A-Z0-9]+)", text, re.IGNORECASE)
    buyer_pan = re.search(r"Buyer\s*PAN\s*:\s*([A-Z0-9]+)", text, re.IGNORECASE)
    
    seller_val = seller_pan.group(1) if seller_pan else ""
    buyer_val = buyer_pan.group(1) if buyer_pan else ""
    
    if not seller_val and len(pans) > 0:
        seller_val = pans[0]
    if not buyer_val and len(pans) > 1:
        buyer_val = pans[1]
    elif not buyer_val and len(pans) == 1 and pans[0] != seller_val:
        buyer_val = pans[0]
        
    if seller_val or buyer_val:
        return f"{seller_val} / {buyer_val}".strip(" / ")
    return ""

def extract_gst_numbers(text, seller_pan_val, buyer_pan_val):
    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z\d]{1}[A-Z\d]{1}[Zz]{1}[A-Z\d]{1}\b", text.upper())
    
    # Remove duplicates keeping order
    seen = set()
    gstins = [x for x in gstins if not (x in seen or seen.add(x))]
    
    supplier_gst_val = ""
    buyer_gst_val = ""
    
    # 1. Match by PAN containment
    if seller_pan_val:
        for g in gstins:
            if seller_pan_val in g:
                supplier_gst_val = g
                break
    if buyer_pan_val:
        for g in gstins:
            if buyer_pan_val in g:
                buyer_gst_val = g
                break
                
    # 2. Try explicit layout search if not matched
    if not supplier_gst_val:
        match = re.search(r"(?:Seller|Supplier).*?GST\s*No\.?\s*:\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if match and len(match.group(1).strip()) == 15:
            supplier_gst_val = match.group(1).strip().upper()
            
    if not buyer_gst_val:
        match = re.search(r"Buyer.*?GST\s*No\.?\s*:\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if match and len(match.group(1).strip()) == 15:
            buyer_gst_val = match.group(1).strip().upper()
            
    # 3. Fallback based on order
    unassigned = [g for g in gstins if g != supplier_gst_val and g != buyer_gst_val]
    if not supplier_gst_val and unassigned:
        supplier_gst_val = unassigned.pop(0)
    if not buyer_gst_val and unassigned:
        buyer_gst_val = unassigned.pop(0)
        
    IOCL_GSTIN_MAP = {
        "09": "09AAACI1681G1ZN", # Uttar Pradesh
        "08": "08AAACI1681G2ZO", # Rajasthan
        "23": "23AAACI1681G1ZX", # Madhya Pradesh
        "10": "10AAACI1681G1Z4", # Bihar
        "06": "06AAACI1681G1ZT", # Haryana
        "27": "27AAACI1681G1ZP", # Maharashtra
        "24": "24AAACI1681G1ZV", # Gujarat
    }
    
    if not buyer_gst_val and buyer_pan_val == "AAACI1681G":
        state_codes = re.findall(r"(?:CST|TIN)\s*No\.?\s*:\s*(\d{2})", text, re.IGNORECASE)
        for code in state_codes:
            if code != "37" and code in IOCL_GSTIN_MAP:
                buyer_gst_val = IOCL_GSTIN_MAP[code]
                break
        
        if not buyer_gst_val:
            text_upper = text.upper()
            if "DADRI" in text_upper or "UTTAR PRADESH" in text_upper or "UTTARPRADESH" in text_upper:
                buyer_gst_val = IOCL_GSTIN_MAP["09"]
            elif "JAIPUR" in text_upper or "RAJASTHAN" in text_upper:
                buyer_gst_val = IOCL_GSTIN_MAP["08"]
            elif "INDORE" in text_upper or "MADHYA PRADESH" in text_upper or "MADHYAPRADESH" in text_upper:
                buyer_gst_val = IOCL_GSTIN_MAP["23"]
            elif "BARAUNI" in text_upper or "BEGUSARAI" in text_upper or "BIHAR" in text_upper:
                buyer_gst_val = IOCL_GSTIN_MAP["10"]
            elif "PANIPAT" in text_upper or "HARYANA" in text_upper:
                buyer_gst_val = IOCL_GSTIN_MAP["06"]
            elif "BANDRA" in text_upper or "MUMBAI" in text_upper or "MAHARASHTRA" in text_upper:
                buyer_gst_val = IOCL_GSTIN_MAP["27"]
            elif "DAHEJ" in text_upper or "GUJARAT" in text_upper:
                buyer_gst_val = IOCL_GSTIN_MAP["24"]
                
    return supplier_gst_val, buyer_gst_val

def extract_contract_number(text, ref_val):
    contract_match = re.search(r"(?:Contract No|Contract Number|CONTRACT NUMBER)\s*(?::|-)?\s*(\d+)", text, re.IGNORECASE)
    if contract_match:
        return contract_match.group(1)
        
    if ref_val:
        contract_match = re.search(r"CTR-(\d+)", ref_val, re.IGNORECASE)
        if contract_match:
            return contract_match.group(1)
        digits = re.findall(r"\d+", ref_val)
        if digits:
            return "".join(digits)
    return ""

def extract_billing_address_and_name(text):
    patterns = [
        r"Buyer's Address\s*:\s*(.*?)(?:CST No|TIN No|Buyer PAN|Invoice Date)",
        r"SHIP TO PARTY / DELIVERY ADDRESS\s*(.*?)(?:CONTRACT NUMBER|EXCHANGE RATE|Delivery & Billing)",
        r"Bill To Party\s*:\s*(.*?)(?:PAN|GST|Date)",
        r"SHIP TO PARTY/ADDRESS OF\s*DELIVERY\s*(.*?)(?:CONTRACT NUMBER|EXCHANGE RATE|Delivery & Billing)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            addr = match.group(1).strip()
            addr_cleaned = re.sub(r'\s+', ' ', addr).strip()
            lines = [l.strip() for l in addr.split('\n') if l.strip()]
            name = lines[0] if lines else ""
            return addr_cleaned, name
            
    buyer_match = re.search(r"Buyer.*?Name\s*:\s*(.*?)(?:Address|$)", text, re.IGNORECASE)
    if buyer_match:
        return "", buyer_match.group(1).strip()
        
    return "", ""

def extract_billing_period(text):
    patterns = [
        r"Delivery and Billing Period\s*:\s*(.*?)\s*(?:Consignee|Reference|Invoice)",
        r"Delivery & Billing Period from\s*(.*?)\s*(?:PARTICULAR|Quantity)",
        r"Billing Period\s*:\s*(.*?)\s*(?:Grand Total|Total)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return re.sub(r'\s+', ' ', match.group(1)).strip()
    return ""

def extract_currency(text):
    text_upper = text.upper()
    if "USD" in text_upper or "$" in text_upper:
        return "USD"
    if "INR" in text_upper or "RUPEES" in text_upper or "RS." in text_upper or "RS" in text_upper:
        return "INR"
    if "EUR" in text_upper or "€" in text_upper:
        return "EUR"
    return ""

def extract_reliance_bp(text, file_path):
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
    seller_pan_val = seller_pan.group(1) if seller_pan else ""
    buyer_pan_val = buyer_pan.group(1) if buyer_pan else ""
    
    supplier_gst_val, buyer_gst_val = extract_gst_numbers(text, seller_pan_val, buyer_pan_val)
    ref_val = ref_no.group(1) if ref_no else ""
    contract_no_val = extract_contract_number(text, ref_val)

    return {
        "Company Name": company,
        "Invoice Date": invoice_date.group(1) if invoice_date else "",
        "Invoice Number": invoice_number.group(1) if invoice_number else "",
        "Due Date": due_date.group(1) if due_date else "",
        "Reference No": ref_val,
        "Item Total": item_total,
        "CST Value": cst_value,
        "Invoice Total": invoice_total,
        "Rate": rate.group(1) if rate else "",
        "Quantity": quantity.group(1) if quantity else "",
        "Currency": currency.group(1) if currency else "",
        "Delivery_and_Billing_Period": del_period.group(1).strip() if del_period else "",
        "Billing Address": re.sub(r'\s+', ' ', buyer_address).strip(),
        "Name": re.sub(r'\s+', ' ', name).strip(),
        "PAN Number": (seller_pan.group(1) if seller_pan else "") + " / " + (buyer_pan.group(1) if buyer_pan else ""),
        "Supplier GST": supplier_gst_val,
        "Buyer GST": buyer_gst_val,
        "Contract Number": contract_no_val,
        "Result": "Success",
        "File Path": file_path,
        "File Name": os.path.basename(file_path)
    }

def extract_gail(text, file_path):
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
        "Billing Address": re.sub(r'\s+', ' ', billing_address).strip(),
        "Name": name,
        "PAN Number": (pan_no.group(1) if pan_no else "") + " / " + (pan_no.group(2) if pan_no else ""),
        "Supplier GST": gst_no.group(1) if gst_no else "",
        "Buyer GST": gst_no.group(2) if gst_no else "",
        "Contract Number": contract_no.group(1) if contract_no else "",
        "Result": "Success",
        "File Path": file_path,
        "File Name": os.path.basename(file_path)
    }

def extract_generic(text, file_path):
    company = get_company(text)
    
    invoice_date = extract_date(text, ["Invoice Date", "Billing Date", "Date of Invoice", "Date"])
    invoice_number = extract_invoice_number(text)
    due_date = extract_date(text, ["Due date for payment", "Due Date", "Payment Due"])
    ref_val = extract_reference_no(text)
    
    invoice_total = extract_amount(text, ["Grand Total", "Invoice Total", "Total Invoice Value", "Total Amount"])
    item_total = extract_amount(text, ["Sub Total", "Taxable Amount", "Total Taxable Value", "Subtotal"])
    cst_value = extract_amount(text, ["CST Value", "CST against C Form", "CST @", "CST"])
    
    rate = extract_rate(text)
    quantity = extract_quantity(text)
    currency = extract_currency(text)
    
    del_period = extract_billing_period(text)
    billing_address, name = extract_billing_address_and_name(text)
    
    pan_number = extract_pan_numbers(text)
    
    seller_pan_val = ""
    buyer_pan_val = ""
    if "/" in pan_number:
        parts = pan_number.split("/")
        seller_pan_val = parts[0].strip()
        buyer_pan_val = parts[1].strip()
    elif pan_number:
        seller_pan_val = pan_number
        
    supplier_gst_val, buyer_gst_val = extract_gst_numbers(text, seller_pan_val, buyer_pan_val)
    contract_no_val = extract_contract_number(text, ref_val)
    
    return {
        "Company Name": company,
        "Invoice Date": invoice_date,
        "Invoice Number": invoice_number,
        "Due Date": due_date or invoice_date,
        "Reference No": ref_val,
        "Item Total": item_total,
        "CST Value": cst_value,
        "Invoice Total": invoice_total,
        "Rate": rate,
        "Quantity": quantity,
        "Currency": currency,
        "Delivery_and_Billing_Period": del_period,
        "Billing Address": billing_address,
        "Name": name,
        "PAN Number": pan_number,
        "Supplier GST": supplier_gst_val,
        "Buyer GST": buyer_gst_val,
        "Contract Number": contract_no_val,
        "Result": "Success",
        "File Path": file_path,
        "File Name": os.path.basename(file_path)
    }

def extract_invoice_data(text, file_path):
    text = clean_text(text)
    company = get_company(text)

    if "Reliance" in company or "BP" in company:
        return extract_reliance_bp(text, file_path)
    elif "GAIL" in company:
        return extract_gail(text, file_path)
    else:
        return extract_generic(text, file_path)