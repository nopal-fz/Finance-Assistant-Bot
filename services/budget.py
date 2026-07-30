from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models import Budget, Transaction, TransactionType
from datetime import datetime
from sqlalchemy.sql import func

async def set_budget(db: AsyncSession, kategori: str, limit: float, bulan: str = None):
    """
    Set or update budget for a category and month.
    bulan format: YYYY-MM. Defaults to current month.
    """
    if not bulan:
        bulan = datetime.now().strftime("%Y-%m")
    
    stmt = select(Budget).where(
        and_(Budget.kategori == kategori, Budget.bulan_aktif == bulan)
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    
    if existing:
        existing.limit_bulanan = limit
    else:
        new_budget = Budget(kategori=kategori, limit_bulanan=limit, bulan_aktif=bulan)
        db.add(new_budget)
    
    await db.commit()
    return True

async def get_budget_usage(db: AsyncSession, bulan: str = None):
    """
    Get all budgets and their current usage for a specific month.
    """
    if not bulan:
        bulan = datetime.now().strftime("%Y-%m")
    
    # 1. Get all budgets for the month
    budget_stmt = select(Budget).where(Budget.bulan_aktif == bulan)
    budget_res = await db.execute(budget_stmt)
    budgets = budget_res.scalars().all()
    
    # 2. Get current expenses per category for the month
    # Parse month start/end
    start_date = datetime.strptime(f"{bulan}-01", "%Y-%m-%d")
    if start_date.month == 12:
        end_date = datetime(start_date.year + 1, 1, 1)
    else:
        end_date = datetime(start_date.year, start_date.month + 1, 1)
        
    usage_stmt = select(Transaction.kategori, func.sum(Transaction.nominal)).where(
        and_(
            Transaction.jenis == TransactionType.EXPENSE,
            Transaction.timestamp >= start_date,
            Transaction.timestamp < end_date,
            Transaction.is_confirmed == 1
        )
    ).group_by(Transaction.kategori)
    
    usage_res = await db.execute(usage_stmt)
    usage_dict = {k: v for k, v in usage_res.all()}
    
    results = []
    for b in budgets:
        spent = usage_dict.get(b.kategori, 0)
        results.append({
            "kategori": b.kategori,
            "limit": b.limit_bulanan,
            "spent": spent,
            "remaining": b.limit_bulanan - spent,
            "percent": (spent / b.limit_bulanan * 100) if b.limit_bulanan > 0 else 0
        })
    return results
