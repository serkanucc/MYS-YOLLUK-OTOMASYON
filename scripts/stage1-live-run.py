import json,os,re,shutil,subprocess,time,argparse
from pathlib import Path
import openpyxl
from assignment import assignment_id,classify_candidates,TRAVEL_TYPE,duty_period

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config/runner-settings.json").read_text(encoding="utf-8-sig"))
FIXED=json.loads((ROOT/"config/fixed-values.json").read_text(encoding="utf-8-sig"))
FLOW_PRE=(ROOT/"scripts/stage1-flow-pre.js").read_text(encoding="utf-8")
FLOW_POST=(ROOT/"scripts/stage1-flow-post.js").read_text(encoding="utf-8")
DUP=(ROOT/"scripts/duplicate-check.js").read_text(encoding="utf-8")
EXCEL_CFG=CFG["sourceWorkbook"]
EXCEL=(ROOT/EXCEL_CFG) if not Path(EXCEL_CFG).is_absolute() else Path(EXCEL_CFG)
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


def playwright_health():
    """Bağlantı durumunu Playwright CLI oturum listesinden okur.
    Bu proje hiçbir şekilde attach başlatmaz; bağlantı kullanıcı tarafından başlatılır.

    Dönen değerler:
      OK              : hedef session açık ve attach
      NO_CONNECTION   : CLI çalışıyor ama hedef session yok / attach değil
      SESSION_CONFLICT: birden fazla aynı adlı session (uyumsuz durum)
      CLI_MISSING     : playwright-cli.cmd hiç bulunamadı (kurulum/yol sorunu)
      CLI_ERROR       : CLI çalıştırılamadı veya çıktısı okunamadı
    """
    if not CLI or not Path(CLI).exists():
        return "CLI_MISSING"
    try:
        raw=subprocess.run([CLI,"list","--all","--json"],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=10)
    except Exception:
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
        return "OK"
    return "NO_CONNECTION"


def wait_for_playwright(context="",max_wait=None):
    """Bağlantı yoksa işlemi güvenli noktada bekletir; otomatik ikinci attach yapmaz.
    CLI kurulu değilse (CLI_MISSING) beklemek anlamsızdır; hemen hata verir.
    max_wait: saniye; verilirse bu süre içinde bağlantı kurulmazsa sessizce döner."""
    start=time.time();last=None
    while True:
        state=playwright_health()
        if state=="OK":
            if last is not None:
                log("PLAYWRIGHT_RECONNECTED | chrome-main oturumu dogrulandi")
                step("Playwright bağlantısı yeniden kuruldu", "chrome-main oturumu doğrulandı")
            return
        if state=="CLI_MISSING":
            raise RuntimeError("playwright-cli.cmd bulunamadı. Playwright CLI kurulumunu veya cliPath ayarını kontrol edin.")
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
    wait_for_playwright("Playwright işlemi öncesi kontrol")
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
            "Excel dosyası bulunamadı: "+str(EXCEL)+"\n"
            "Güncel 'Yolluk Liste' dosyasını bu yola koyun veya config/runner-settings.json "
            "içindeki 'sourceWorkbook' değerini güncelleyin (panelden çalıştırırken de "
            "--excel <dosya> ile geçici yol verebilirsiniz).")
    wb=openpyxl.load_workbook(EXCEL,data_only=True,read_only=True);ws=wb[wb.sheetnames[0]]
    amir_tckn=read_amir_tckn(wb)
    rows=list(ws.iter_rows(values_only=True));h=[str(x).strip() if x is not None else "" for x in rows[0]]
    def ci(*names):
        for n in names:
            if n in h:return h.index(n)
        raise RuntimeError("Excel sütunu eksik: "+names[0])
    ti,di,ii,ai,ri=ci("TC NO","TCKN"),ci("GEÇ. GÖREV TARİHİ","GEÇ GÖREV TARİHİ"),ci("IBAN"),ci("GÜNDELİĞİ","GUNDELIGI"),ci("SIRANO","SIRA NO")
    # GÜN SAYISI indeksini bir kez hesapla (önceden her satırda yeniden aranıyordu -> verimsiz).
    gsi=ci("GÜN SAYISI","GUN SAYISI") if ("GÜN SAYISI" in h or "GUN SAYISI" in h) else None
    out=[];skipped=[]
    for r in rows[1:]:
        if not any(x is not None and str(x).strip() for x in r):continue
        try:
            # Bir satır bozuk/format-dışıysa TÜM listeyi çökertme; o satırı atla ve logla.
            dates,start,end=duty_period(r[di])
            iban_value=str(r[ii] or "").strip()
            if not valid_tr_iban(iban_value):
                raise RuntimeError(f"IBAN biçimi/checksum geçersiz: {iban_value!r}")
            x={"row":r[ri],"tckn":r[ti],"iban":iban_value,"daily":r[ai],
               "dayCount":(r[gsi] if gsi is not None else None),
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

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--live",action="store_true")
    ap.add_argument("--approve",action="append",default=[])
    ap.add_argument("--skip-duplicate",action="store_true")
    ap.add_argument("--stop-before-submit",action="store_true")
    ap.add_argument("--force-form-test",action="store_true")
    ap.add_argument("--force-iban-reset",action="store_true")
    ap.add_argument("--excel")
    a=ap.parse_args()
    global EXCEL
    if a.excel: EXCEL=(ROOT/a.excel) if not Path(a.excel).is_absolute() else Path(a.excel)
    approvals=set(a.approve)|approved_ids(a)
    # BAŞLANGIÇ KONTROLÜ: Excel/form işlemine geçmeden önce bağlantı kesinlikle hazır olmalı.
    wait_for_playwright("MYS otomasyonu başlangıç kontrolü")
    try:
        assignments=people()
    except RuntimeError as e:
        msg=str(e)
        if "Birim Amiri" in msg and "Excel" in msg:
            print(json.dumps({"status":"USER_INFORMATION_REQUIRED","field":"Birim Amiri TCKN","message":msg},ensure_ascii=False)); return
        raise
    for x in assignments:
        d=json.loads(CHECK.read_text(encoding="utf-8-sig")) if CHECK.exists() else {}
        old=d.get("records",{}).get(x["assignmentId"],{})
        if old.get("status")=="STAGE1_COMPLETED" and not a.force_form_test: continue
        approval_granted=(x["assignmentId"] in approvals) or (old.get("approvalGranted") is True)
        if approval_granted: approvals.add(x["assignmentId"])
        save(x,"PROCESSING",approvalGranted=approval_granted)
        log(f"PROCESSING assignment={x['assignmentId']} row={x['row']}");step("Kişi işleme alındı", f"Excel satırı {x['row']}")
        matches=[]
        if not a.skip_duplicate:
            step("MYS kayıtları kontrol ediliyor");q=duplicate(x)
            matches=classify_candidates(q.get("candidates",[]),x)
            if matches:
                warning="MEVCUT KAYIT BİLGİSİ: Aynı personel için yolluk kaydı bulundu (aynı tarihlerde dahi olabilir — normal durum). Onay gerekmiyor; otomasyon devam ediyor."
                save(x,"DUPLICATE_WARNING_CONTINUING",matches=matches,approvalGranted=False,warning=warning)
                log(f"DUPLICATE_WARNING_CONTINUING assignment={x['assignmentId']} matches={len(matches)} -> devam ediliyor")
                step("Mevcut kayıt bulundu", "Bilgi amaçlı: aynı tarihlerde dahi yeni işlem açılabilir; onay beklemeden deviliyor.")
        # Formu açmadan hemen önce listeyi bir kez daha tazele; mevcut kayıt ID'lerini referans al.
        step("Yeni form açılıyor");baseline_q=query_yolluk_list(x["tckn"])
        baseline_ids=set()
        for bc in baseline_q.get("candidates",[]):
            for bu in bc.get("links",[]):
                bm=re.search(r"/yolluk/view\?id=(\d+)",bu)
                if bm: baseline_ids.add(bm.group(1))
        js_pre=FLOW_PRE.replace("{{FORCE_IBAN}}","true" if a.force_iban_reset else "false").replace("{{TCKN}}",str(x["tckn"])).replace("{{IBAN}}",str(x["iban"])).replace("{{DAILY}}",str(x["daily"])).replace("{{START}}",x["start"]).replace("{{END}}",x["end"]).replace("{{AMIR_TCKN}}",str(x["amirTckn"])).replace("{{BUDGET}}",FIXED["budgetItem"])
        js_post=FLOW_POST.replace("{{TCKN}}",str(x["tckn"])).replace("{{IBAN}}",str(x["iban"])).replace("{{DAILY}}",str(x["daily"])).replace("{{START}}",x["start"]).replace("{{END}}",x["end"]).replace("{{AMIR_TCKN}}",str(x["amirTckn"])).replace("{{BUDGET}}",FIXED["budgetItem"])
        result=None
        for form_attempt in range(1,3):
            pw("goto",CFG["formUrl"]);time.sleep(1.2)
            try:
                step("Form dolduruluyor", "TCKN, Mernis, maaş, IBAN ve sabit alanlar");result=ev(re.sub(r"\s+"," ",js_pre))
                if result.get("needsIbanCommit"):
                    pw("press","Enter");time.sleep(.7)
                    iban_check=ev("(()=>{const l=[...document.querySelectorAll('label.yte-form-label')].find(x=>x.title==='IBAN');const e=document.getElementById(l.htmlFor);return [...e.querySelectorAll('.yte-power-select-multiple-selected-option-label')].map(x=>x.innerText.trim())})()")
                    if str(x["iban"]).strip().upper() not in [str(v).strip().upper() for v in iban_check]: raise RuntimeError("Excel IBAN Enter sonrası MYS formunda seçilemedi")
                step("Form tamamlanıyor", "Tarih, gündelik, bütçe ve Birim Amiri kontrolleri");result=ev(re.sub(r"\s+"," ",js_post))
                if result.get("submitDisabled") is not False: raise RuntimeError("Form tamamlanmadı: Yolluk Süreç Hazırlama aktif değil")
                break
            except Exception as e:
                log(f"FORM_FILL_RETRY assignment={x['assignmentId']} attempt={form_attempt} error={e}")
                if form_attempt==2:
                    save(x,"ERROR",message=str(e),formAttempts=form_attempt)
                    raise
                time.sleep(1.5)
        step("Form hazır", "Yolluk Süreç Hazırlama gönderimine hazır.");save(x,"READY_TO_SUBMIT",approvalGranted=(x["assignmentId"] in approvals))
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


