from database.connection import engine

print('PYTHON:', __import__('sys').executable)
print('ENGINE URL:', engine.url)
try:
    with engine.connect() as conn:
        print('DB connection ok')
except Exception as exc:
    print('DB connection failed:', exc)
