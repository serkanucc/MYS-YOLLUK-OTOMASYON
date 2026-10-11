import sys
import importlib.util
import importlib.util
import sys
from io import BytesIO
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from workbook_support import create_template, validate_workbook

# Şablonun ikinci sayfası motorun mevcut amir TCKN okuyucusuyla da uyumlu olmalı.
runner_path = Path(__file__).resolve().parents[1] / "scripts" / "stage1-live-run.py"
spec = importlib.util.spec_from_file_location("stage1_live_run", runner_path)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

# İndirilen boş şablon upload kontrolünden ve motorun amir etiketi kuralından geçmeli.
template = create_template()
validate_workbook(template)
try:
    runner.read_amir_tckn(openpyxl.load_workbook(BytesIO(template)))
except RuntimeError as error:
    assert "Birim Amiri TC/TCKN bulunamadı" in str(error)
else:
    raise AssertionError("Boş şablonda amir TCKN doldurulmadığı halde hata üretilmedi")

# Yanlış sütunlu Excel, yükleme sırasında açıklayıcı bir hatayla reddedilmeli.
invalid = openpyxl.Workbook()
invalid.create_sheet("Birim Amiri")
buffer = BytesIO()
invalid.save(buffer)
try:
    validate_workbook(buffer.getvalue())
except ValueError as error:
    assert "zorunlu sütun" in str(error)
else:
    raise AssertionError("Zorunlu sütunları olmayan çalışma kitabı kabul edildi")

print("WORKBOOK SUPPORT TESTS OK")
