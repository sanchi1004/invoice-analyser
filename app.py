from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from typing import List
import shutil
import os
import traceback

from src.batch_processor import process_folder
from src.excel_exporter import export_to_excel

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
# LIST FILES
# =====================================================

@app.get("/invoices")
def invoices():

    pdfs = [
        file
        for file in os.listdir(INVOICE_FOLDER)
        if file.lower().endswith(".pdf")
    ]

    return {
        "count": len(pdfs),
        "files": pdfs
    }