# Bot Kas Pribadi

Bot Telegram personal finance tracker. Catat pemasukan/pengeluaran via chat biasa, lihat laporan, atur budget, dan dashboard visual.

## Fitur

- **Natural Language Chat** — `makan 45rb`, `gajian 5jt`, bot auto-detect nominal, kategori, jenis.
- **Kategorisasi Otomatis** — Makan, Transport, Tagihan, dll. Koreksi via chat (ketik nama kategori pas konfirmasi).
- **Laporan** — `/laporan` ringkasan harian/mingguan/bulanan + perbandingan dengan periode sebelumnya.
- **Budget** — `/budget Makan 2000000` atur limit bulanan, bot kirim peringatan (pas simpan + reminder mingguan).
- **Kelola Kategori** — `/kategori` lihat/tambah/hapus kategori custom.
- **Hapus** — `/hapus {id}` atau `/batal` (hapus transaksi terakhir) + tombol Undo.
- **Scheduler** — Laporan mingguan (Senin 09:00), laporan bulanan (tgl 1), reminder budget (Senin 10:00).
- **Dashboard** — Grafik interaktif FastAPI + Chart.js, dark mode toggle, Inter font, responsive.
- **MCP Server** — Tools `get_transactions`, `get_summary`, `get_budget_status` untuk AI agent.

## Kategori Transaksi

Bot auto-detect kategori dari chat. Berikut daftar kategori default:

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
| Lainnya | (default jika tidak cocok) |

### Pemasukan (Income)
| Kategori | Contoh Chat |
|----------|------------|
| Gaji | `gajian 5jt`, `bonus 2jt` |
| Lainnya | `jual 200rb`, `dapet 50rb` |

Kustomisasi: `/kategori tambah [nama]` atau `/kategori hapus [nama]`.

## Persyaratan

- Python 3.11+
- Bot Telegram ([buat via @BotFather](https://t.me/BotFather))
- Pip / venv

## Instalasi & Setup

```bash
# Clone
git clone https://github.com/nopal-fz/Finance-Assistant-Bot.git bot-kas-pribadi
cd bot-kas-pribadi

# Virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
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
TELEGRAM_USER_CHAT_ID=          # (opsional, isi setelah bot jalan sekali)
```

Database SQLite (`bot_kemas.db`) auto-created saat pertama kali bot/dashboard jalan. Backup cukup kopi file ini.

## Cara Jalankan

Butuh **2 terminal** terpisah — satu buat bot, satu buat dashboard.

### Terminal 1: Bot Telegram
```bash
python -m bot.main
```
Bot siap di-chat di Telegram. Database `bot_kemas.db` auto-created.

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
Bot akan konfirmasi dulu sebelum simpan.

**Koreksi kategori (override):** kalau kategori salah tebak, tinggal ketik nama kategori yang bener pas muncul tombol Simpan — bot akan update tanpa perlu cancel & ulang.
```
User: grab 20k
Bot: Dicatat Rp 20.000 - Transport. Simpan? [Ya] [Salah]
User: Makan              ← override kategori
Bot: Kategori diubah ke Makan. Simpan? [Ya] [Salah]
```

**Undo:** setelah klik Simpan, ada tombol "↩️ Undo" untuk hapus transaksi terakhir yang baru disimpan.

**Perintah:**
| Perintah | Contoh | Fungsi |
|----------|--------|--------|
| `/start` | — | Mulai, dapat sapaan random |
| `/catat` | `/catat 50000 Makan Nasi Goreng` | Input manual |
| `/laporan` | — | Ringkasan (pilih periode) |
| `/budget` | `/budget Makan 2000000` | Set limit bulanan |
| `/hapus` | `/hapus 3` | Hapus transaksi by ID |
| `/batal` | — | Hapus transaksi terakhir |
| `/kategori` | `/kategori` atau `/kategori tambah Makanan` | Lihat/tambah/hapus kategori |
| `/help` | — | Panduan lengkap |

**Budget alert:** otomatis dikirim saat simpan transaksi kalau pengeluaran kategori sudah ≥80% limit. ≥100% dapat alert merah (`⚠️ Melebihi limit`). Juga ada reminder setiap Senin jam 10:00 via scheduler.

## Struktur Proyek

```
bot/            → Handler Telegram (message, commands, callback)
api/            → FastAPI router + dashboard HTML
services/       → Business logic (NLP parser, transaction, budget)
models/         → SQLAlchemy ORM (Transaction, Category, Budget)
schemas/        → Pydantic v2 schemas
mcp/            → FastMCP tools (get_transactions, get_summary, get_budget_status)
```

## Dashboard

Dashboard menampilkan:
- Grafik batang pemasukan vs pengeluaran
- Pie chart distribusi kategori
- Daftar transaksi terbaru
- Dark mode (toggle tombol di pojok kanan atas)

Akses: `http://127.0.0.1:8000/?token=your_password`

## MCP Tools

Terintegrasi dengan AI agent via FastMCP:
- `get_transactions(period, kategori?)` — daftar transaksi
- `get_summary(period)` — ringkasan income/expense
- `get_budget_status()` — status budget bulan ini

## Catatan

- Single-user, data pribadi di SQLite.
- Tanpa LLM — parsing pake regex sederhana (ringan & cepat).
- Timezone: Asia/Jakarta.

## Deployment

### Railway (Recommended)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login & deploy
railway login
railway init
railway up

# Set environment variables di dashboard Railway:
# BOT_TOKEN, DASHBOARD_PASSWORD, DATABASE_URL=sqlite+aiosqlite:///bot_kemas.db
```

### Fly.io
```bash
fly launch
fly secrets set BOT_TOKEN=xxx DASHBOARD_PASSWORD=xxx
fly deploy
```

### VPS (systemd + nginx)
```bash
# 1. Clone & setup di server
git clone <repo> /opt/bot-kas
cd /opt/bot-kas
python -m venv .venv
pip install -r requirements.txt

# 2. Buat systemd service (/etc/systemd/system/bot-kas.service)
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

# 3. Buat systemd untuk dashboard
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

# 4. nginx reverse proxy (/etc/nginx/sites-available/bot-kas)
server {
    listen 80;
    server_name domainkamu.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 5. Enable & start
sudo systemctl enable bot-kas bot-kas-dash
sudo systemctl start bot-kas bot-kas-dash
```