import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from assignment import assignment_id,classify_candidates

base={"tckn":"TEST","travelType":"Yurtiçi Geçici Görev Yolluğu - Talimatlı","start":"03/08/2026","end":"13/08/2026"}
other={**base,"start":"20/08/2026","end":"25/08/2026"}
assert assignment_id(base)!=assignment_id(other)

same={"text":"Yurtiçi Geçici Görev Yolluğu - Talimatlı 03/08/2026 12/08/2026"}
over={"text":"Yurtiçi Geçici Görev Yolluğu - Talimatlı 10/08/2026 20/08/2026"}
assert classify_candidates([same],base)[0]["relation"]=="EXACT"
assert classify_candidates([over],base)[0]["relation"]=="OVERLAP"
print("ASSIGNMENT TESTS OK")
