from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from typing import List, Optional
import shutil
import os
import traceback
import re
from collections import defaultdict
from sqlalchemy import text

from pydantic import BaseModel
from sqlalchemy.orm import Session
import sqlalchemy.exc
import sys

from src.batch_processor import process_folder
from src.excel_exporter import export_to_excel

# =====================================================
# DATABASE IMPORTS & INITIALIZATION
# =====================================================
# 1. Import engine and Base from your connection file
from database.connection import SessionLocal, engine, Base

# 2. Import your models (CRUCIAL: Must be imported before create_all)
from database.models import Invoice

# 3. Import your CRUD operations
from database.crud import (
    get_all_invoices, get_invoice, delete_invoice, update_invoice,
    search_by_invoice_number, search_by_company, search_by_date
)

# 4. Create the tables in PostgreSQL and ensure new columns exist

def ensure_invoice_columns():
    with engine.connect() as conn:
        existing_columns = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'invoices'"
        )).fetchall()
        existing_columns = {row[0] for row in existing_columns}

        for column_name in [
            'contract_number',
            'pan_number',
            'supplier_gst',
            'buyer_gst',
        ]:
            if column_name not in existing_columns:
                conn.execute(text(
                    f"ALTER TABLE invoices ADD COLUMN {column_name} VARCHAR"
                ))
                print(f"Added missing column: {column_name}")

try:
    Base.metadata.create_all(bind=engine)
    try:
        ensure_invoice_columns()
    except Exception as exc:
        print(f"Invoice schema update warning: {exc}")
except Exception as exc:
    print(f"Database initialization skipped: {exc}")

# =====================================================
# CONFIG
# =====================================================

UPLOAD_FOLDER = "uploads"
INVOICE_FOLDER = "invoices"
OUTPUT_FOLDER = "output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(INVOICE_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =====================================================
# APP
# =====================================================

app = FastAPI(
    title="Invoice Analyzer",
    version="1.0.0"
)

templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# DATABASE DEPENDENCY & UTILS
# =====================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def serialize_invoice(invoice):
    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date,
        "invoice_total": invoice.invoice_total,
        "company_name": invoice.company_name,
        "billing_address": invoice.billing_address,
        "due_date": invoice.due_date,
        "customer_name": invoice.customer_name,
        "reference_no": invoice.reference_no,
        "rate": invoice.rate,
        "cst_value": invoice.cst_value,
        "currency": invoice.currency,
        "delivery_period": invoice.delivery_period,
        "item_total": invoice.item_total,
        "quantity": invoice.quantity,
        "contract_number": invoice.contract_number,
        "pan_number": invoice.pan_number,
        "supplier_gst": invoice.supplier_gst,
        "buyer_gst": invoice.buyer_gst,
        "file_path": invoice.file_path,
        "file_name": invoice.file_name,
        "result": invoice.result,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None
    }

# =====================================================
# HOME PAGE
# =====================================================

@app.get("/")
def root():
    return FileResponse("templates/index.html")


def parse_amount(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return 0.0

    cleaned = re.sub(r"[^\d.-]", "", text)
    if not cleaned or cleaned in {"-", "."}:
        return 0.0

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


@app.get("/analytics/summary")
def analytics_summary(company: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        invoices = get_all_invoices(db)
    except Exception as exc:
        print(f"Analytics fetch failed: {exc}")
        invoices = []

    company_filter = (company or "").strip().lower()
    if company_filter:
        invoices = [invoice for invoice in invoices if company_filter in (invoice.company_name or "").lower()]

    totals = defaultdict(lambda: {"total": 0.0, "count": 0, "latest_invoice": None})

    for invoice in invoices:
        company_name = invoice.company_name or "Unknown Company"
        amount = parse_amount(invoice.invoice_total)
        entry = totals[company_name]
        entry["total"] += amount
        entry["count"] += 1
        if entry["latest_invoice"] is None or (invoice.created_at and (entry["latest_invoice"].get("created_at") is None or invoice.created_at > entry["latest_invoice"].get("created_at"))):
            entry["latest_invoice"] = {
                "invoice_number": invoice.invoice_number or "-",
                "invoice_total": invoice.invoice_total or "-",
                "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
            }

    companies = []
    for company_name, entry in sorted(totals.items(), key=lambda item: item[1]["total"], reverse=True):
        companies.append({
            "company_name": company_name,
            "total": round(entry["total"], 2),
            "invoice_count": entry["count"],
            "latest_invoice": entry["latest_invoice"],
        })

    return {
        "total_invoices": sum(item["invoice_count"] for item in companies),
        "total_spend": round(sum(item["total"] for item in companies), 2),
        "company_count": len(companies),
        "companies": companies,
    }

# =====================================================
# HEALTH
# =====================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

# =====================================================
# UPLOAD PDF FOLDER
# =====================================================

@app.post("/upload-folder")
async def upload_folder(
    files: List[UploadFile] = File(...)
):

    uploaded = 0

    try:

        for file in files:

            if not file.filename.lower().endswith(".pdf"):
                continue

            filepath = os.path.join(
                INVOICE_FOLDER,
                os.path.basename(file.filename)
            )

            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(
                    file.file,
                    buffer
                )

            uploaded += 1

        return {
            "success": True,
            "uploaded": uploaded
        }


    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =====================================================
# PROCESS ALL INVOICES
# =====================================================

@app.post("/process-folder")
def process_invoices(db: Session = Depends(get_db)):

    try:

        print("Starting invoice processing...")

        result = process_folder(INVOICE_FOLDER)

        processed = result.get("processed_count", 0)
        duplicates = result.get("duplicates", [])

        print(f"Processed {processed} invoices")
        if duplicates:
            print(f"Skipped duplicates: {duplicates}")

        all_db_invoices = get_all_invoices(db)
        excel_rows = [
            {
                "Invoice Date": invoice.invoice_date,
                "Invoice Number": invoice.invoice_number,
                "Invoice Total": invoice.invoice_total,
                "Company Name": invoice.company_name,
                "Billing Address": invoice.billing_address,
                "Due Date": invoice.due_date,
                "Name": invoice.customer_name,
                "Reference No": invoice.reference_no,
                "Contract Number": invoice.contract_number,
                "PAN Number": invoice.pan_number,
                "Supplier GST": invoice.supplier_gst,
                "Buyer GST": invoice.buyer_gst,
                "Rate": invoice.rate,
                "CST Value": invoice.cst_value,
                "Currency": invoice.currency,
                "Delivery_and_Billing_Period": invoice.delivery_period,
                "Item Total": invoice.item_total,
                "Quantity": invoice.quantity,
                "Result": invoice.result,
                "File Path": invoice.file_path,
                "File Name": invoice.file_name,
            }
            for invoice in all_db_invoices
        ]

        export_to_excel(excel_rows)

        print("Excel exported successfully")

        return {
            "success": True,
            "processed": processed,
            "duplicates": duplicates,
            "download_url": "/download-excel"
        }

    except Exception as e:

        import traceback

        print("\n\n========== ERROR ==========")
        traceback.print_exc()
        print("===========================\n\n")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# =====================================================
# DOWNLOAD EXCEL
# =====================================================

@app.get("/download-excel")
def download_excel():

    excel_path = "output/invoices.xlsx"

    if not os.path.exists(excel_path):

        raise HTTPException(
            status_code=404,
            detail="Excel file not found"
        )

    return FileResponse(
        excel_path,
        filename="invoices.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Database dependencies and utilities moved to the top of the module.

# =====================================================
# EXCEPTION HANDLERS
# =====================================================

@app.exception_handler(sqlalchemy.exc.OperationalError)
def db_operational_error_handler(request: Request, exc: sqlalchemy.exc.OperationalError):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Database connection failure: {str(exc)}"}
    )

@app.exception_handler(sqlalchemy.exc.SQLAlchemyError)
def db_sqlalchemy_error_handler(request: Request, exc: sqlalchemy.exc.SQLAlchemyError):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Database error occurred: {str(exc)}"}
    )

# =====================================================
# LIST / RETRIEVE ALL INVOICES
# =====================================================

@app.get("/invoices")
def invoices(source: str = "db", db: Session = Depends(get_db)):
    if source == "files":
        pdfs = [
            file
            for file in os.listdir(INVOICE_FOLDER)
            if file.lower().endswith(".pdf")
        ]
        return {
            "count": len(pdfs),
            "files": pdfs
        }
    
    # Default is returning all invoices from the database
    db_invoices = get_all_invoices(db)
    return [serialize_invoice(inv) for inv in db_invoices]

# =====================================================
# DATABASE CRUD ENDPOINTS
# =====================================================

class InvoiceUpdate(BaseModel):
    invoice_number: str = None
    invoice_date: str = None
    invoice_total: str = None
    company_name: str = None
    billing_address: str = None
    due_date: str = None
    customer_name: str = None
    reference_no: str = None
    rate: str = None
    cst_value: str = None
    currency: str = None
    delivery_period: str = None
    item_total: str = None
    quantity: str = None
    contract_number: str = None
    pan_number: str = None
    supplier_gst: str = None
    buyer_gst: str = None
    file_path: str = None
    file_name: str = None
    result: str = None

@app.get("/invoice/{invoice_id}")
def get_single_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=404,
            detail=f"Invoice with ID {invoice_id} not found"
        )
    return serialize_invoice(invoice)

@app.delete("/invoice/{invoice_id}")
def delete_single_invoice(invoice_id: int, db: Session = Depends(get_db)):
    success = delete_invoice(db, invoice_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Invoice with ID {invoice_id} not found"
        )
    return {
        "success": True,
        "message": f"Invoice with ID {invoice_id} deleted successfully"
    }

@app.put("/invoice/{invoice_id}")
def update_single_invoice(invoice_id: int, invoice_update: InvoiceUpdate, db: Session = Depends(get_db)):
    current_invoice = get_invoice(db, invoice_id)
    if not current_invoice:
        raise HTTPException(
            status_code=404,
            detail=f"Invoice with ID {invoice_id} not found"
        )
        
    update_data = invoice_update.dict(exclude_unset=True)
    # Filter out None values
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    # Check for duplicates on update
    new_inv_num = update_data.get("invoice_number", current_invoice.invoice_number)
    new_comp_name = update_data.get("company_name", current_invoice.company_name)
    
    if new_inv_num and new_comp_name:
        existing = db.query(Invoice).filter(
            Invoice.invoice_number == new_inv_num,
            Invoice.company_name == new_comp_name,
            Invoice.id != invoice_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail="An invoice with the same invoice number and company name already exists"
            )
            
    updated = update_invoice(db, invoice_id, update_data)
    return serialize_invoice(updated)

# =====================================================
# SEARCH ENDPOINTS
# =====================================================

@app.get("/search/company/{company}")
def search_company(company: str, db: Session = Depends(get_db)):
    results = search_by_company(db, company)
    return [serialize_invoice(inv) for inv in results]

@app.get("/search/invoice/{invoice_number}")
def search_invoice(invoice_number: str, db: Session = Depends(get_db)):
    results = search_by_invoice_number(db, invoice_number)
    return [serialize_invoice(inv) for inv in results]

@app.get("/search/date/{date}")
def search_date(date: str, db: Session = Depends(get_db)):
    results = search_by_date(db, date)
    return [serialize_invoice(inv) for inv in results]