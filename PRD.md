# 📋 Product Requirement Document (PRD): Bot Kas Pribadi (Telegram Personal Finance Tracker)

## 🎯 Goal & Objective
Membuat bot Telegram yang mencatat pemasukan dan pengeluaran pribadi lewat chat biasa (natural language), tanpa perlu buka aplikasi lain atau input manual di spreadsheet. Data yang tercatat divisualisasikan lewat dashboard web (FastAPI) dan bisa diakses oleh AI agent lewat MCP Server untuk analisis on-demand (misal "berapa pengeluaranku bulan ini" atau "kategori mana yang paling boros").

## 👥 User & Core Features
- **Target User / Context:** 1 user pribadi + 1 bot, di chat personal (DM) dengan bot. Tidak ada konsep multi-user, grup, atau berbagi data — murni personal finance tracker.
- **Key Features:**
  1. **Pencatatan transaksi via chat natural language** — cara utama pakai bot ini adalah ngobrol biasa (misal "abis makan 45rb", "gajian 5jt", "beli token listrik 100rb"). Bot mem-parsing nominal, jenis (pemasukan/pengeluaran), dan kategori dari kalimat, lalu konfirmasi singkat sebelum menyimpan.
  2. **Kategorisasi otomatis + manual override** — bot menebak kategori dari konteks kalimat (Makan, Transport, Tagihan, Hiburan, Belanja, Kesehatan, Lainnya), user bisa koreksi langsung di chat kalau salah tebak.
  3. **Dashboard FastAPI** — halaman web pribadi menampilkan grafik pengeluaran per kategori, tren bulanan, perbandingan pemasukan vs pengeluaran.
  4. **MCP Server integration** — mengekspos data keuangan (transaksi, ringkasan, breakdown kategori) sebagai MCP tools, sehingga AI agent (Claude/Cursor, dsb) bisa melakukan query & analisis natural language terhadap data tanpa akses langsung ke database.
  5. **Laporan otomatis** — ringkasan mingguan/bulanan dikirim otomatis oleh bot (total pemasukan/pengeluaran, breakdown kategori, kategori yang naik/turun dibanding periode sebelumnya).
  6. **Reminder budget** — notifikasi kalau pengeluaran kategori tertentu mendekati/melewati limit bulanan yang di-set sendiri.
  7. **Manajemen kategori** — kategori default + kemampuan menambah/edit kategori custom.

## 📐 Business Rules & Logic
- **Cara interaksi utama: natural language chat**, bukan command. Contoh alur:
  - User: "abis makan 45rb" → bot: "Dicatat Rp 45.000 - Makan. Betul?" — user cukup balas biasa kalau ada koreksi (misal "salah, itu transport").
  - User: "gajian 5jt" → bot mendeteksi ini pemasukan, bukan pengeluaran, dan mencatat sebagai income.
  - Kalau bot ragu soal kategori atau jenis transaksi (income/expense), bot **selalu konfirmasi dulu**, tidak pernah asumsi sepihak.
- **Command sebagai fallback teknis** (opsional, tidak wajib dihafal): `/catat [jumlah] [kategori] [keterangan]`, `/laporan [minggu|bulan]`, `/kategori` (kelola kategori) — tersedia untuk kasus parsing natural language gagal atau user lebih suka ketik command langsung.
- **Mata uang & format angka:** Rupiah (IDR), format ribuan gaya Indonesia (misal `Rp 45.000`), tanpa desimal.
- **Kategori:** daftar default bisa dikustomisasi bebas oleh user.
- **Validasi transaksi:** nominal harus > 0, kategori harus terdaftar (atau auto-create jika user konfirmasi), setiap transaksi menyimpan timestamp dan jenis (`income`/`expense`).
- **Dashboard akses:** dashboard FastAPI dilindungi otentikasi sederhana (token/login), karena ini data finansial pribadi.
- **MCP tools yang diekspos (minimal):**
  - `get_transactions(period, category?)` — ambil daftar transaksi.
  - `get_summary(period)` — ringkasan total & breakdown kategori, pemasukan vs pengeluaran.
  - `get_budget_status(category?)` — status pengeluaran terhadap limit budget yang di-set.
