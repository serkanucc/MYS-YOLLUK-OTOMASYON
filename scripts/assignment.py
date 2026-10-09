import hashlib,re
from datetime import datetime,timedelta

TRAVEL_TYPE="Yurtiçi Geçici Görev Yolluğu - Talimatlı"

def norm_date(s):
    return datetime.strptime(s,"%d/%m/%Y").date()

def parse_duty_dates(raw):
    """Excel görev tarihi biçimlerini gerçek görev günlerine ve MYS aralığına çevirir."""
    s=str(raw or "").strip()
    if not s: raise ValueError("Görev tarihi boş.")
    full=re.findall(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b",s)
    if full and re.fullmatch(r"\s*\d{1,2}[./-]\d{1,2}[./-]\d{4}(?:\s*,\s*\d{1,2}[./-]\d{1,2}[./-]\d{4})*\s*",s):
        dates=sorted({datetime(int(y),int(m),int(d)).date() for d,m,y in full})
    else:
        m=re.fullmatch(r"(.+?)[/\.](\d{1,2})[/\.](\d{4})",s)
        if not m: raise ValueError("Görev tarihi biçimi tanınmadı: "+s)
        token=m.group(1).strip(); month,year=int(m.group(2)),int(m.group(3))
        nums=[int(x) for x in re.findall(r"\d{1,2}",token)]
        if not nums: raise ValueError("Görev günü yok: "+s)
        if len(nums)==2 and "-" in token:
            lo,hi=sorted(nums); dates=[datetime(year,month,d).date() for d in range(lo,hi+1)]
        else:
            dates=sorted({datetime(year,month,d).date() for d in nums})
    return dates

def duty_period(raw):
    dates=parse_duty_dates(raw)
    return dates, dates[0].strftime("%d/%m/%Y"), (dates[-1]+timedelta(days=1)).strftime("%d/%m/%Y")

def assignment_id(x):
    raw="|".join([str(x["tckn"]).strip(),str(x.get("travelType",TRAVEL_TYPE)).strip(),
                  str(x["start"]).strip(),str(x["end"]).strip()])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]

def interval(x):
    return norm_date(x["start"]),norm_date(x["end"])

def extract_dates(text):
    return [norm_date(x) for x in re.findall(r"\b\d{2}/\d{2}/\d{4}\b",text or "")]

def classify_candidates(candidates, assignment):
    a0,a1=interval(assignment);out=[]
    for c in candidates:
        ds=extract_dates(c.get("text",""))
        if len(ds)<2:
            out.append({**c,"relation":"AMBIGUOUS"});continue
        b0,b1=min(ds),max(ds)+timedelta(days=1)
        if b0<a1 and a0<b1:
            relation="EXACT" if b0==a0 and b1==a1 else "OVERLAP"
            out.append({**c,"relation":relation,
                        "start":b0.strftime("%d/%m/%Y"),
                        "end":(b1-timedelta(days=1)).strftime("%d/%m/%Y")})
    return out

def split_candidates(matches):
    return ([m for m in matches if m.get("relation") in ("EXACT","OVERLAP")],
            [m for m in matches if m.get("relation")=="AMBIGUOUS"])

