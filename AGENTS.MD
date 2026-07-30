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
- *Status:* Semua fitur PRD + perbaikan teknis selesai. Bot commands: `/start`, `/help`, `/laporan`, `/budget`, `/catat`, `/hapus`, `/batal`, `/kategori`. Category override via chat. Scheduler: laporan mingguan (Senin 09:00), laporan bulanan (tgl 1 09:00), reminder budget (Senin 10:00). Dashboard FastAPI + Chart.js + dark mode + auth middleware. MCP server 3 tools. Git init & push ke GitHub. Semua akses data via services layer. Pydantic schemas selesai. Error handler bot aktif.
- *Repo:* `https://github.com/nopal-fz/Finance-Assistant-Bot`
- *What's Next:* Tergantung kebutuhan — bisa tambah fitur baru, testing, deploy production, atau improvement NLP/dashboard.
