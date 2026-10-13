import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from assignment import assignment_id,classify_candidates,split_candidates,parse_duty_dates,validate_day_count

base={"tckn":"TEST","travelType":"Yurtiçi Geçici Görev Yolluğu - Talimatlı","start":"03/08/2026","end":"13/08/2026"}
other={**base,"start":"20/08/2026","end":"25/08/2026"}
assert assignment_id(base)!=assignment_id(other)

same={"text":"Yurtiçi Geçici Görev Yolluğu - Talimatlı 03/08/2026 12/08/2026"}
over={"text":"Yurtiçi Geçici Görev Yolluğu - Talimatlı 10/08/2026 20/08/2026"}
assert classify_candidates([same],base)[0]["relation"]=="EXACT"
assert classify_candidates([over],base)[0]["relation"]=="OVERLAP"

# Farklı tarihlerdeki eski kayıtlar sınıflandırma ve kullanıcı uyarısı üretmemeli.
different_dates={"text":"Yurtiçi Geçici Görev Yolluğu - Talimatlı 20/08/2026 24/08/2026"}
assert classify_candidates([different_dates],base)==[]

# Tarihi çözümlenemeyen kayıt, tarih çakışması kesin olmadığı için bilgilendirme üretmemeli.
ambiguous={"text":"Yurtiçi Geçici Görev Yolluğu - Talimatlı"}
definite,uncertain=split_candidates(classify_candidates([same,ambiguous],base))
assert [candidate["relation"] for candidate in definite]==["EXACT"]
assert [candidate["relation"] for candidate in uncertain]==["AMBIGUOUS"]

# Kısa tarih listesi noktayla ayrılabilir; gün aralığının iki ucu da dahildir.
separate_dates=parse_duty_dates("03.10.25/09/2026")
assert [date.strftime("%d/%m/%Y") for date in separate_dates]==[
    "03/09/2026","10/09/2026","25/09/2026"
]
assert validate_day_count(separate_dates,3)==3
inclusive_range=parse_duty_dates("03-13/09/2026")
assert len(inclusive_range)==11 and validate_day_count(inclusive_range,11)==11
try:
    validate_day_count(inclusive_range,10)
except ValueError as error:
    assert "11 görev günü" in str(error)
else:
    raise AssertionError("03-13 aralığı 10 gün olarak kabul edildi")
try:
    validate_day_count(separate_dates,None)
except ValueError as error:
    assert "pozitif tam sayı" in str(error)
else:
    raise AssertionError("Boş GÜN SAYISI kabul edildi")
print("ASSIGNMENT TESTS OK")
