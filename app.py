from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from typing import List
import shutil
import os
import traceback

from pydantic import BaseModel
from sqlalchemy.orm import Session
import sqlalchemy.exc

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

# 4. Create the tables in PostgreSQL
Base.metadata.create_all(bind=engine)

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
# HOME PAGE
# =====================================================

@app.get("/")
def root():
    return FileResponse("templates/index.html")

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
def process_invoices():

    try:

        print("Starting invoice processing...")

        invoices = process_folder(INVOICE_FOLDER)

        print(f"Processed {len(invoices)} invoices")

        export_to_excel(invoices)

        print("Excel exported successfully")

        return {
            "success": True,
            "processed": len(invoices),
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
        "file_path": invoice.file_path,
        "file_name": invoice.file_name,
        "result": invoice.result,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None
    }

# =====================================================
# EXCEPTION HANDLERS
# =====================================================

@app.exception_handler(sqlalchemy.exc.OperationalError)
def db_operational_error_handler(request: Request, exc: sqlalchemy.exc.OperationalError):
    return JSONResponse(
        status_code=500,
        content={"detail": "Database connection failure"}
    )

@app.exception_handler(sqlalchemy.exc.SQLAlchemyError)
def db_sqlalchemy_error_handler(request: Request, exc: sqlalchemy.exc.SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred"}
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