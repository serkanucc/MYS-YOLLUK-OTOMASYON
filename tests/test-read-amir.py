import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import importlib.util
import openpyxl

# stage1-live-run.py nokta içermeyen bir modül adı olmadığı için importlib ile yüklenir.
_spec = importlib.util.spec_from_file_location(
    "stage1_live_run", Path(__file__).resolve().parents[1] / "scripts" / "stage1-live-run.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
read_amir_tckn = _mod.read_amir_tckn


def workbook_with_amir(value, label="TC/TCKN"):
    wb = openpyxl.Workbook()
    wb.worksheets[0].title = "Personel"
    ws = wb.create_sheet("Birim Amiri")
    ws["A1"] = "Birim Amiri"
    ws["B1"] = label
    ws["C1"] = value
    return wb


# 1) Temiz 11 haneli metin
assert read_amir_tckn(workbook_with_amir("12345678901")) == "12345678901"

# 2) Boşluklu / ayraçlı metin (eski hatalı desen bunları temizlemiyordu)
assert read_amir_tckn(workbook_with_amir("123 456 78901")) == "12345678901"
assert read_amir_tckn(workbook_with_amir("123-456-78901")) == "12345678901"

# 3) Excel sayı hücresi (int / float) -> "12345678901.0" 12 hane oluyordu
assert read_amir_tckn(workbook_with_amir(12345678901)) == "12345678901"
assert read_amir_tckn(workbook_with_amir(12345678901.0)) == "12345678901"

# 4) Etiket biçimi varyasyonları
assert read_amir_tckn(workbook_with_amir("12345678901", label="TCKN")) == "12345678901"

# 5) 11 hane olmayan değer -> güvenli hata
for bad in ("1234567890", "123456789012", None, ""):
    try:
        read_amir_tckn(workbook_with_amir(bad))
    except RuntimeError:
        pass
    else:
        raise AssertionError(f"Geçersiz değer hata üretmedi: {bad!r}")

# 6) 2. sayfa yoksa hata
wb = openpyxl.Workbook()
try:
    read_amir_tckn(wb)
except RuntimeError:
    pass
else:
    raise AssertionError("2. sayfa yokken hata üretilmedi")

print("READ_AMIR_TCKN TESTS OK")
