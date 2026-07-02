import psycopg2

conn = psycopg2.connect('dbname=invoice_db user=postgres password=Antihero@2023 host=localhost port=5432')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='invoices' ORDER BY ordinal_position;")
cols = cur.fetchall()
print(cols)
conn.close()
