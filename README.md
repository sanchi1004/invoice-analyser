# Invoice Analyser

Invoice Analyser extracts text and structured data from invoice PDFs and exports results to Excel and other formats.

## What it does
- Converts PDFs to images and/or text using OCR.  
- Extracts invoice fields (vendor, date, total, line items) via heuristics and rules.  
- Exports structured results to Excel and saves raw outputs in `output/`.

## Repo layout
- `main.py` — project entry point.  
- `src/` — core modules:
  - `excel_exporter.py` — Excel export helpers
  - `extractor.py` — extraction logic
  - `ocr_engine.py` — OCR wrapper
  - `pdf_converter.py` — PDF → images/text helpers
- `invoices/` — sample input PDFs.  
- `output/` — processed outputs.  
- `tests/` — unit/integration tests.

## Why use a virtual environment
- Keeps project dependencies isolated from your system Python.  
- Makes installs reproducible for collaborators and CI.  
- Avoids version conflicts between projects.

## Quick setup (recommended)
1. Create and activate a virtual environment (recommended name: `.venv`).

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (CMD):
```cmd
python -m venv .venv
.venv\\Scripts\\activate
```

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
```

2. Upgrade pip and install dependencies:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Run the project (example):
```bash
python main.py
```

4. Run tests:
```bash
pytest
```

5. Deactivate and remove the venv when finished:
```bash
deactivate
# macOS/Linux
rm -rf .venv
# Windows
rmdir /s .venv
```

## Notes
- Add `.venv/` to `.gitignore` so the environment isn't committed.  
- If you need exact OS-level parity (system packages, libraries), consider Docker instead.
