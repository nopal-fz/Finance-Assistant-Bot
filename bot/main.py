import logging
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv

from services.nlp_parser import parse_transaction
from services.transaction import create_transaction, get_summary, delete_transaction, get_last_transaction
from services.budget import set_budget, get_budget_usage
from services.category import list_categories, add_category, delete_category
from services.helpers import format_idr
from models import AsyncSessionLocal
from datetime import datetime, timedelta
import calendar
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

GREETINGS = [
    "Halo! Ada pemasukan atau pengeluaran hari ini?",
    "Eh, ada transaksi baru nih? Langsung chat aja, ya.",
    "Hai! Catat keuangan yuk. Contoh: 'makan siang 45rb'",
    "Halo! Siap bantu catat uang masuk/keluar kamu.",
    "Hey! Keuangan hari ini gimana? Catat yuk biar rapi.",
]

HELP_TEXT = (
    "*Bot Kas Pribadi — Panduan Cepat*\n\n"
    "*Cara Chat Biasa (Rekomendasi):*\n"
    "Langsung chat: `beli nasi 25rb`, `gajian 5jt`\n"
    "Bot auto-detect nominal, kategori & jenis.\n\n"
    "*Perintah:*\n"
    "📊 /laporan — Ringkasan (hari/minggu/bulan)\n"
    "💰 /budget [kategori] [nominal] — Set limit bulanan\n"
    "✏️ /catat [nominal] [kategori] [ket] — Input manual\n"
    "🗑️ /hapus [id] — Hapus transaksi (ID dari hasil simpan)\n"
    "↩️ /batal — Hapus transaksi terakhir\n"
    "📁 /kategori — Lihat/tambah/hapus kategori\n"
    "📋 /help — Bantuan ini\n"
    "🏁 /start — Mulai ulang\n\n"
    "Ketik `/budget Makan 2000000` buat set budget kategori.\n"
    "Ketik `/kategori tambah Kesehatan` buat kategori baru."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.getenv("TELEGRAM_USER_CHAT_ID"):
        await update.message.reply_text(
            f"{random.choice(GREETINGS)}\n\n"
            f"Untuk bisa mengirim laporan otomatis, aku perlu tahu ID chatmu. "
            f"Tolong simpan chat ID ini di file `.env` sebagai `TELEGRAM_USER_CHAT_ID`:\n`{update.message.chat_id}`"
        )
    else:
        await update.message.reply_text(random.choice(GREETINGS))
    await update.message.reply_text("Cara pakai:\n1. Chat biasa: 'makan siang 45rb'\n2. /help : Lihat semua perintah")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode='Markdown')

async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Hari Ini", callback_data='rep_today'),
         InlineKeyboardButton("Minggu Ini", callback_data='rep_week')],
        [InlineKeyboardButton("Bulan Ini", callback_data='rep_month')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Pilih periode laporan:", reply_markup=reply_markup)

async def budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Format: /budget Makan 2000000
    if len(context.args) < 2:
        await update.message.reply_text("Format salah. Contoh: /budget Makan 2000000")
        return
    
    kategori = context.args[0].capitalize()
    try:
        limit = float(context.args[1].replace(".", "").replace(",", ""))
        async with AsyncSessionLocal() as db:
            await set_budget(db, kategori, limit)
        await update.message.reply_text(f"✅ Budget {kategori} di-set ke {format_idr(int(limit))}")
    except ValueError:
        await update.message.reply_text("Nominal harus angka.")

async def catat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Format: /catat 50000 Makan Nasi Goreng
    if len(context.args) < 2:
        await update.message.reply_text("Format salah. Contoh: /catat 50000 Makan Nasi Goreng")
        return
    
    try:
        nominal = int(context.args[0].replace(".", "").replace(",", ""))
        kategori = context.args[1].capitalize()
        deskripsi = " ".join(context.args[2:]) if len(context.args) > 2 else kategori
        
        from services.nlp_parser import ParsedTransaction
        parsed = ParsedTransaction(
            nominal=nominal,
            jenis="expense",
            kategori=kategori,
            deskripsi=deskripsi,
            confidence=1.0
        )
        
        async with AsyncSessionLocal() as db:
            tx = await create_transaction(db, parsed, confirmed=True)
        await update.message.reply_text(f"✅ Dicatat: {format_idr(nominal)} ({kategori}) (ID: {tx.id})\nKetik `/hapus {tx.id}` kalau salah.")
    except ValueError:
        await update.message.reply_text("Nominal harus angka.")

async def hapus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /hapus {id_transaksi}. Contoh: /hapus 3")
        return
    try:
        tx_id = int(context.args[0])
        async with AsyncSessionLocal() as db:
            ok = await delete_transaction(db, tx_id)
        if ok:
            await update.message.reply_text(f"🗑️ Transaksi ID {tx_id} berhasil dihapus.")
        else:
            await update.message.reply_text(f"Transaksi ID {tx_id} tidak ditemukan.")
    except ValueError:
        await update.message.reply_text("ID harus angka.")
    except Exception as e:
        await update.message.reply_text(f"Gagal hapus: {e}")

async def batal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hapus transaksi terakhir."""
    async with AsyncSessionLocal() as db:
        last_tx = await get_last_transaction(db)
        if not last_tx:
            await update.message.reply_text("Belum ada transaksi untuk dibatalkan.")
            return
        await delete_transaction(db, last_tx.id)
        await update.message.reply_text(f"🗑️ Transaksi terakhir ({format_idr(last_tx.nominal)} - {last_tx.kategori}) berhasil dibatalkan.")

async def kategori_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        async with AsyncSessionLocal() as db:
            cats = await list_categories(db)
        if not cats:
            await update.message.reply_text("Belum ada kategori. Tambah: /kategori tambah [nama]")
            return
        msg = "*📁 Daftar Kategori:*\n"
        for c in cats:
            msg += f"- {c.nama}\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        return

    action = context.args[0].lower()
    if action == "tambah" and len(context.args) >= 2:
        nama = " ".join(context.args[1:]).capitalize()
        async with AsyncSessionLocal() as db:
            ok = await add_category(db, nama)
        if ok:
            await update.message.reply_text(f"✅ Kategori '{nama}' ditambahkan.")
        else:
            await update.message.reply_text(f"Kategori '{nama}' sudah ada.")
    elif action == "hapus" and len(context.args) >= 2:
        nama = " ".join(context.args[1:]).capitalize()
        async with AsyncSessionLocal() as db:
            ok = await delete_category(db, nama)
        if ok:
            await update.message.reply_text(f"🗑️ Kategori '{nama}' dihapus.")
        else:
            await update.message.reply_text(f"Kategori '{nama}' tidak ditemukan.")
    else:
        await update.message.reply_text("Format: /kategori tambah [nama] atau /kategori hapus [nama]")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Category override: if pending confirmation + text doesn't parse as new tx
    if context.user_data.get('last_parsed') and not parse_transaction(text):
        parsed = context.user_data['last_parsed']
        parsed.kategori = text.capitalize()
        msg = f"Kategori diubah ke *{parsed.kategori}*\n"
        msg += f"Dicatat: *{format_idr(parsed.nominal)}*\n"
        msg += f"Jenis: {'Pemasukan' if parsed.jenis == 'income' else 'Pengeluaran'}\n\n"
        msg += "Simpan?"
        keyboard = [
            [InlineKeyboardButton("Ya, Simpan", callback_data='save'),
             InlineKeyboardButton("Salah, Batalkan", callback_data='cancel')]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    parsed = parse_transaction(text)
    
    if not parsed:
        await update.message.reply_text("Maaf, aku ga paham. Coba 'makan 45rb' atau 'gajian 5jt'.")
        return

    # Store in context for confirmation
    context.user_data['last_parsed'] = parsed
    
    msg = f"Dicatat: *{format_idr(parsed.nominal)}*\n"
    msg += f"Kategori: {parsed.kategori}\n"
    msg += f"Jenis: {'Pemasukan' if parsed.jenis == 'income' else 'Pengeluaran'}\n\n"
    msg += "Simpan?"

    keyboard = [
        [InlineKeyboardButton("Ya, Simpan", callback_data='save'),
         InlineKeyboardButton("Salah, Batalkan", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'save':
        parsed = context.user_data.get('last_parsed')
        if parsed:
            async with AsyncSessionLocal() as db:
                tx = await create_transaction(db, parsed, confirmed=True)
            keyboard = [[InlineKeyboardButton("↩️ Undo", callback_data=f'undo_{tx.id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text=f"✅ Berhasil disimpan: {format_idr(parsed.nominal)} ({parsed.kategori}) (ID: {tx.id})",
                reply_markup=reply_markup
            )
            
            # Check for budget alert (existing code below)
            async with AsyncSessionLocal() as db_alert:
                budget_status = await get_budget_usage(db_alert)
                for b in budget_status:
                    if b["kategori"] == tx.kategori and b["percent"] >= 80 and os.getenv("TELEGRAM_USER_CHAT_ID"):
                        if b["percent"] >= 100:
                            alert_msg = f"⚠️ *Peringatan!* Pengeluaranmu untuk *{b['kategori']}* sudah *melebihi limit* ({format_idr(int(b['spent']))} / {format_idr(int(b['limit']))}) bulan ini!"
                        else:
                            alert_msg = f"🔔 *Peringatan!* Pengeluaranmu untuk *{b['kategori']}* sudah *mencapai {int(b['percent'])}%* dari limit ({format_idr(int(b['spent']))} / {format_idr(int(b['limit']))}) bulan ini."
                        await context.bot.send_message(chat_id=os.getenv("TELEGRAM_USER_CHAT_ID"), text=alert_msg, parse_mode='Markdown')
        else:
            await query.edit_message_text(text="Sesi kadaluarsa.")
        context.user_data['last_parsed'] = None
        
    elif query.data == 'cancel':
        await query.edit_message_text(text="❌ Dibatalkan.")
        context.user_data['last_parsed'] = None
        
    elif query.data.startswith('undo_'):
        tx_id = int(query.data.split('_')[1])
        async with AsyncSessionLocal() as db:
            await delete_transaction(db, tx_id)
        await query.edit_message_text(text="↩️ Transaksi berhasil dibatalkan.")
        context.user_data['last_parsed'] = None
        
    elif query.data.startswith('rep_'):
        period = query.data.split('_')[1]
        now = datetime.now()
        if period == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            prev_start = start - timedelta(days=1)
            prev_end = end - timedelta(days=1)
            title = "HARI INI"
        elif period == 'week':
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            prev_start = start - timedelta(days=7)
            prev_end = start - timedelta(seconds=1)
            title = "MINGGU INI"
        else: # month
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day = calendar.monthrange(now.year, now.month)[1]
            end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
            prev_month_end = start - timedelta(seconds=1)
            prev_start = prev_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            prev_end = prev_month_end
            title = "BULAN INI"
            
        async with AsyncSessionLocal() as db:
            summary = await get_summary(db, start, end)
            prev_summary = await get_summary(db, prev_start, prev_end)
            
        text = f"📊 *LAPORAN {title}*\n\n"
        text += f"💰 Pemasukan: {format_idr(int(summary['total_income']))}\n"
        text += f"💸 Pengeluaran: {format_idr(int(summary['total_expense']))}\n"
        text += f"⚖️ Selisih: {format_idr(int(summary['total_income'] - summary['total_expense']))}\n"
        
        # Historical comparison
        prev_total = prev_summary['total_income'] + prev_summary['total_expense']
        cur_total = summary['total_income'] + summary['total_expense']
        if prev_total > 0:
            diff_pct = ((cur_total - prev_total) / prev_total) * 100
            sign = "+" if diff_pct >= 0 else ""
            text += f"\n📈 *Vs periode sebelumnya:* {sign}{diff_pct:.1f}%\n"
        
        text += "\n"
        
        if summary['by_category']:
            text += "*Breakdown Kategori:*\n"
            for cat, val in summary['by_category'].items():
                prev_val = prev_summary['by_category'].get(cat, 0)
                line = f"- {cat}: {format_idr(int(val))}"
                if prev_val > 0:
                    d = ((val - prev_val) / prev_val) * 100
                    s = "+" if d >= 0 else ""
                    line += f" ({s}{d:.0f}%)"
                text += line + "\n"
        
        await query.edit_message_text(text=text, parse_mode='Markdown')

async def send_weekly_report(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    async with AsyncSessionLocal() as db:
        summary = await get_summary(db, start_of_week, end_of_week)

    text = f"📊 *LAPORAN MINGGUAN (Senin - Minggu)*\n\n"
    text += f"💰 Pemasukan: {format_idr(int(summary['total_income']))}\n"
    text += f"💸 Pengeluaran: {format_idr(int(summary['total_expense']))}\n"
    text += f"⚖️ Selisih: {format_idr(int(summary['total_income'] - summary['total_expense']))}\n\n"
    
    if summary['by_category']:
        text += "*Breakdown Kategori Pengeluaran:*\n"
        for cat, val in summary['by_category'].items():
            text += f"- {cat}: {format_idr(int(val))}\n"
    
    logging.info(f"Weekly Report Generated:\n{text}")

    if os.getenv("TELEGRAM_USER_CHAT_ID"):
        await context.bot.send_message(chat_id=os.getenv("TELEGRAM_USER_CHAT_ID"), text=text, parse_mode='Markdown')

async def send_monthly_report(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day = calendar.monthrange(now.year, now.month)[1]
    end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

    async with AsyncSessionLocal() as db:
        summary = await get_summary(db, start, end)

    text = f"📊 *LAPORAN BULANAN*\n\n"
    text += f"💰 Pemasukan: {format_idr(int(summary['total_income']))}\n"
    text += f"💸 Pengeluaran: {format_idr(int(summary['total_expense']))}\n"
    text += f"⚖️ Selisih: {format_idr(int(summary['total_income'] - summary['total_expense']))}\n\n"
    
    if summary['by_category']:
        text += "*Breakdown Kategori:*\n"
        for cat, val in summary['by_category'].items():
            text += f"- {cat}: {format_idr(int(val))}\n"

    if os.getenv("TELEGRAM_USER_CHAT_ID"):
        await context.bot.send_message(chat_id=os.getenv("TELEGRAM_USER_CHAT_ID"), text=text, parse_mode='Markdown')

async def check_budget_reminder(context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as db:
        budget_status = await get_budget_usage(db)
    for b in budget_status:
        if b["percent"] >= 80:
            if b["percent"] >= 100:
                alert_msg = f"⚠️ *Peringatan!* Pengeluaran untuk *{b['kategori']}* sudah *melebihi limit* ({format_idr(int(b['spent']))} / {format_idr(int(b['limit']))}) bulan ini!"
            else:
                alert_msg = f"🔔 *Peringatan!* Pengeluaran untuk *{b['kategori']}* sudah *mencapai {int(b['percent'])}%* dari limit ({format_idr(int(b['spent']))} / {format_idr(int(b['limit']))}) bulan ini."
            if os.getenv("TELEGRAM_USER_CHAT_ID"):
                await context.bot.send_message(chat_id=os.getenv("TELEGRAM_USER_CHAT_ID"), text=alert_msg, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("Maaf, ada kesalahan teknis. Coba lagi ya.")

if __name__ == '__main__':
    import asyncio
    import signal
    
    async def main():
        token = os.getenv("BOT_TOKEN")
        if not token or token == "your_telegram_bot_token_here":
            print("Error: BOT_TOKEN belum diisi di .env")
            return
        
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("laporan", laporan))
        app.add_handler(CommandHandler("budget", budget_command))
        app.add_handler(CommandHandler("catat", catat_command))
        app.add_handler(CommandHandler("hapus", hapus_command))
        app.add_handler(CommandHandler("batal", batal_command))
        app.add_handler(CommandHandler("kategori", kategori_command))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_error_handler(error_handler)

        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        scheduler = AsyncIOScheduler()
        scheduler.add_job(send_weekly_report, 'cron', day_of_week='mon', hour=9, minute=0, args=[app])
        scheduler.add_job(send_monthly_report, 'cron', day=1, hour=9, minute=0, args=[app])
        scheduler.add_job(check_budget_reminder, 'cron', day_of_week='mon', hour=10, minute=0, args=[app])
        scheduler.start()

        print("Bot is running...")
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, SystemExit):
            await app.stop()
            await app.shutdown()

    asyncio.run(main())
