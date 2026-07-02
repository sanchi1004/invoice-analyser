import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from urllib.parse import quote_plus

# 1. HARDCODE your variables so we know exactly what is being sent
DB_USER = "postgres"
# Put the EXACT password you use to log into pgAdmin here:
DB_PASSWORD = "Antihero@2023" # (Change to "XX@2023" if that is your real password)
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "invoice_db"

# 2. REMOVE os.getenv from the URL so it doesn't accidentally load an old URL
DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

class Base(DeclarativeBase):
    pass