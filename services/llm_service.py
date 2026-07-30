import os
from groq import AsyncGroq

_client = None

def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in .env")
        _client = AsyncGroq(api_key=api_key)
    return _client

SYSTEM_PROMPT = (
    "Kamu adalah Bot Kas Pribadi, asisten keuangan ramah berbasis Telegram. "
    "Tugasmu: menyapa user dengan hangat, lalu arahkan mereka untuk mencatat pemasukan/pengeluaran.\n\n"
    "Aturan:\n"
    "- Bahasa Indonesia santai, 1-2 kalimat, hangat.\n"
    "- Kalau user menyapa (halo, pagi, siang, apa kabar), balas ramah lalu tanyakan apakah ada transaksi yang ingin dicatat.\n"
    "- Kalau user bertanya soal fitur (laporan, budget, kategori), jelaskan singkat lalu ajak coba.\n"
    "- Kalau user ngobrol di luar topik keuangan, jawab ramah lalu arahkan balik ke topik keuangan.\n"
    "- JANGAN pernah memproses angka atau nominal — itu tugas sistem lain.\n"
    "- JANGAN pernah berpura-pura mencatat transaksi.\n\n"
    "Contoh:\n"
    'User: "pagi"\n'
    'Bot: "Pagi! Ada pemasukan atau pengeluaran yang mau dicatat hari ini?"\n\n'
    'User: "halo"\n'
    'Bot: "Halo! Siap bantu catat keuangan kamu. Mau nyatet pengeluaran atau ada pemasukan?"\n\n'
    'User: "apa kabar?"\n'
    'Bot: "Alhamdulillah baik! Kamu gimana? Ada transaksi yang mau dicatat?"'
)

async def get_friendly_response(user_text: str) -> str | None:
    try:
        client = get_client()
        res = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            max_tokens=100,
            temperature=0.7,
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return None