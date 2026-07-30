from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class TransactionCreate(BaseModel):
    nominal: int = Field(gt=0)
    jenis: str  # 'income' or 'expense'
    kategori: str
    deskripsi: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    nominal: int
    jenis: str
    kategori: str
    deskripsi: Optional[str] = None
    waktu: datetime
    is_confirmed: int

class SummaryResponse(BaseModel):
    total_income: float
    total_expense: float
    by_category: Dict[str, float]

class BudgetResponse(BaseModel):
    kategori: str
    limit: float
    spent: float
    remaining: float
    percent: float