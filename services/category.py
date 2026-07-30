from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models import Category

async def list_categories(db: AsyncSession):
    stmt = select(Category).order_by(Category.nama)
    res = await db.execute(stmt)
    return res.scalars().all()

async def add_category(db: AsyncSession, nama: str, warna_hex: str = "#CBD5E1"):
    existing = await db.execute(select(Category).where(Category.nama == nama))
    if existing.scalar_one_or_none():
        return False
    cat = Category(nama=nama, warna_hex=warna_hex)
    db.add(cat)
    await db.commit()
    return True

async def delete_category(db: AsyncSession, nama: str):
    stmt = delete(Category).where(Category.nama == nama)
    res = await db.execute(stmt)
    await db.commit()
    return res.rowcount > 0