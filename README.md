# Bot Kas Pribadi

Bot Telegram buat catat pemasukan/pengeluaran lewat chat biasa. Lengkap dengan laporan otomatis, budget tracker, dashboard web, dan MCP server.

## Fitur

- **Natural Language Chat** - `makan 45rb`, `gajian 5jt`. Bot auto-detect nominal, kategori, jenis transaksi.
- **Kategorisasi Otomatis** - Makan, Transport, Tagihan, dll. Koreksi kategori cukup ketik nama pas konfirmasi.
- **Laporan** - `/laporan` ringkasan harian/mingguan/bulanan + perbandingan sama periode sebelumnya.
- **Budget** - `/budget Makan 2000000` set limit bulanan. Dapat peringatan pas simpan + reminder mingguan.
- **Kelola Kategori** - `/kategori` buat lihat/tambah/hapus kategori custom.
- **Hapus** - `/hapus {id}`, `/batal` (hapus transaksi terakhir), atau tombol Undo habis simpan.
- **Scheduler** - Laporan mingguan (Senin 09:00), laporan bulanan (tgl 1), reminder budget (Senin 10:00).
- **Dashboard** - FastAPI + Chart.js. Dark mode, Inter font, responsive. Layout grid 2:1:1.
- **MCP Server** - 3 tools buat AI agent: `get_transactions`, `get_summary`, `get_budget_status`.
- **Sapaan Ramah** - Groq Llama-3.3-70b buat jawab sapaan kayak "halo", "pagi" secara natural.

## Kategori Transaksi

Bot auto-detect kategori dari chat.

### Pengeluaran (Expense)
| Kategori | Contoh Chat |
|----------|------------|
| Makan | `makan siang 45rb`, `kopi 20rb`, `go-food 50rb` |
| Transport | `bensin 100rb`, `ojol 15rb`, `tol 25rb` |
| Tagihan | `token listrik 200rb`, `pulsa 50rb`, `wifi 150rb` |
| Hiburan | `nonton 50rb`, `netflix 120rb`, `game 30rb` |
| Belanja | `beli baju 200rb`, `shopee 75rb`, `indomaret 45rb` |
| Kesehatan | `obat 30rb`, `dokter 200rb` |
| Pendidikan | `buku 100rb`, `kursus 500rb` |
| Hutang | `bayar utang 50rb`, `cicilan 200rb` |
| Piutang | `pinjemin andi 100k` |
| Transfer | `transfer ke ortu 200rb` |
| Lainnya | (default kalo nggak cocok) |

### Pemasukan (Income)
| Kategori | Contoh Chat |
|----------|------------|
| Gaji | `gajian 5jt`, `bonus 2jt` |
| Piutang | `balikin utang 100k` (deteksi otomatis dari konteks) |
| Lainnya | `jual 200rb`, `dapet 50rb` |

Tambah/hapus kategori: `/kategori tambah [nama]` atau `/kategori hapus [nama]`.

## Persyaratan

- Python 3.11+
- Bot Telegram ([buat via @BotFather](https://t.me/BotFather))
- Pip / venv

## Instalasi

```bash
# Clone
git clone https://github.com/nopal-fz/Finance-Assistant-Bot.git bot-kas-pribadi
cd bot-kas-pribadi

# Virtual environment
python -m venv .venv
.venv\Scripts\activate    # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Buat .env dari template
cp .env.example .env
```

Edit `.env`:
```
BOT_TOKEN=isi_token_dari_botfather
DASHBOARD_PASSWORD=ganti_password_aman
GROQ_API_KEY=isi_api_key_groq          # buat sapaan ramah
TELEGRAM_USER_CHAT_ID=                  # opsional, isi setelah bot jalan sekali
```

Database SQLite (`bot_kemas.db`) auto-created pertama kali bot/dashboard jalan. Backup cukup copy file ini.

## Cara Jalankan

Butuh 2 terminal terpisah (bot + dashboard).

### Terminal 1: Bot
```bash
python -m bot.main
```

### Terminal 2: Dashboard (opsional)
```bash
uvicorn api.main:app --reload
```
Buka `http://127.0.0.1:8000/?token=your_password`

## Cara Pakai Bot

**Chat biasa (rekomendasi):**
```
makan siang 45rb
gajian 5jt
beli token listrik 100rb
```

Bot konfirmasi dulu sebelum simpan.

**Koreksi kategori:** kalo kategori salah tebak, ketik nama kategori yang bener pas tombol Simpan muncul. Bot update tanpa perlu cancel & ulang.
```
User: grab 20k
Bot: Dicatat Rp 20.000 - Transport. Simpan? [Ya] [Salah]
User: Makan
Bot: Kategori diubah ke Makan. Simpan? [Ya] [Salah]
```

**Undo:** habis klik Simpan, ada tombol Undo buat hapus transaksi terakhir.

**Perintah:**
| Perintah | Contoh | Fungsi |
|----------|--------|--------|
| `/start` | - | Mulai, dapat sapaan random |
| `/catat` | `/catat 50000 Makan Nasi Goreng` | Input manual |
| `/laporan` | - | Ringkasan (pilih periode) |
| `/budget` | `/budget Makan 2000000` | Set limit bulanan |
| `/hapus` | `/hapus 3` | Hapus transaksi by ID |
| `/batal` | - | Hapus transaksi terakhir |
| `/kategori` | `/kategori` atau `/kategori tambah Makanan` | Lihat/tambah/hapus kategori |
| `/help` | - | Panduan lengkap |

**Budget alert:** otomatis dikirim pas simpan transaksi kalo pengeluaran kategori >= 80% limit. >= 100% dapet alert merah. Ada reminder tiap Senin jam 10:00.

## Struktur Proyek

```
bot/            Handler Telegram (message, commands, callback)
api/            FastAPI router + dashboard HTML
services/       Business logic (NLP parser, transaction, budget, LLM)
models/         SQLAlchemy ORM (Transaction, Category, Budget)
schemas/        Pydantic v2 schemas
mcp/            FastMCP tools
```

## Dashboard

Isi:
- Grafik batang pemasukan vs pengeluaran
- Pie chart distribusi kategori
- Daftar transaksi terbaru
- Dark mode toggle

Akses: `http://127.0.0.1:8000/?token=your_password`

## MCP Tools

Integrasi AI agent via FastMCP:
- `get_transactions(period, kategori?)` - daftar transaksi
- `get_summary(period)` - ringkasan income/expense
- `get_budget_status()` - status budget bulan ini

## Catatan

- Single-user, data di SQLite.
- Parsing pake regex (cepat, tanpa LLM). LLM cuma buat sapaan.
- Timezone Asia/Jakarta.

## Deployment

### Railway (Recommended)
```bash
npm i -g @railway/cli
railway login
railway init
railway up
```
Set env di dashboard Railway: `BOT_TOKEN`, `DASHBOARD_PASSWORD`, `GROQ_API_KEY`, `DATABASE_URL=sqlite+aiosqlite:///bot_kemas.db`.

### Fly.io
```bash
fly launch
fly secrets set BOT_TOKEN=xxx DASHBOARD_PASSWORD=xxx GROQ_API_KEY=xxx
fly deploy
```

### VPS (systemd + nginx)
```bash
# Clone & setup
git clone <repo> /opt/bot-kas
cd /opt/bot-kas
python -m venv .venv
pip install -r requirements.txt

# systemd service buat bot
# /etc/systemd/system/bot-kas.service
[Unit]
Description=Bot Kas Pribadi
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/bot-kas
EnvironmentFile=/opt/bot-kas/.env
ExecStart=/opt/bot-kas/.venv/bin/python -m bot.main
Restart=always

[Install]
WantedBy=multi-user.target

# systemd service buat dashboard
# /etc/systemd/system/bot-kas-dash.service
[Unit]
Description=Bot Kas Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/bot-kas
EnvironmentFile=/opt/bot-kas/.env
ExecStart=/opt/bot-kas/.venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

# nginx reverse proxy
# /etc/nginx/sites-available/bot-kas
server {
    listen 80;
    server_name domainkamu.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable & start
sudo systemctl enable bot-kas bot-kas-dash
sudo systemctl start bot-kas bot-kas-dash
```

## Groq API Key (untuk Sapaan Ramah)

Buat dapetin API Key:
1. Daftar di https://console.groq.com
2. Generate API key
3. Masukin ke `.env`: `GROQ_API_KEY=key_kamu`

Bot pake `llama-3.3-70b-versatile`. Gratis. Cuma dipake kalo user chat tanpa nominal transaksi (sapaan, obrolan ringan).
