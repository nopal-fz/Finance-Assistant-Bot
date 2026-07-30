from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from models import AsyncSessionLocal, Transaction, TransactionType
from models.base import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import calendar
import os
from services.budget import get_budget_usage

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

def get_password_header(request: Request):
    token = request.headers.get("Authorization") or request.query_params.get("token")
    if token and token.startswith("Bearer "):
        token = token[7:]
    if token != os.getenv("DASHBOARD_PASSWORD"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token

@app.get("/api/transactions")
async def get_transactions(request: Request, db: AsyncSession = Depends(get_db_session), _auth: str = Depends(get_password_header)):
    # Filter opsional: periode hari ini/minggu/bulan ini
    period = request.query_params.get("periode", "bulan ini")
    now = datetime.now()
    if period == "hari ini":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == "minggu ini":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:  # bulan ini
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(now.year, now.month)[1]
        end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

    stmt = select(Transaction).where(
        Transaction.timestamp >= start,
        Transaction.timestamp <= end,
        Transaction.is_confirmed == 1
    ).order_by(Transaction.timestamp.desc())

    res = await db.execute(stmt)
    txs = res.scalars().all()

    return [
        {
            "id": t.id,
            "nominal": t.nominal,
            "jenis": t.jenis.value,
            "kategori": t.kategori,
            "deskripsi": t.deskripsi,
            "waktu": t.timestamp.isoformat()
        } for t in txs
    ]

@app.get("/api/summary")
async def get_summary(request: Request, db: AsyncSession = Depends(get_db_session), _auth: str = Depends(get_password_header)):
    period = request.query_params.get("periode", "bulan ini")
    now = datetime.now()
    if period == "hari ini":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == "minggu ini":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(now.year, now.month)[1]
        end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

    stmt_income = select(func.sum(Transaction.nominal)).where(
        Transaction.jenis == TransactionType.INCOME,
        Transaction.timestamp >= start,
        Transaction.timestamp <= end,
        Transaction.is_confirmed == 1
    )
    stmt_expense = select(func.sum(Transaction.nominal)).where(
        Transaction.jenis == TransactionType.EXPENSE,
        Transaction.timestamp >= start,
        Transaction.timestamp <= end,
        Transaction.is_confirmed == 1
    )
    stmt_cat = select(Transaction.kategori, func.sum(Transaction.nominal)).where(
        Transaction.jenis == TransactionType.EXPENSE,
        Transaction.timestamp >= start,
        Transaction.timestamp <= end,
        Transaction.is_confirmed == 1
    ).group_by(Transaction.kategori)

    income_res = await db.execute(stmt_income)
    expense_res = await db.execute(stmt_expense)
    cat_res = await db.execute(stmt_cat)

    return {
        "total_income": income_res.scalar() or 0,
        "total_expense": expense_res.scalar() or 0,
        "by_category": dict(cat_res.all())
    }

@app.get("/")
async def get_dashboard(request: Request, _auth: str = Depends(get_password_header)):
    import aiofiles
    async with aiofiles.open("api/templates/index.html", encoding="utf-8") as f:
        html = await f.read()
    return HTMLResponse(html)

@app.get("/api/budget")
async def budget_status(request: Request, db: AsyncSession = Depends(get_db_session), _auth: str = Depends(get_password_header)):
    res = await get_budget_usage(db)
    return res
