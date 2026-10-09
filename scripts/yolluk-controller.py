import argparse, json, subprocess, sys, threading, time, shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"config/runner-settings.json"
CHECK=ROOT/"data/checkpoint.json"
LOG=ROOT/"logs/stage1.log"
steps=ROOT/"data/live-steps.json"
RUNNER=ROOT/"scripts/stage1-live-run.py"
PROC=None
LOCK=threading.Lock()

def read_json(p,default):
    try:return json.loads(p.read_text(encoding="utf-8-sig"))
    except:return default

def status():
    d=read_json(CHECK,{"records":{},"lastAssignment":None})
    records=d.get("records",{})
    last=records.get(d.get("lastAssignment"),{})
    return {
        "stage":d.get("stage","STAGE1"),
        "lastAssignment":d.get("lastAssignment"),
        "last":last,
        "records":records,
        "steps":live_steps(),
        "runnerRunning":PROC is not None and PROC.poll() is None,
        "liveLocked":not (read_json(CFG,{}).get("liveSubmissionEnabled",False) and not read_json(CFG,{}).get("stopBeforeLiveSubmit",True))
    }

def logs(n=120):
    if not LOG.exists(): return []
    return LOG.read_text(encoding="utf-8",errors="replace").splitlines()[-n:]

def live_steps():
    try: return json.loads(steps.read_text(encoding="utf-8"))
    except: return []

def start(args):
    global PROC
    with LOCK:
        if PROC is not None and PROC.poll() is None:return False,"Otomasyon zaten çalışıyor."
        if LOG.exists() and LOG.stat().st_size:
            archive=ROOT/"logs"/"archive"
            archive.mkdir(parents=True,exist_ok=True)
            stamp=time.strftime("%Y%m%d_%H%M%S")
            shutil.copy2(LOG, archive/f"stage1_{stamp}.txt")
        LOG.write_text("",encoding="utf-8")
        steps.write_text("[]",encoding="utf-8")
        out=LOG.open("a",encoding="utf-8")
        PROC=subprocess.Popen([sys.executable,str(RUNNER)]+args,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,
                              creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0))
        return True,"Otomasyon başlatıldı."

def stop():
    global PROC
    with LOCK:
        if PROC is None or PROC.poll() is not None:return False,"Çalışan otomasyon yok."
        PROC.terminate();return True,"Otomasyon durduruldu."

HTML=r'''<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>MYS Yolluk Otomasyon</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#eef2f6;color:#17202a;font-family:Segoe UI,Arial,sans-serif}
.wrap{max-width:1450px;margin:auto;padding:18px}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
h1{font-size:24px;margin:0}.sub{color:#667085;font-size:13px;margin-top:3px}
.badge{padding:8px 13px;border-radius:20px;font-weight:700;background:#e8edf3}.run{background:#dcfce7;color:#166534}.stop{background:#fee2e2;color:#991b1b}
.alert{display:none;padding:14px 16px;border-radius:10px;margin-bottom:14px;font-weight:700;border:1px solid #fecaca;background:#fff1f2;color:#991b1b}
.alert.show{display:block}.alert.wait{border-color:#fcd34d;background:#fffbeb;color:#92400e}
.layout{display:grid;grid-template-columns:390px 1fr;gap:14px}.card{background:white;border:1px solid #d9dee7;border-radius:12px;padding:15px;box-shadow:0 1px 2px #00000008}
.card h2{font-size:16px;margin:0 0 12px}.state{font-size:22px;font-weight:800;margin-bottom:5px}.muted{color:#667085;font-size:12px}
.buttons{display:grid;gap:8px;margin-top:12px}.buttons button{border:0;border-radius:8px;padding:12px;text-align:left;font-weight:700;cursor:pointer}
.primary{background:#2563eb;color:white}.warn{background:#f59e0b;color:#17202a}.safe{background:#e7edf5;color:#17202a}.danger{background:#dc2626;color:white}
button:disabled{opacity:.45;cursor:not-allowed}.info{background:#f7f9fb;border-radius:8px;padding:10px;margin-top:12px;font-size:13px;line-height:1.55}
.logcard{min-width:0}.loghead{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}.live{font-size:12px;color:#166534;font-weight:700}
.log{height:610px;background:#101722;color:#d9e2ec;border-radius:9px;padding:13px;overflow:auto;font:12px/1.55 Consolas,monospace;white-space:pre-wrap}
.counts{display:flex;gap:6px;flex-wrap:wrap}.pill{background:#edf1f5;border-radius:14px;padding:5px 8px;font-size:11px}
.detail{margin-top:12px;font-size:13px;line-height:1.6}.detail b{display:inline-block;width:120px}
.steps{max-height:430px;overflow:auto;border:1px solid #e5e9ef;border-radius:8px;padding:5px 10px;background:#fbfcfd}
.step{padding:8px 2px;border-bottom:1px solid #e9edf2}
.step:last-child{border-bottom:0}.step .num{font-weight:800}.step .time{font-size:11px;color:#667085;margin-right:7px}.step .desc{font-size:12px;color:#475467;margin-top:2px}
@media(max-width:900px){.layout{grid-template-columns:1fr}.log{height:450px}}
</style></head><body><div class="wrap">
<div class="top"><div><h1>MYS Yolluk Otomasyon</h1><div class="sub">Aşama 1 • Excel → Yolluk Süreç Hazırlama</div></div><div id="badge" class="badge stop">DURDU</div></div>
<div id="alert" class="alert"></div>
<div class="layout">
<div>
<div class="card"><h2>Şu an ne yapıyor?</h2><div id="state" class="state">Bekliyor</div><div id="stateSub" class="muted">Henüz işlem başlatılmadı.</div>
<div class="buttons">
<button class="primary" onclick="run([])">▶ Kuru Test</button>
<button class="safe" onclick="run(['--stop-before-submit'])">🧪 Formu Doldur — Gönderme</button>
<button class="danger" onclick="stopRun()">■ Durdur</button>
</div>
<div class="info">Çakışma bulunursa ekranda <b>açık uyarı</b> gösterilir ama otomasyon durmaz; yeni yolluk işlemiyle otomatik devam eder. Teknik ayrıntılar alttaki logda tutulur.</div></div>
<div class="card" style="margin-top:14px"><h2>İşlem adımları <span class="muted">• canlı</span></h2><div id="steps" class="steps">-</div></div>
<div class="card" style="margin-top:14px"><h2>Son işlem</h2><div id="detail" class="detail">-</div></div>
<div class="card" style="margin-top:14px"><h2>Durum özeti</h2><div id="counts" class="counts">-</div></div>
</div>
<div class="card logcard"><div class="loghead"><h2 style="margin:0">Canlı İşlem Günlüğü</h2><span id="live" class="live">● OTOMATİK YENİLENİYOR</span></div><div id="log" class="log">Log bekleniyor...</div></div>
</div></div>
<script>
async function api(p,o){let r=await fetch(p,Object.assign({cache:"no-store"},o||{}));let t=await r.text();try{return JSON.parse(t)}catch(e){throw new Error("Sunucu cevabı okunamadı: "+t.slice(0,120))}}
function setAlert(text,wait=false){let a=document.getElementById('alert');a.textContent=text;a.className='alert'+(text?' show':'')+(wait?' wait':'')}
let actionMsg={text:'',until:0};
function stateText(s){
 let x=s.last||{},st=x.status||'IDLE';
 const map={PROCESSING:'İşlem yapılıyor',WAITING_FOR_USER_APPROVAL:'Eski durum',DUPLICATE_APPROVED:'Eski durum',DUPLICATE_WARNING_CONTINUING:'Mevcut kayıt var — devam ediliyor (bilgi)',READY_TO_SUBMIT:'Form hazır — gönderilmedi',ERROR:'İŞLEM DURDU — HATA',STAGE1_COMPLETED:'Tamamlandı',SUBMITTING:'Canlı kayıt gönderiliyor',SUBMITTED_UNVERIFIED:'Gönderildi — doğrulama bekleniyor',AMBIGUOUS_DUPLICATE:'Tarih belirsizliği — bilgiyle devam ediliyor'};
 return [map[st]||st,st]
}
async function refresh(){
 try{
 let s=await api('/api/status'), [label,st]=stateText(s);
 document.getElementById('state').textContent=s.runnerRunning?'● '+label:label;
 document.getElementById('stateSub').textContent=s.runnerRunning?'Otomasyon aktif.':(st==='ERROR'?'Güvenli noktada durdu. Ayrıntı aşağıda ve logda.':st==='WAITING_FOR_USER_APPROVAL'?'Çakışma bulundu. Devam için onay gerekiyor.':'Otomasyon şu anda çalışmıyor.');
 let b=document.getElementById('badge');b.textContent=s.runnerRunning?'ÇALIŞIYOR':'DURDU';b.className='badge '+(s.runnerRunning?'run':'stop');
 let x=s.last||{}, detail='<b>Durum:</b> '+(x.status||'-')+'<br><b>Satır:</b> '+(x.row||'-')+'<br><b>Tarih:</b> '+(x.mysStart||'-')+' → '+(x.mysEnd||'-');
 if(x.warning)detail+='<br><b>Uyarı:</b> '+x.warning;if(x.message)detail+='<br><b>Hata:</b> '+x.message;
 document.getElementById('detail').innerHTML=detail;
 let steps=s.steps||[];
 let boxSteps=document.getElementById('steps');
 boxSteps.innerHTML=steps.length?steps.map((z,i)=>'<div class="step"><span class="num">'+(i+1)+'. '+z.label+'</span> <span class="time">'+z.time+'</span><div class="desc">'+(z.detail||'')+'</div></div>').join(''):'-';
 boxSteps.scrollTop=boxSteps.scrollHeight;
 let c={};Object.values(s.records||{}).forEach(x=>c[x.status]=(c[x.status]||0)+1);document.getElementById('counts').innerHTML=Object.entries(c).map(([k,v])=>'<span class="pill">'+k+': '+v+'</span>').join('')||'-';
 let l=await api('/api/log');let box=document.getElementById('log');let old=box.scrollTop,atBottom=box.scrollHeight-box.clientHeight-old<80;box.textContent=l.lines.length?l.lines.join('\n'):'Log bekleniyor... (günlük boş — işlem başlayınca satırlar buraya düşer)';if(atBottom)box.scrollTop=box.scrollHeight;
 let warning='';
 if(st==='ERROR')warning='⛔ İŞLEM DURDU: '+(x.message||'Hata oluştu.');
 else if(st==='WAITING_FOR_USER_APPROVAL')warning='⚠ Eski durum: bu proje artık çakışma için kullanıcı onayı beklemiyor.';
 else if(st==='DUPLICATE_WARNING_CONTINUING')warning='ℹ BİLGİ: Aynı personel için mevcut yolluk kaydı bulundu (aynı tarihlerde dahi olabilir). Normal durum; onay beklemeden devam ediliyor.';
 else if(st==='AMBIGUOUS_DUPLICATE')warning='ℹ BİLGİ: Mevcut kayıt tarihleri güvenle ayrıştırılamadı; onay beklemeden devam ediliyor.';
 setAlert(warning||((Date.now()<actionMsg.until)?actionMsg.text:''),st!=='ERROR');
 let lu=document.getElementById('live');if(lu)lu.textContent='● OTOMATİK YENİLENİYOR '+new Date().toLocaleTimeString('tr-TR');
 }catch(e){setAlert('⚠ Panelden sunucuya ulaşılamıyor — http://127.0.0.1:8765 sayfasını yenileyin ('+e.message+')',true)}
}
async function run(args){actionMsg={text:'⏳ Komut gönderiliyor...',until:Date.now()+30000};setAlert(actionMsg.text,true);try{let r=await api('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({args})});actionMsg={text:r.message,until:Date.now()+6000};setAlert(r.message,!!r.ok);await refresh()}catch(e){actionMsg={text:'⛔ Panel hatası: '+e.message,until:Date.now()+15000};setAlert(actionMsg.text,true)}}
async function stopRun(){actionMsg={text:'⏳ Durdurma komutu gönderiliyor...',until:Date.now()+15000};setAlert(actionMsg.text,true);try{let r=await api('/api/stop',{method:'POST'});actionMsg={text:r.message,until:Date.now()+6000};setAlert(r.message,!!r.ok);await refresh()}catch(e){actionMsg={text:'⛔ Panel hatası: '+e.message,until:Date.now()+15000};setAlert(actionMsg.text,true)}}
refresh();setInterval(refresh,1000)
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def sendj(self,obj,code=200):
        b=json.dumps(obj,ensure_ascii=False).encode("utf-8");self.send_response(code);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path)
        if p.path=="/":
            b=HTML.encode("utf-8");self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b);return
        if p.path=="/api/status":self.sendj(status());return
        if p.path=="/api/log":self.sendj({"lines":logs()});return
        self.send_error(404)
    def do_POST(self):
        p=urlparse(self.path)
        if p.path in ("/api/start","/api/stop"):
            if p.path=="/api/stop":ok,msg=stop();self.sendj({"ok":ok,"message":msg},200 if ok else 409);return
            n=int(self.headers.get("Content-Length","0"));body=json.loads(self.rfile.read(n) or b"{}");ok,msg=start(body.get("args",[]));self.sendj({"ok":ok,"message":msg},200 if ok else 409);return
        self.send_error(404)
    def log_message(self,*args):pass

if __name__=="__main__":
    LOG.parent.mkdir(parents=True,exist_ok=True)
    if LOG.exists() and LOG.stat().st_size:
        archive=ROOT/"logs"/"archive";archive.mkdir(parents=True,exist_ok=True)
        shutil.copy2(LOG, archive/f"stage1_{time.strftime("%Y%m%d_%H%M%S")}_panelstart.txt")
    LOG.write_text("",encoding="utf-8")
    steps.write_text("[]",encoding="utf-8")
    ap=argparse.ArgumentParser();ap.add_argument("--port",type=int,default=8765);a=ap.parse_args()
    print("MYS Yolluk Otomasyon: http://127.0.0.1:"+str(a.port),flush=True)
    ThreadingHTTPServer(("127.0.0.1",a.port),Handler).serve_forever()
