from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from .base import Base
import enum

class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nominal = Column(Integer, nullable=False)
    jenis = Column(Enum(TransactionType), nullable=False)
    kategori = Column(String, nullable=False)
    deskripsi = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_confirmed = Column(Integer, default=0) # 0: pending, 1: confirmed
