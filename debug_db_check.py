from database.connection import SessionLocal
from database.models import Invoice

session = SessionLocal()
try:
    count = session.query(Invoice).count()
    print('count=', count)
    if count > 0:
        sample = session.query(Invoice).first()
        print('sample:', sample.invoice_number, sample.company_name, sample.invoice_total, sample.file_name)
finally:
    session.close()
