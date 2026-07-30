# 📌 Project Memory & Rules: Bot Kas Pribadi (Telegram Personal Finance Tracker)

## 🛠 Tech Stack
- **Language & Runtime:** Python 3.11+
- **Framework & Libraries:** FastAPI (dashboard & API layer) / python-telegram-bot v21+ (bot handler, async) / Pydantic v2 (schema & validasi) / SQLAlchemy 2.0 (ORM, async) / FastMCP (MCP server) / APScheduler (laporan & reminder terjadwal) / Plotly atau Chart.js (visualisasi dashboard)
- **Database / Vector Store:** SQLite cukup untuk personal use (single user, single writer) — bisa upgrade ke PostgreSQL kalau nanti butuh multi-device sync yang lebih robust. Tidak butuh vector store.
- **Integrations / SDK:** python-telegram-bot / FastMCP (expose finance tools ke AI agent) / python-dotenv (config `.env`)

## 📐 Coding Rules & Conventions
- Selalu gunakan type hinting eksplisit pada fungsi Python.
- Utamakan modularitas: pisahkan `bot/` (handler Telegram), `api/` (router FastAPI + dashboard), `services/` (business logic: parsing NLP sederhana, kalkulasi summary, budget check), `models/` (SQLAlchemy models), `schemas/` (Pydantic schemas), `mcp/` (MCP tool definitions).
- Terapkan prinsip YAGNI & clean code — ini single-user app, jangan bangun struktur multi-user/multi-tenant yang tidak dibutuhkan.
- Semua akses data lewat `services/`, jangan query SQLAlchemy langsung dari handler bot atau router FastAPI.
- Error handling jelas: setiap exception di handler Telegram harus di-catch dan direspons dengan pesan ramah, bukan silent fail. Gunakan `logging` module dengan level yang informatif (INFO untuk transaksi masuk, ERROR untuk kegagalan sistem).
- Validasi input nominal & kategori di layer Pydantic schema sebelum masuk ke service layer.
- Format angka Rupiah konsisten lewat satu helper function (`format_idr()`), jangan duplikasi logic format di banyak tempat.
- Parsing natural language (deteksi nominal, jenis income/expense, kategori) taruh di service terpisah (`services/nlp_parser.py`) supaya gampang di-tes dan di-improve tanpa menyentuh handler bot.

## 📝 Current Progress & Architecture Status
- [x] Inisialisasi struktur folder proyek & virtual environment.
- [x] Setup file `.mcp.json` & `SKILLS.md` lokal.
- [x] Implementasi Database Model & Migration (Transaction, Category, Budget).
- [x] Implementasi Core Logic / Service Layer (parsing NLP nominal + kategori + jenis transaksi).
- [x] Implementasi API Endpoint / Bot Handler (natural language chat + konfirmasi simpan).
- [x] Implementasi MCP Server (tools: `get_transactions`, `get_summary`, `get_budget_status`).
- [x] Implementasi scheduler untuk laporan otomatis mingguan & reminder budget (saat save).
- [x] Implementasi dashboard frontend sederhana (FastAPI + Chart.js).
- [x] Testing & Validation (unit test service layer & manual bot testing).

## 🚀 Last Session Notes
- *Status:* Core flow (Input chat -> NLP Parser -> SQLite -> MCP), bot commands (`/laporan`, `/budget`, `/catat`, `/help`, `/hapus`, `/batal`), scheduler (laporan mingguan + budget alert saat save), Undo inline button, dashboard FastAPI + Chart.js, dan MCP server sudah selesai. Bot jalan via `python -m bot.main`, dashboard via `uvicorn api.main:app --reload`.
- *Remaining:* 
  1. **Category management** — `/kategori` command + CRUD kategori via bot.
  2. **Category override flow** — koreksi kategori pas konfirmasi tanpa cancel.
  3. **Monthly report scheduler** — cron awal bulan.
  4. **Periodic budget reminder** — scheduler mingguan cek budget >80%.
  5. **Historical comparison** — laporan banding periode sebelumnya.
  6. **Dashboard beautify** — redesign rapi, font Inter, responsive.
  7. **Pydantic schemas** — isi `schemas/` layer.
  8. **Refactor direct SQL** — pindah query dari `hapus`/`batal` ke `services/`.
  9. **`/api/budget` endpoint** — buat dashboard.
  10. **Bot error handler** — register `error_handler()`.
  11. **Clean stale files** — hapus `dashboard.html`, `static/app.js`, `static/style.css`.
  12. **Fix auth middleware** — pasang `Depends(get_password_header)`.
  13. **GitHub setup** — untrack `.env`, push repo.
  14. **Deployment guide** — verify & update README.
