from pydantic import BaseModel
from typing import Optional
import re

class ParsedTransaction(BaseModel):
    nominal: int
    jenis: str # 'income' or 'expense'
    kategori: str
    deskripsi: str
    confidence: float

CATEGORY_KEYWORDS = {
    "Makan": ["makan", "minum", "kopi", "teh", "sarapan", "siang", "malam", "cemilan", "jajan", "restoran", "warung", "skm", "indomie", "nasgor", "go-food", "grabfood"],
    "Transport": ["transport", "bensin", "tol", "parkir", "ojol", "gojek", "grab", "bus", "kereta", "ojek", "taxi", "go-ride", "grabride"],
    "Tagihan": ["listrik", "token", "pulsa", "wifi", "internet", "tagihan", "langganan", "iuran", "pln", "pdam", "bpjs"],
    "Hiburan": ["hiburan", "nonton", "bioskop", "game", "netflix", "spotify", "main", "healing"],
    "Belanja": ["belanja", "beli", "shopee", "tokopedia", "toped", "baju", "sepatu", "tas", "supermarket", "indomaret", "alfamart"],
    "Kesehatan": ["obat", "dokter", "sehat", "apotek", "vitamin", "sakit"],
    "Pendidikan": ["buku", "kursus", "belajar", "kampus", "sekolah", "udemy"],
    "Gaji": ["gaji", "gajian", "bonus", "insentif", "payroll"],
    "Hutang": ["bayar utang", "bayar hutang", "lunasi utang", "cicilan"], # expense
    "Piutang": ["pinjamkan", "pinjemin", "kasih pinjam", "ngutangin"], # expense
    "Transfer": ["transfer ke", "transfer uang"], # expense
}

INCOME_KEYWORDS = ["gaji", "gajian", "bonus", "jual", "dapet", "terima", "pemasukan", "income", "pendapatan", "transfer balik", "balikin utang", "dibayar utang", "balikin pinjeman"]

def parse_transaction(text: str) -> Optional[ParsedTransaction]:
    text = text.lower()
    
    # 1. Extract Nominal
    nominal = 0
    match_rb = re.search(r'(\d+)\s*(rb|k)', text)
    match_jt = re.search(r'(\d+)\s*jt', text)
    match_raw = re.search(r'(\d+[\d\.]*)', text)
    
    if match_rb:
        nominal = int(match_rb.group(1)) * 1000
    elif match_jt:
        nominal = int(match_jt.group(1)) * 1000000
    elif match_raw:
        raw_val = match_raw.group(1).replace(".", "")
        if raw_val.isdigit():
            nominal = int(raw_val)
            
    if nominal == 0:
        return None

    # 2. Detect Jenis
    jenis = "expense"
    confidence = 0.5
    
    for kw in INCOME_KEYWORDS:
        if kw in text:
            jenis = "income"
            confidence += 0.2
            break
            
    # 3. Detect Kategori
    kategori = "Lainnya"
    cat_found = False
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                kategori = cat
                cat_found = True
                confidence += 0.3
                break
        if cat_found: break

    # Special case for Gaji -> Income
    if kategori == "Gaji":
        jenis = "income"
        confidence = max(confidence, 0.9)
    
    # Special handling for Piutang income
    if kategori == "Piutang" and ("balikin utang" in text or "dibayar utang" in text or "balikin pinjeman" in text):
        jenis = "income"
        confidence = max(confidence, 0.9)

    return ParsedTransaction(
        nominal=nominal,
        jenis=jenis,
        kategori=kategori,
        deskripsi=text,
        confidence=min(confidence, 1.0)
    )

if __name__ == "__main__":
    test_cases = [
        "abis makan 45rb", 
        "gajian 5jt", 
        "beli token listrik 100rb", 
        "grab 20k", 
        "nemu duit 5000",
        "bayar utang 50rb",
        "pinjemin andi 100k",
        "si A balikin utang 100k",
        "transfer ke ortu 200rb"
    ]
    for tc in test_cases:
        print(f"'{tc}' -> {parse_transaction(tc)}")
