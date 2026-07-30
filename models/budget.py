from sqlalchemy import Column, Integer, String, Float, ForeignKey
from .base import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kategori = Column(String, nullable=False)
    limit_bulanan = Column(Float, nullable=False)
    bulan_aktif = Column(String, nullable=False) # Format: YYYY-MM
