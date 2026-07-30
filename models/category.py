from sqlalchemy import Column, String, Integer
from .base import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nama = Column(String, unique=True, nullable=False)
    warna_hex = Column(String, default="#CBD5E1")
