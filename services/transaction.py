from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from models import Transaction, TransactionType
from services.nlp_parser import ParsedTransaction
from datetime import datetime, timedelta

async def create_transaction(db: AsyncSession, parsed: ParsedTransaction, confirmed: bool = False):
    new_tx = Transaction(
        nominal=parsed.nominal,
        jenis=TransactionType.INCOME if parsed.jenis == "income" else TransactionType.EXPENSE,
        kategori=parsed.kategori,
        deskripsi=parsed.deskripsi,
        is_confirmed=1 if confirmed else 0
    )
    db.add(new_tx)
    await db.commit()
    await db.refresh(new_tx)
    return new_tx

async def get_summary(db: AsyncSession, start_date: datetime, end_date: datetime):
    # Total Income
    income_stmt = select(func.sum(Transaction.nominal)).where(
        Transaction.jenis == TransactionType.INCOME,
        Transaction.timestamp >= start_date,
        Transaction.timestamp <= end_date,
        Transaction.is_confirmed == 1
    )
    # Total Expense
    expense_stmt = select(func.sum(Transaction.nominal)).where(
        Transaction.jenis == TransactionType.EXPENSE,
        Transaction.timestamp >= start_date,
        Transaction.timestamp <= end_date,
        Transaction.is_confirmed == 1
    )
    # Group by Category
    category_stmt = select(Transaction.kategori, func.sum(Transaction.nominal)).where(
        Transaction.timestamp >= start_date,
        Transaction.timestamp <= end_date,
        Transaction.is_confirmed == 1,
        Transaction.jenis == TransactionType.EXPENSE
    ).group_by(Transaction.kategori)
    
    income_res = await db.execute(income_stmt)
    expense_res = await db.execute(expense_stmt)
    category_res = await db.execute(category_stmt)
    
    return {
        "total_income": income_res.scalar() or 0,
        "total_expense": expense_res.scalar() or 0,
        "by_category": dict(category_res.all())
    }

async def get_filtered_transactions(db: AsyncSession, start_date: datetime = None, end_date: datetime = None, kategori: str = None, limit: int = 50):
    stmt = select(Transaction).where(Transaction.is_confirmed == 1)
    if start_date:
        stmt = stmt.where(Transaction.timestamp >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.timestamp <= end_date)
    if kategori:
        stmt = stmt.where(Transaction.kategori == kategori)
    
    stmt = stmt.order_by(Transaction.timestamp.desc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()

async def delete_transaction(db: AsyncSession, tx_id: int):
    stmt = delete(Transaction).where(Transaction.id == tx_id)
    res = await db.execute(stmt)
    await db.commit()
    return res.rowcount > 0

async def get_last_transaction(db: AsyncSession):
    stmt = select(Transaction).order_by(Transaction.id.desc()).limit(1)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()
