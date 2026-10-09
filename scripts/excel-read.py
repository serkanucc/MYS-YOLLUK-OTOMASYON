import json, sys, openpyxl, re
from pathlib import Path
from datetime import datetime, timedelta
from assignment import duty_period

path = Path(sys.argv[1])
wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
ws = wb[wb.sheetnames[0]]
rows = list(ws.iter_rows(values_only=True))
if not rows: raise SystemExit("Excel boş.")
headers = [str(x).strip() if x is not None else "" for x in rows[0]]
aliases = {
    "identityNo":["TC NO","TCKN","TC KIMLIK NO"], "firstName":["AD","ADI"],
    "lastName":["SOYAD","SOYADI"], "title":["UNVAN","ÜNVAN"],
    "degree":["DERECE"], "step":["KADEME"],
    "additionalIndicator":["EK GÖSTERGE","EK GOSTERGE"],
    "dailyAmount":["GÜNDELİĞİ","GUNDELIGI"],
    "dutyDates":["GEÇ. GÖREV TARİHİ","GEÇ GÖREV TARİHİ"],
    "dayCount":["GÜN SAYISI"], "iban":["IBAN"], "rowNumber":["SIRANO","SIRA NO"]
}
idx = {}
for key, names in aliases.items():
    for name in names:
        if name in headers: idx[key] = headers.index(name); break
required = ["identityNo","dutyDates","iban"]
missing = [x for x in required if x not in idx]
if missing: raise SystemExit("Eksik Excel sütunu: " + ", ".join(missing))

def derive_dates(raw):
    _, start, end = duty_period(raw)
    return start, end

out = []
for row in rows[1:]:
    if not any(x is not None and str(x).strip() for x in row): continue
    item = {key:(row[pos] if pos < len(row) else None) for key,pos in idx.items()}
    item["startDate"], item["endDate"] = derive_dates(item["dutyDates"])
    out.append(item)
print(json.dumps(out, ensure_ascii=False, default=str))
