import json,os,re,shutil,subprocess,time,argparse
from pathlib import Path
import openpyxl
from assignment import assignment_id,classify_candidates,split_candidates,TRAVEL_TYPE,duty_period,validate_day_count
from playwright_connection import has_green_group,launch_connection_setup,resolve_cli_js
from workbook_support import initialize_result_workbook,simulated_yolluk_number,write_yolluk_number

def find_excel_workbook(root: Path, cfg: dict) -> Path:
    """
    Kullanıcının upload ettiği her isimde Excel'i bulur.
    Öncelik sırası:
    1. Runtime config'den sourceWorkbook (mutlak yol olabilir)
    2. Ana config sourceWorkbook (relative -> root ile çözümle)
    3. data/ klasöründeki .xlsx dosyalarından ilkini kullan (dosya ismi önemli değil)
    4. None döndür (çağıranın kontrol etmesi gerekiyor)
    """
    EXCEL_CANDIDATES = []
    
    # 1. Runtime config (varsa)
    runtime_cfg = root / "config" / "runner-settings.runtime.json"
    if runtime_cfg.exists():
        try:
            rs = json.loads(runtime_cfg.read_text(encoding="utf-8-sig"))
            if rs.get("sourceWorkbook"):
                p = Path(rs["sourceWorkbook"])
                EXCEL_CANDIDATES.append(p if p.is_absolute() else root / p)
        except Exception: pass
    
    # 2. Ana config sourceWorkbook
    cfg_source = cfg.get("sourceWorkbook")
    if cfg_source:
        p = Path(cfg_source)
        EXCEL_CANDIDATES.append(p if p.is_absolute() else root / p)
    
    # 3. data/ klasöründeki tüm .xlsx'yi tara (dosya ismi önemli değil, var olsun)
    data_dir = root / "data"
    if data_dir.exists():
        for f in sorted(data_dir.glob("*.xlsx")):
            # uploaded-workbook.xlsx ve Yolluk Sonuc.xlsx'yi atla
            if f.name in ["uploaded-workbook.xlsx", "Yolluk Sonuc.xlsx"]:
                continue
            if f not in EXCEL_CANDIDATES:
                EXCEL_CANDIDATES.append(f)
    
    # 4. Bulunan ilk var olanı döndür
    for path in EXCEL_CANDIDATES:
        if path.exists():
            return path
    
    return None

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config/runner-settings.json").read_text(encoding="utf-8-sig"))
FIXED=json.loads((ROOT/"config/fixed-values.json").read_text(encoding="utf-8-sig"))
FLOW_PRE=(ROOT/"scripts/stage1-flow-pre.js").read_text(encoding="utf-8")
FLOW_POST=(ROOT/"scripts/stage1-flow-post.js").read_text(encoding="utf-8")
DUP=(ROOT/"scripts/duplicate-check.js").read_text(encoding="utf-8")
# Makineye özel runtime ayarı varsa önce onun Excel yolunu dene; taşınabilir varsayılanı koru.
RUNTIME_CFG=ROOT/"config/runner-settings.runtime.json"
EXCEL_CANDIDATES=[]
if RUNTIME_CFG.exists():
    runtime_settings=json.loads(RUNTIME_CFG.read_text(encoding="utf-8-sig"))
    if runtime_settings.get("sourceWorkbook"):
        EXCEL_CANDIDATES.append(runtime_settings["sourceWorkbook"])
EXCEL=find_excel_workbook(ROOT, CFG)  # Dinamik Excel yol bulma
EXCEL_PATHS=[]
for workbook in EXCEL_CANDIDATES:
    path=Path(workbook)
    path=path if path.is_absolute() else ROOT/path
    if path not in EXCEL_PATHS:
        EXCEL_PATHS.append(path)
EXCEL=next((path for path in EXCEL_PATHS if path.exists()),EXCEL_PATHS[0])
CHECK=ROOT/"data/checkpoint.json"; LOG=ROOT/"logs/stage1.log"; STEPS=ROOT/"data/live-steps.json"
def resolve_cli():
    """playwright-cli.cmd yolunu çalışma anında çözer.
    Öncelik: config > PATH(shutil.which) > %APPDATA%\\npm.
    Proje farklı kullanıcı/makineye taşındığında bağlantı kopmasın diye
    kullanıcı adı koda gömmüyoruz. Bulunamazsa None döner."""
    cfg=CFG.get("cliPath") if isinstance(CFG,dict) else None
    if cfg and Path(cfg).exists():
        return str(cfg)
    which=shutil.which("playwright-cli.cmd") or shutil.which("playwright-cli")
    if which:
        return which
    appdata=os.environ.get("APPDATA")
    if appdata:
        cand=Path(appdata)/"npm"/"playwright-cli.cmd"
        if cand.exists():
            return str(cand)
    return None


CLI=resolve_cli()


def playwright_health(require_green=True):
    """Bağlantı durumunu Playwright CLI oturum listesinden okur.
    Başlangıçta istenirse chrome-main attach'i ve Chrome'daki yeşil grubu doğrular.

    Dönen değerler:
      OK              : hedef session açık/attach; istenirse yeşil Playwright grubu da var
      NO_CONNECTION   : CLI çalışıyor ama hedef session yok / attach değil
      SESSION_CONFLICT: birden fazla aynı adlı session (uyumsuz durum)
      CLI_MISSING     : playwright-cli.cmd hiç bulunamadı (kurulum/yol sorunu)
      CLI_ERROR       : CLI çalıştırılamadı veya çıktısı okunamadı
    """
    if not CLI or not Path(CLI).exists():
        return "CLI_MISSING"
    try:
        raw=subprocess.run([CLI,"list","--all","--json"],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=10)
    except (OSError,subprocess.SubprocessError,RuntimeError):
        return "CLI_ERROR"
    if raw.returncode != 0 or not raw.stdout.strip():
        return "CLI_ERROR"
    try:
        state=json.loads(raw.stdout)
    except Exception:
        return "CLI_ERROR"
    browsers=state.get("browsers",[])
    session=CFG.get("browserSession","chrome-main")
    cm=[b for b in browsers if b.get("name")==session]
    if len(cm)>1:
        return "SESSION_CONFLICT"
    if len(cm)==1 and cm[0].get("status")=="open" and cm[0].get("attached") is True:
        if not require_green:
            return "OK"
        try:
            return "OK" if has_green_group(ROOT/"scripts/playwright-connection/PW-GREEN-CHECK.ps1") else "NO_CONNECTION"
        except Exception:
            return "CLI_ERROR"
    return "NO_CONNECTION"


def wait_for_playwright(context="",max_wait=None,auto_start=False,require_green=True):
    """Yalnız açıkça istendiğinde eksik başlangıç bağlantısını kur; çalışma ortasında attach başlatma.
    Sağlıklı bağlantı varsa yeni attach açılmaz. CLI kurulu değilse hemen hata verir.
    max_wait: saniye; verilirse bu süre içinde bağlantı kurulmazsa sessizce döner."""
    start=time.time();last=None;connection_started=False
    while True:
        state=playwright_health(require_green=require_green)
        if state=="OK":
            if last is not None:
                log("PLAYWRIGHT_RECONNECTED | chrome-main oturumu dogrulandi")
                step("Playwright bağlantısı yeniden kuruldu", "chrome-main oturumu doğrulandı")
            return
        if state=="CLI_MISSING":
            raise RuntimeError("playwright-cli.cmd bulunamadı. Playwright CLI kurulumunu veya cliPath ayarını kontrol edin.")
        if state=="NO_CONNECTION" and auto_start and CFG.get("autoStartPlaywrightConnection",True) and not connection_started:
            cli_js=resolve_cli_js(CLI,os.environ.get("APPDATA"))
            if not cli_js:
                raise RuntimeError("Playwright bağlantı başlatıcısı için playwright-cli.js bulunamadı. CLI kurulumunu veya cliPath ayarını kontrol edin.")
            step("Playwright bağlantısı başlatılıyor","Var olan bağlantı kontrol ediliyor; hazır bağlantı korunacak, yoksa Allow & select açılacak.")
            log("PLAYWRIGHT_AUTOSTART | local connection helper")
            launch_connection_setup(ROOT,cli_js)
            connection_started=True
            last="NO_CONNECTION"
        msg={
            "NO_CONNECTION":"Playwright bağlantısı bekleniyor",
            "SESSION_CONFLICT":"Playwright bağlantı durumu tutarsız: birden fazla/uyumsuz chrome-main oturumu",
            "CLI_ERROR":"Playwright CLI çalıştırılamadı veya çıktısı okunamadı"
        }.get(state,"Playwright bağlantısı bekleniyor")
        if msg!=last:
            log("PLAYWRIGHT_WAIT | "+msg+((" | "+context) if context else ""))
            step("Playwright bağlantısı bekleniyor", msg+((" | "+context) if context else ""))
            last=msg
        if max_wait is not None and time.time()-start>max_wait:
            return
        time.sleep(2)


def is_login_page(url):
    s=str(url).lower()
    return any(k in s for k in ("giris.hmb.gov.tr","/login","callbackauthorize","oauth2.0","cas/login"))

def pw(*args):
    # Akış sırasında bağlantı koparsa bekle; yeni BAT/attach başlatma ve Chrome izin durumunu yeniden sorgulama.
    wait_for_playwright("Playwright işlemi öncesi kontrol",auto_start=False,require_green=False)
    p=subprocess.run([CLI,"-s="+str(CFG.get("browserSession","chrome-main")),*args],capture_output=True,text=True,encoding="utf-8",errors="replace")
    if p.returncode: raise RuntimeError(p.stderr or p.stdout)
    if args and args[0]=="goto" and len(args)>1:
        ensure_mys_session("goto "+str(args[1]))
    return p.stdout

def ev(expr):
    out=pw("eval",expr);m=re.search(r"### Result\s*\n([\s\S]*?)(?:\n### Ran|$)",out)
    if not m: raise RuntimeError(out)
    try:return json.loads(m.group(1).strip())
    except:return m.group(1).strip()

def ensure_mys_session(context=""):
    """Sayfa CAS giriş ekranına düşmüşse oturum düşmüştür.
    Otomasyon giriş yapmaz; kullanıcıyı net bilgilendirir ve tarayıcıda
    giriş yapılmasını bekler. Giriş tamamlanıp MYS sayfasına dönülünce devam eder."""
    announced=None
    while True:
        try:
            url=str(ev("location.href"))
        except Exception:
            return
        if not is_login_page(url):
            if announced:
                log("MYS_SESSION_RESTORED | giris tamamlandi, devam ediliyor")
                step("MYS oturumu geri geldi","Giriş tamamlandı; işleme devam ediliyor.")
            return
        msg="MYS oturumu düşmüş: tarayıcı CAS giriş ekranında. Lütfen açık Chrome penceresinde MYS'e giriş yapın; giriş yapılınca otomasyon otomatik devam eder."
        if msg!=announced:
            log("MYS_SESSION_EXPIRED | "+msg+((" | "+context) if context else ""))
            step("MYS girişi bekleniyor", msg+((" | "+context) if context else ""))
            announced=msg
        time.sleep(3)

def save(x,status,**extra):
    d=json.loads(CHECK.read_text(encoding="utf-8-sig")) if CHECK.exists() else {"version":2,"stage":"STAGE1","records":{}}
    d["version"]=2;d["stage"]="STAGE1";d["source"]=str(EXCEL);d["lastAssignment"]=x["assignmentId"]
    base={"row":x["row"],"status":status,"dutyDates":x.get("dutyDates"),
          "actualDutyDates":x.get("actualDutyDates",[]),"dayCount":x.get("dayCount"),
          "mysStart":x.get("start"),"mysEnd":x.get("end")}
    d.setdefault("records",{})[x["assignmentId"]]={**base,**extra}
    CHECK.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")

def log(s):
    LOG.parent.mkdir(exist_ok=True);LOG.open("a",encoding="utf8").write(time.strftime("%Y-%m-%dT%H:%M:%S")+" | "+s+"\n")
def step(label, detail=""):
    try: arr=json.loads(STEPS.read_text(encoding="utf-8")) if STEPS.exists() else []
    except: arr=[]
    arr.append({"time":time.strftime("%H:%M:%S"),"label":label,"detail":detail,"status":"active"})
    arr=arr[-30:]
    STEPS.write_text(json.dumps(arr,ensure_ascii=False,indent=2),encoding="utf-8")
    log("STEP | "+label+((" | "+detail) if detail else ""))

def valid_tr_iban(value):
    s=re.sub(r"\s+","",str(value or "").upper())
    if not re.fullmatch(r"TR\d{24}",s): return False
    moved=s[4:]+s[:4]
    converted=""
    for ch in moved:
        converted += ch if ch.isdigit() else str(ord(ch)-55)
    return int(converted) % 97 == 1

def read_amir_tckn(wb):
    if len(wb.worksheets)<2: raise RuntimeError("Excel 2. sayfa yok: Birim Amiri TCKN bilgisi alınamadı.")
    ws=wb.worksheets[1]
    for row in ws.iter_rows(min_row=1,max_row=min(ws.max_row,20),values_only=True):
        for j,v in enumerate(row):
            label=str(v).strip() if v is not None else ""
            if label and re.search(r"(?:TC|TCKN)$",label,re.I) and j+1<len(row):
                val=row[j+1]
                if isinstance(val,float) and val.is_integer(): raw=str(int(val))
                elif isinstance(val,int): raw=str(val)
                else: raw=str(val) if val is not None else ""
                digits=re.sub(r"\D","",raw)
                if len(digits)==11: return digits
    raise RuntimeError("Excel 2. sayfada Birim Amiri TC/TCKN bulunamadı. Güncel amir TCKN'sini 2. sayfaya girin.")

def people():
    if not EXCEL.exists():
        raise RuntimeError(
            "Excel dosyası bulunamadı. Kontrol edilen yollar: "
            +"; ".join(str(path) for path in EXCEL_PATHS)+"\n"
            "Güncel 'Yolluk Liste' dosyasını bu yollardan birine koyun veya "
            "config/runner-settings.json içindeki 'sourceWorkbook' değerini güncelleyin "
            "(--excel <dosya> ile farklı bir dosya verebilirsiniz).")
    wb=openpyxl.load_workbook(EXCEL,data_only=True,read_only=True)
    try:
        ws=wb[wb.sheetnames[0]]
        amir_tckn=read_amir_tckn(wb)
        rows=list(ws.iter_rows(values_only=True))
    finally:
        wb.close()
    h=[str(x).strip() if x is not None else "" for x in rows[0]]
    def ci(*names):
        for n in names:
            if n in h:return h.index(n)
        raise RuntimeError("Excel sütunu eksik: "+names[0])
    ti,di,ii,ai,ri=ci("TC NO","TCKN"),ci("GEÇ. GÖREV TARİHİ","GEÇ GÖREV TARİHİ"),ci("IBAN"),ci("GÜNDELİĞİ","GUNDELIGI"),ci("SIRANO","SIRA NO")
    # GÜN SAYISI her satırda tarih alanındaki dahilî görev günleriyle tutarlı olmalı.
    gsi=ci("GÜN SAYISI","GUN SAYISI")
    out=[];skipped=[]
    for excel_row,r in enumerate(rows[1:],start=2):
        if not any(x is not None and str(x).strip() for x in r):continue
        try:
            # Bir satır bozuk/format-dışıysa TÜM listeyi çökertme; o satırı atla ve logla.
            dates,start,end=duty_period(r[di])
            day_count=validate_day_count(dates,r[gsi])
            iban_value=str(r[ii] or "").strip()
            if not valid_tr_iban(iban_value):
                raise RuntimeError(f"IBAN biçimi/checksum geçersiz: {iban_value!r}")
            x={"row":r[ri],"excelRow":excel_row,"tckn":r[ti],"iban":iban_value,"daily":r[ai],
               "dayCount":day_count,
               "dutyDates":str(r[di]).strip(),"actualDutyDates":[d.strftime("%d/%m/%Y") for d in dates],
               "start":start,"end":end,"travelType":TRAVEL_TYPE,"amirTckn":amir_tckn}
            x["assignmentId"]=assignment_id(x);out.append(x)
        except Exception as e:
            # Hatalı satırı atla; kullanıcı panel logundan görebilir. Sağlıklı satırlar işlenmeye devam eder.
            skipped.append({"row":(r[ri] if ri<len(r) else None),"tckn":(r[ti] if ti<len(r) else None),"error":str(e)})
            log(f"EXCEL_ROW_SKIPPED satir={r[ri] if ri<len(r) else '?'} hata={e}")
    if skipped:
        log(f"EXCEL_SKIP_SUMMARY atlanan_satir={len(skipped)} islenen={len(out)}")
    return out


def query_yolluk_list(tckn):
    """Yolluk Süreç ana sayfasındaki listeyi sadece taze Sorgula sonrası okur."""
    pw("goto",CFG["queryUrl"]);time.sleep(.7)
    js=re.sub(r"\s+"," ",DUP.replace("{{TCKN}}",str(tckn)))
    q=ev(js)
    return q

def duplicate(x):
    q=query_yolluk_list(x["tckn"])
    log(f"DUPLICATE_CHECK assignment={x['assignmentId']} candidates={len(q.get('candidates',[]))} (kayıt detay sayfası açılmadan kontrol)")
    for c in q.get("candidates",[]):
        href=next((u for u in c.get("links",[]) if "/yolluk/view?id=" in u),None)
        if not href: continue
        try:
            # Eski kaydı görünür sekmede açmak yerine mevcut oturum çerezleriyle arka planda HTML al.
            fetch_js = f"""(async()=>{{const r=await fetch({json.dumps(href)},{{credentials:'include'}});return await r.text()}})()"""
            html=str(ev(fetch_js))
            m=re.search(r"Başlangıç Tarihi\s*[^0-9]*(\d{2}/\d{2}/\d{4})[\s\S]{0,500}?Bitiş Tarihi\s*[^0-9]*(\d{2}/\d{2}/\d{4})",html,re.I)
            if m: c["text"]+="\nDATES:"+m.group(1)+" "+m.group(2)
        except Exception as e:
            log(f"DUPLICATE_DETAIL_READ_FAILED assignment={x['assignmentId']} error={e}")
    return q

def approved_ids(a):
    d=json.loads(CHECK.read_text(encoding="utf-8-sig")) if CHECK.exists() else {}
    return {k for k,v in d.get("records",{}).items() if v.get("status")=="DUPLICATE_APPROVED" or v.get("approvalGranted") is True}

def should_skip_assignment(old,force_form_test=False):
    # Simülasyon MYS'de kayıt oluşturmadığından tekrar test edilmesini checkpoint engellememeli.
    return old.get("status")=="STAGE1_COMPLETED" and not force_form_test

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--live",action="store_true")
    ap.add_argument("--approve",action="append",default=[])
    ap.add_argument("--skip-duplicate",action="store_true")
    ap.add_argument("--stop-before-submit",action="store_true")
    ap.add_argument("--simulate-submit",action="store_true")
    ap.add_argument("--force-form-test",action="store_true")
    ap.add_argument("--force-iban-reset",action="store_true")
    ap.add_argument("--excel")
    a=ap.parse_args()
    if a.simulate_submit and (a.live or a.stop_before_submit):
        ap.error("--simulate-submit canlı gönderim veya gönderim öncesi durdurma seçenekleriyle birlikte kullanılamaz.")
    global EXCEL,EXCEL_PATHS
    if a.excel:
        EXCEL=(ROOT/a.excel) if not Path(a.excel).is_absolute() else Path(a.excel)
        EXCEL_PATHS=[EXCEL]
    approvals=set(a.approve)|approved_ids(a)
    # Allow & select yalnız otomasyon başlamadan önce eksik bağlantı varsa bir kez tetiklenir.
    wait_for_playwright("MYS otomasyonu başlangıç kontrolü",
                        auto_start=True,
                        require_green=True)
    try:
        assignments=people()
    except RuntimeError as e:
        msg=str(e)
        if "Birim Amiri" in msg and "Excel" in msg:
            print(json.dumps({"status":"USER_INFORMATION_REQUIRED","field":"Birim Amiri TCKN","message":msg},ensure_ascii=False)); return
        raise
    result_excel=ROOT/"data"/"Yolluk Sonuc.xlsx"
    if a.simulate_submit:
        initialize_result_workbook(EXCEL,result_excel)
    for x in assignments:
        d=json.loads(CHECK.read_text(encoding="utf-8-sig")) if CHECK.exists() else {}
        old=d.get("records",{}).get(x["assignmentId"],{})
        if should_skip_assignment(old,a.force_form_test): continue
        approval_granted=(x["assignmentId"] in approvals) or (old.get("approvalGranted") is True)
        if approval_granted: approvals.add(x["assignmentId"])
        save(x,"PROCESSING",approvalGranted=approval_granted)
        log(f"PROCESSING assignment={x['assignmentId']} row={x['row']}");step("Kişi işleme alındı", f"Excel satırı {x['row']}")
        matches=[];baseline_q=None
        if not a.skip_duplicate:
            step("MYS kayıtları kontrol ediliyor");q=duplicate(x)
            # Aynı taze sorgu hem tarih çakışması hem de submit öncesi baseline ID'ler için kullanılır.
            baseline_q=q
            # Yalnızca doğrulanmış aynı/kesişen tarih aralıklarını bildir; diğer ve belirsiz kayıtlar sessiz kalır.
            classified=classify_candidates(q.get("candidates",[]),x)
            matches,_=split_candidates(classified)
            if matches:
                date_ranges=", ".join(f"{match['start']} - {match['end']}" for match in matches)
                warning=("TARİH ÇAKIŞMASI BİLGİSİ: Bu tarihlerde daha önce yolluk bildirimi yapılmış: "
                         f"{date_ranges}. Bu bir hata değildir; bilgilendirme yapıldı ve otomasyon devam ediyor.")
                save(x,"DUPLICATE_WARNING_CONTINUING",matches=matches,approvalGranted=False,warning=warning)
                log(f"DUPLICATE_WARNING_CONTINUING assignment={x['assignmentId']} matches={len(matches)} -> devam ediliyor")
                step("Tarih çakışması bulundu", warning)
        # Duplicate kontrolü atlandıysa baseline için sorgula; normal akışta ikinci sorguyu yapma.
        if baseline_q is None:
            step("MYS kayıtları baseline için sorgulanıyor");baseline_q=query_yolluk_list(x["tckn"])
        step("Yeni form açılıyor")
        baseline_ids=set()
        for bc in baseline_q.get("candidates",[]):
            for bu in bc.get("links",[]):
                bm=re.search(r"/yolluk/view\?id=(\d+)",bu)
                if bm: baseline_ids.add(bm.group(1))
        js_pre=FLOW_PRE.replace("{{FORCE_IBAN}}","true" if a.force_iban_reset else "false").replace("{{TCKN}}",str(x["tckn"])).replace("{{IBAN}}",str(x["iban"])).replace("{{DAILY}}",str(x["daily"])).replace("{{START}}",x["start"]).replace("{{END}}",x["end"]).replace("{{AMIR_TCKN}}",str(x["amirTckn"])).replace("{{BUDGET}}",FIXED["budgetItem"])
        js_post=FLOW_POST.replace("{{TCKN}}",str(x["tckn"])).replace("{{IBAN}}",str(x["iban"])).replace("{{DAILY}}",str(x["daily"])).replace("{{START}}",x["start"]).replace("{{END}}",x["end"]).replace("{{AMIR_TCKN}}",str(x["amirTckn"])).replace("{{BUDGET}}",FIXED["budgetItem"])
        result=None
        personel_yok=False  # NEDEN: geçersiz TCKN'de Mernis personel döndürmez; bu durumda submit'a geçilmeyecek.
        for form_attempt in range(1,3):
            pw("goto",CFG["formUrl"]);time.sleep(1.2)
            try:
                step("Form dolduruluyor", "TCKN, Mernis, maaş, IBAN ve sabit alanlar");result=ev(re.sub(r"\s+"," ",js_pre))
                # NEDEN: Mernis geçersiz/gerçek-olmayan TCKN'de personel döndürmez; Ad Soyad/IBAN/
                # Birim Amiri alanları hiç oluşmaz. Bu bir hata değil DURUM: tahmin yapma, güvenle
                # kullanıcıya bildir ve bir sonraki kişiye geç (formu boşuna doldurmaya çalışma).
                if result.get("personelBulunamadi"):
                    step("Mernis personel bulunamadı", f"TCKN {x['tckn']} için MYS/Mernis personel döndürmedi (geçersiz/gerçek-olmayan TCKN olabilir).")
                    log(f"PERSONEL_NOT_FOUND assignment={x['assignmentId']} tckn={x['tckn']} -> atlaniyor")
                    save(x,"USER_INFORMATION_REQUIRED",message="MYS/Mernis bu TCKN için personel döndürmedi; Excel TCKN'sini kontrol edin.",personelBulunamadi=True)
                    personel_yok=True
                    break
                if result.get("needsIbanCommit"):
                    pw("press","Enter");time.sleep(.7)
                    iban_check=ev("(()=>{const l=[...document.querySelectorAll('label.yte-form-label')].find(x=>x.title==='IBAN');const e=document.getElementById(l.htmlFor);return [...e.querySelectorAll('.yte-power-select-multiple-selected-option-label')].map(x=>x.innerText.trim())})()")
                    if str(x["iban"]).strip().upper() not in [str(v).strip().upper() for v in iban_check]: raise RuntimeError("Excel IBAN Enter sonrası MYS formunda seçilemedi")
                step("Form tamamlanıyor", "Tarih, gündelik, bütçe ve Birim Amiri kontrolleri");result=ev(re.sub(r"\s+"," ",js_post))
                # js_post da personel gelmediyse (geçersiz TCKN) aynı durumu döndürür.
                if result.get("personelBulunamadi"):
                    step("Mernis personel bulunamadı", f"TCKN {x['tckn']} için personel alanları oluşmadı (Birim Amiri alanı yok).")
                    log(f"PERSONEL_NOT_FOUND assignment={x['assignmentId']} tckn={x['tckn']} (post) -> atlaniyor")
                    save(x,"USER_INFORMATION_REQUIRED",message="MYS/Mernis bu TCKN için personel döndürmedi; Excel TCKN'sini kontrol edin.",personelBulunamadi=True)
                    personel_yok=True
                    break
                if result.get("submitDisabled") is not False: raise RuntimeError("Form tamamlanmadı: Yolluk Süreç Hazırlama aktif değil")
                break
            except Exception as e:
                log(f"FORM_FILL_RETRY assignment={x['assignmentId']} attempt={form_attempt} error={e}")
                if form_attempt==2:
                    save(x,"ERROR",message=str(e),formAttempts=form_attempt)
                    raise
                time.sleep(1.5)
        # NEDEN: Mernis bu TCKN için personel döndürmediyse (geçersiz/gerçek-olmayan TCKN) form
        # dolmadı; submit'a geçme, bir sonraki kişiye geç. Tahmin yok, güvenli atlama.
        if personel_yok: continue
        step("Form hazır", "Yolluk Süreç Hazırlama gönderimine hazır.");save(x,"READY_TO_SUBMIT",approvalGranted=(x["assignmentId"] in approvals))
        if a.simulate_submit:
            # Test modu son adımı tamamlanmış gibi kaydeder; MYS submit butonuna hiçbir zaman basmaz.
            yolluk_no=simulated_yolluk_number()
            try:
                write_yolluk_number(result_excel,x["excelRow"],yolluk_no)
            except (OSError,ValueError,PermissionError) as e:
                save(x,"ERROR",message=f"Sonuç Excel'ine yolluk no yazılamadı: {e}",testMode="SIMULATED_NO_MYS_SUBMISSION")
                log(f"SIMULATED_RESULT_WRITE_FAILED assignment={x['assignmentId']} error={e}")
                raise
            save(x,"SIMULATED_COMPLETED",yollukId=yolluk_no,testMode="SIMULATED_NO_MYS_SUBMISSION",
                 resultWorkbook=str(result_excel))
            step("Test gönderimi simüle edildi",f"Sahte yolluk no {yolluk_no} Excel'e yazıldı; MYS kaydı oluşturulmadı.")
            log(f"SIMULATED_SUBMISSION assignment={x['assignmentId']} row={x['excelRow']} yollukNo={yolluk_no}")
            print(json.dumps({"status":"SIMULATED_COMPLETED","assignmentId":x["assignmentId"],
                              "yollukNo":yolluk_no,"resultWorkbook":str(result_excel)},ensure_ascii=False))
            continue
        if not a.live: print(json.dumps({"status":"READY_TO_SUBMIT","assignmentId":x["assignmentId"]},ensure_ascii=False)); return
        if not CFG.get("liveSubmissionEnabled") and not a.stop_before_submit: raise RuntimeError("Canlı gönderim kilidi kapalı.")
        if a.stop_before_submit:
            save(x,"READY_TO_SUBMIT",approvalGranted=(x["assignmentId"] in approvals),testMode="STOP_BEFORE_SUBMIT")
            print(json.dumps({"status":"STOP_BEFORE_SUBMIT","assignmentId":x["assignmentId"],"message":"Form tamamen dolduruldu; Yolluk Süreç Hazırlama butonuna BASILMADI."},ensure_ascii=False)); return
        # Kayıt butonuna yalnızca bir kez basılır. Bu noktadan sonra ikinci tıklama yasaktır.
        save(x,"SUBMITTING",approvalGranted=(x["assignmentId"] in approvals))
        ev("(()=>{let b=[...document.querySelectorAll('button')].find(x=>x.innerText.includes('Yolluk Süreç Hazırlama'));if(!b||b.disabled)throw Error('Submit aktif değil');b.click();return true})()")
        # MYS başarılı kayıtta kısa süreli yeşil bildirim gösterir ve ana sayfaya döner.
        time.sleep(2)
        save(x,"SUBMITTED_UNVERIFIED",approvalGranted=(x["assignmentId"] in approvals))
        url=str(ev("location.href"))
        m=re.search(r"/yolluk/view\?id=(\d+)",url)
        if m:
            save(x,"STAGE1_COMPLETED",yollukId=m.group(1));log("STAGE1_COMPLETED assignment="+x["assignmentId"]);continue
        # Ana sayfaya dönüldüyse liste henüz güvenilir değildir. MUTLAKA Sorgula yapılır.
        if "/yolluk/query" not in url:
            raise RuntimeError("Kayıt sonrası beklenmeyen sayfa: "+url)
        q=query_yolluk_list(x["tckn"])
        # Yeni kayıt listenin üstünde olsa da sıraya güvenmeyiz; tam tarih eşleşmesiyle doğrularız.
        found=[]
        for c in q.get("candidates",[]):
            for href in [u for u in c.get("links",[]) if "/yolluk/view?id=" in u]:
                try:
                    pw("goto",href);time.sleep(.5)
                    body=str(ev("document.body.innerText"))
                    sm=re.search(r"Başlangıç Tarihi\s+(\d{2}/\d{2}/\d{4})",body,re.I)
                    em=re.search(r"Bitiş Tarihi\s+(\d{2}/\d{2}/\d{4})",body,re.I)
                    if sm and em and sm.group(1)==x["start"] and em.group(1)==x["end"]:
                        mid=re.search(r"/yolluk/view\?id=(\d+)",href)
                        if mid and mid.group(1) not in baseline_ids: found.append(mid.group(1))
                except Exception: pass
        if len(found)==1:
            save(x,"STAGE1_COMPLETED",yollukId=found[0]);log("STAGE1_COMPLETED assignment="+x["assignmentId"]);continue
        # Belirsizlikte kesinlikle yeniden kayıt deneme.
        raise RuntimeError("Kayıt gönderildi ancak Sorgula sonrası yeni kayıt güvenle doğrulanamadı; ikinci kez gönderim yapılmadı.")
    print(json.dumps({"status":"RUN_COMPLETE"},ensure_ascii=False))

if __name__=="__main__": main()
