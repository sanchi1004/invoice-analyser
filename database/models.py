from sqlalchemy import Column, Integer, String, DateTime, func
from database.connection import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, nullable=True)
    invoice_date = Column(String, nullable=True)
    invoice_total = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    billing_address = Column(String, nullable=True)
    due_date = Column(String, nullable=True)
    customer_name = Column(String, nullable=True)
    reference_no = Column(String, nullable=True)
    rate = Column(String, nullable=True)
    cst_value = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    delivery_period = Column(String, nullable=True)
    item_total = Column(String, nullable=True)
    quantity = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    result = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())