from io import BytesIO
import re
from zipfile import BadZipFile

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.styles import Font, PatternFill


PERSONNEL_HEADERS = (
    "SIRANO",
    "TC NO",
    "AD",
    "SOYAD",
    "UNVAN",
    "DERECE",
    "KADEME",
    "EK GÖSTERGE",
    "GÜNDELİĞİ",
    "GEÇ. GÖREV TARİHİ",
    "GÜN SAYISI",
    "IBAN",
)


def validate_workbook(data):
    # Yüklenen Excel'in motorun beklediği iki sayfayı ve alan başlıklarını içerdiğini doğrula.
    try:
        workbook = openpyxl.load_workbook(BytesIO(data), read_only=True, data_only=True)
    except (BadZipFile, InvalidFileException, OSError, ValueError, KeyError) as exc:
        raise ValueError("Dosya geçerli veya okunabilir bir .xlsx çalışma kitabı değil.") from exc
    try:
        if len(workbook.worksheets) < 2:
            raise ValueError("Excel dosyasında Personel ve Birim Amiri olmak üzere en az 2 sayfa olmalı.")

        headers = {
            str(value).strip().upper()
            for value in next(workbook.worksheets[0].iter_rows(max_row=1, values_only=True), ())
            if value is not None
        }
        required_groups = (
            ("TC NO", "TCKN"),
            ("GEÇ. GÖREV TARİHİ", "GEÇ GÖREV TARİHİ"),
            ("IBAN",),
            ("GÜNDELİĞİ", "GUNDELIGI"),
            ("SIRANO", "SIRA NO"),
        )
        missing = ["/".join(group) for group in required_groups if not headers.intersection(group)]
        if missing:
            raise ValueError("Personel sayfasında zorunlu sütun(lar) eksik: " + ", ".join(missing))

        amir_sheet = workbook.worksheets[1]
        amir_label_found = any(
            value is not None and re.search(r"(?:TC|TCKN)$", str(value).strip(), re.IGNORECASE)
            for row in amir_sheet.iter_rows(min_row=1, max_row=min(amir_sheet.max_row, 20), values_only=True)
            for value in row
        )
        if not amir_label_found:
            raise ValueError("Birim Amiri sayfasının ilk 20 satırında TC/TCKN etiketi bulunamadı.")
    finally:
        workbook.close()


def create_template():
    # Boş şablon aynı sütun/sayfa düzenini sağlar; gerçek personel veya amir verisi içermez.
    workbook = openpyxl.Workbook()
    personnel = workbook.active
    personnel.title = "Personel"
    personnel.append(PERSONNEL_HEADERS)
    personnel.freeze_panes = "A2"
    personnel.auto_filter.ref = "A1:L1"
    personnel.row_dimensions[1].height = 30
    for cell in personnel[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
    for column, width in {
        "A": 12, "B": 16, "C": 18, "D": 18, "E": 22, "F": 12,
        "G": 12, "H": 16, "I": 16, "J": 24, "K": 14, "L": 30,
    }.items():
        personnel.column_dimensions[column].width = width

    manager = workbook.create_sheet("Birim Amiri")
    manager["A1"] = "Birim Amiri"
    manager["B1"] = "TC/TCKN"
    manager["C1"] = ""
    manager["B1"].font = Font(bold=True, color="FFFFFF")
    manager["B1"].fill = PatternFill("solid", fgColor="1F4E78")
    manager.column_dimensions["A"].width = 20
    manager.column_dimensions["B"].width = 16
    manager.column_dimensions["C"].width = 20

    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()
