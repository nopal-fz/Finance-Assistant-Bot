from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
import csv
import io
from models import AsyncSessionLocal, Transaction, TransactionType
from models.base import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import calendar
import os
from services.budget import get_budget_usage

from dotenv import load_dotenv
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_project_root, ".env"))

app = FastAPI()

@app.on_event("startup")
async def startup():
    from models import init_db
    await init_db()

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

def get_password_header(request: Request):
    password = os.getenv("DASHBOARD_PASSWORD")
    if not password:
        return None
    token = request.headers.get("Authorization") or request.query_params.get("token")
    if token and token.startswith("Bearer "):
        token = token[7:]
    if token != password:
        raise HTTPException(status_code=401, detail="Unauthorized. Pass ?token=xxx or Authorization header.")
    return token

def parse_period(periode: str, tahun: int = None, bulan: int = None, start_date: str = None, end_date: str = None):
    now = datetime.now()
    if periode == "hari ini":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif periode == "minggu ini":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif periode == "range" and start_date and end_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            ed = datetime.strptime(end_date, "%Y-%m-%d")
            if sd > ed:
                sd, ed = ed, sd
            start = sd.replace(hour=0, minute=0, second=0, microsecond=0)
            end = ed.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day = calendar.monthrange(now.year, now.month)[1]
            end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    elif periode == "custom" and tahun and bulan and 1 <= bulan <= 12 and 1900 <= tahun <= 2100:
        start = datetime(tahun, bulan, 1, 0, 0, 0, 0)
        last_day = calendar.monthrange(tahun, bulan)[1]
        end = datetime(tahun, bulan, last_day, 23, 59, 59, 999999)
    else:  # bulan ini atau fallback
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(now.year, now.month)[1]
        end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    return start, end

@app.get("/api/transactions")
async def get_transactions(request: Request, db: AsyncSession = Depends(get_db_session), _auth: str = Depends(get_password_header)):
    period = request.query_params.get("periode", "bulan ini")
    tahun = request.query_params.get("tahun")
    bulan = request.query_params.get("bulan")
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")
    
    tahun_int = int(tahun) if tahun and tahun.isdigit() else None
    bulan_int = int(bulan) if bulan and bulan.isdigit() else None
    
    start, end = parse_period(period, tahun_int, bulan_int, start_date, end_date)

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
    tahun = request.query_params.get("tahun")
    bulan = request.query_params.get("bulan")
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")
    
    tahun_int = int(tahun) if tahun and tahun.isdigit() else None
    bulan_int = int(bulan) if bulan and bulan.isdigit() else None
    
    start, end = parse_period(period, tahun_int, bulan_int, start_date, end_date)

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
    async with aiofiles.open(os.path.join(_project_root, "api", "templates", "index.html"), encoding="utf-8") as f:
        html = await f.read()
    return HTMLResponse(html)

@app.get("/api/export")
async def export_csv(request: Request, db: AsyncSession = Depends(get_db_session), _auth: str = Depends(get_password_header)):
    period = request.query_params.get("periode", "bulan ini")
    tahun = request.query_params.get("tahun")
    bulan = request.query_params.get("bulan")
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")

    tahun_int = int(tahun) if tahun and tahun.isdigit() else None
    bulan_int = int(bulan) if bulan and bulan.isdigit() else None

    start, end = parse_period(period, tahun_int, bulan_int, start_date, end_date)

    stmt = select(Transaction).where(
        Transaction.timestamp >= start,
        Transaction.timestamp <= end,
        Transaction.is_confirmed == 1
    ).order_by(Transaction.timestamp.asc())
    res = await db.execute(stmt)
    txs = res.scalars().all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Tanggal", "Jenis", "Kategori", "Deskripsi", "Nominal", "ID"])
    for t in txs:
        writer.writerow([
            t.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            t.jenis.value,
            t.kategori,
            t.deskripsi or "",
            t.nominal,
            t.id,
        ])

    filename = f"transactions_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/budget")
async def budget_status(request: Request, db: AsyncSession = Depends(get_db_session), _auth: str = Depends(get_password_header)):
    res = await get_budget_usage(db)
    return res

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)
