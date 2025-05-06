from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from pydantic import BaseModel

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    internal_id = Column(String) # z serwisu ktory rzada platnosci
    email = Column(String)
    amount = Column(Float)
    description = Column(String)
    tpay_transaction_id = Column(String)
    tpay_title = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


class CreatePaymentRequest(BaseModel):
    amount: float
    description: str
    email: str
