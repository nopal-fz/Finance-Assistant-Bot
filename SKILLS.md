# 🔧 Development Skills: Bot Kas Pribadi

Dokumen ini mendefinisikan skill development lokal untuk OpenCode agar bisa menyelesaikan proyek Bot Kas Pribadi secara efektif.

---

## Skill 1: `bot-kas-pribadi` (Primary)

**Tujuan:** Mengajarkan OpenCode konteks proyek secara menyeluruh.

### Project Structure
```
bot/               → Handler Telegram (MessageHandler, CommandHandler)
api/               → Router FastAPI + dashboard HTML/JS
services/          → Business logic (NLP parser, summary calc, budget check)
models/            → SQLAlchemy ORM models (Transaction, Category, Budget)
schemas/           → Pydantic v2 schemas (input/output validation)
mcp/               → FastMCP tool definitions (get_transactions, get_summary, get_budget_status)
.env               → Config: BOT_TOKEN, DASHBOARD_PASSWORD, DATABASE_URL
```

### Key Conventions (AGENTS.md)
- Type hints wajib di setiap fungsi Python.
- Single-user app: jangan buat struktur multi-user/multi-tenant.
- Semua akses data lewat `services/`, jangan query SQLAlchemy langsung dari bot handler.
- Format Rupiah via satu fungsi `format_idr()` di `services/helpers.py`.
- Parsing natural language di `services/nlp_parser.py`, return `ParsedTransaction` Pydantic model.
- Exception handler Telegram harus catch semua error + kirim pesan ramah.
- Logging: INFO untuk transaksi, ERROR untuk kegagalan sistem.

### NLP Parsing (services/nlp_parser.py)
- Input: string natural language (contoh: "abis makan 45rb", "gajian 5jt", "beli token listrik 100rb")
- Keluaran: `ParsedTransaction(nominal: int, jenis: 'income'|'expense', kategori: str, deskripsi: str, confidence: float)`
- Deteksi angka: "45rb" → 45000, "5jt" → 5000000, "100rb" → 100000
- Deteksi income/expense: keyword income (gajian, bonus, jual, dapet, terima), keyword expense (beli, bayar, makan, transport, isi)
- Kategori default: Makan, Transport, Tagihan, Hiburan, Belanja, Kesehatan, Lainnya — mapping keyword sederhana
- Confidence < 0.7 → bot wajib konfirmasi sebelum simpan

### Bot Handler (bot/handlers.py)
- python-telegram-bot v21 dengan Application.builder()
- MessageHandler non-command: all text → NLP parser → logika konfirmasi
- CommandHandler: /catat, /laporan, /kategori (fallback)
- error_handler: catch semua exception, log ke file

---

## Skill 2: `sqlalchemy-async`

### Tujuan: Memastikan OpenCode menulis query SQLAlchemy 2.0 async yang benar.

### Pola Utama
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_user_transaction(db: AsyncSession, limit: int = 50):
    stmt = select(Transaction).order_by(Transaction.tanggal.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
```

### Tips
- `await db.commit()` setelah `add()` / `update()`
- `select()` pakai `scalars()` untuk ambil objek
- `select().where().order_by()` pola standard untuk query
- `select(func.sum(), func.count())` untuk agregasi
- MySQL/PostgreSQL support: `case()` expressions, `extract()` untuk grouping

---

## Skill 3: `fastmcp-tool`

### Tujuan
Mengajarkan OpenCode cara mendefinisikan MCP tools dengan FastMCP.

### Pattern untuk `mcp/server.py`
```python
from fastmcp import FastMCP
mcp = FastMCP("Bot Kas Pribadi")

@mcp.tool()
async def get_transactions(period: str = "bulan ini", category: str | None = None):
    ...
```

### Testing
- Jalankan MCP server: `python mcp/server.py`
- Test dengan `fastmcp dev mcp/server.py` atau `mcp run mcp/server.py`
- Registrasi ke OpenCode via `.mcp.json` (di root)

### Parameters Convention
- `period`: "hari ini", "minggu ini", "bulan ini", "tahun ini", atau format "YYYY-MM-DD..YYYY-MM-DD"
- Gunakan timezone Jakarta (UTC+7)

---

## Skill 4: `telegram-bot-testing`

### Cara test bot lokal
```bash
python bot/main.py
```
Bot akan polling Telegram API. Kalau ada error koneksi, cek `BOT_TOKEN` di `.env`.

### Cara test handler unit
```python
async def test_catat_command():
    # Mock Update dan Context
    update = {update with .message.filters=...}
    context =
    await catat_command(update, context)
    # Assert pesan balasan berisi "Dicatat Rp 45.000 - Makan"
```

### Log yang harus diperhatikan
- `INFO: Transaksi masuk: Rp 45.000 Makan (expense)` ← di services.py
- `ERROR: Gagal menyimpan transaksi: <exception>` ← di models/ atau services/
