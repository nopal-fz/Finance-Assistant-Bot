from fastmcp import FastMCP
from models import AsyncSessionLocal, Transaction
from services.transaction import get_filtered_transactions, get_summary as get_tx_summary
from services.budget import get_budget_usage
from datetime import datetime, timedelta
import calendar

mcp = FastMCP("Bot Kas Pribadi")

def parse_period(period: str):
    now = datetime.now()
    if period == "hari ini":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == "minggu ini":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == "bulan ini":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(now.year, now.month)[1]
        end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    else:
        # Fallback to bulan ini
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(now.year, now.month)[1]
        end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    return start, end

@mcp.tool()
async def get_transactions(period: str = "bulan ini", kategori: str = None, limit: int = 50):
    """
    Ambil daftar transaksi. 
    period: 'hari ini', 'minggu ini', 'bulan ini'.
    """
    start, end = parse_period(period)
    async with AsyncSessionLocal() as db:
        txs = await get_filtered_transactions(db, start, end, kategori, limit)
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

@mcp.tool()
async def get_summary(period: str = "bulan ini"):
    """
    Ringkasan pengeluaran dan pemasukan.
    period: 'hari ini', 'minggu ini', 'bulan ini'.
    """
    start, end = parse_period(period)
    async with AsyncSessionLocal() as db:
        summary = await get_tx_summary(db, start, end)
        return summary

@mcp.tool()
async def get_budget_status():
    """
    Cek status budget bulan ini.
    """
    async with AsyncSessionLocal() as db:
        status = await get_budget_usage(db)
        return status

if __name__ == "__main__":
    mcp.run()
