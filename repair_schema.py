import psycopg2

conn = psycopg2.connect('dbname=invoice_db user=postgres password=Antihero@2023 host=localhost port=5432')
cur = conn.cursor()
for col in ['contract_number', 'pan_number', 'supplier_gst', 'buyer_gst']:
    cur.execute(f"ALTER TABLE invoices ADD COLUMN IF NOT EXISTS {col} VARCHAR;")
    print('ensured', col)
conn.commit()
cur.close()
conn.close()
