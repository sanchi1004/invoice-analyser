from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Invoice

def save_invoice(data: dict):
    """
    Saves an invoice to the database.
    Checks for duplicates by invoice_number and company_name.
    """
    db = SessionLocal()
    try:
        # Retrieve keys safely with dict.get and fallback values
        invoice_number = data.get("Invoice Number") or data.get("Invoice No") or ""
        company_name = data.get("Company Name") or ""

        # Check if an invoice with same invoice_number and company_name already exists
        if invoice_number and company_name:
            existing = db.query(Invoice).filter(
                Invoice.invoice_number == invoice_number,
                Invoice.company_name == company_name
            ).first()
            if existing:
                return "Invoice already exists"

        # Create Invoice record mapping standard and fallback keys
        invoice = Invoice(
            invoice_number=invoice_number,
            invoice_date=data.get("Invoice Date") or "",
            invoice_total=data.get("Invoice Total") or "",
            company_name=company_name,
            billing_address=data.get("Billing Address") or "",
            due_date=data.get("Due Date") or "",
            customer_name=data.get("Name") or data.get("Customer Name") or "",
            reference_no=data.get("Reference No") or "",
            rate=data.get("Rate") or "",
            cst_value=data.get("CST Value") or "",
            currency=data.get("Currency") or "",
            delivery_period=data.get("Delivery_and_Billing_Period") or data.get("Delivery Period") or "",
            item_total=data.get("Item Total") or "",
            quantity=data.get("Quantity") or "",
            file_path=data.get("File Path") or "",
            file_name=data.get("File Name") or "",
            result=data.get("Result") or ""
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice.id
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
        raise e
    finally:
        db.close()

def get_all_invoices(db: Session):
    return db.query(Invoice).all()

def get_invoice(db: Session, invoice_id: int):
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()

def delete_invoice(db: Session, invoice_id: int):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice:
        db.delete(invoice)
        db.commit()
        return True
    return False

def update_invoice(db: Session, invoice_id: int, data: dict):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice:
        for key, value in data.items():
            if hasattr(invoice, key):
                setattr(invoice, key, value)
        db.commit()
        db.refresh(invoice)
        return invoice
    return None

def search_by_invoice_number(db: Session, invoice_number: str):
    return db.query(Invoice).filter(Invoice.invoice_number.ilike(f"%{invoice_number}%")).all()

def search_by_company(db: Session, company_name: str):
    return db.query(Invoice).filter(Invoice.company_name.ilike(f"%{company_name}%")).all()

def search_by_date(db: Session, invoice_date: str):
    return db.query(Invoice).filter(Invoice.invoice_date == invoice_date).all()