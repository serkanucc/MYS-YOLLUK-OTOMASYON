from pathlib import Path
p=Path(r"C:\Users\serkan.suc\Desktop\MYS-YOLLUK-OTOMASYON\scripts\yolluk-controller.py")
s=p.read_text(encoding="utf-8-sig")
s=s.replace('''.detail{margin-top:12px;font-size:13px;line-height:1.6}.detail b{display:inline-block;width:120px}''','''.detail{margin-top:12px;font-size:13px;line-height:1.6}.detail b{display:inline-block;width:120px}
.steps{max-height:430px;overflow:auto;border:1px solid #e5e9ef;border-radius:8px;padding:5px 10px;background:#fbfcfd}
.step{padding:8px 2px;border-bottom:1px solid #e9edf2}
.step:last-child{border-bottom:0}.step .num{font-weight:800}.step .time{font-size:11px;color:#667085;margin-right:7px}.step .desc{font-size:12px;color:#475467;margin-top:2px}''')
s=s.replace('''<div class="card" style="margin-top:14px"><h2>İşlem adımları</h2><div id="steps" class="detail">-</div></div>''','''<div class="card" style="margin-top:14px"><h2>İşlem adımları <span class="muted">• canlı</span></h2><div id="steps" class="steps">-</div></div>''')
old='''let st=s.steps||[];
 document.getElementById('steps').innerHTML=st.length?st.map((z,i)=>'<div style="padding:7px 0;border-bottom:1px solid #edf0f3"><b>'+(i+1)+'. '+z.label+'</b><br><span class="muted">'+z.time+' — '+(z.detail||'')+'</span></div>').join(''):'-';'''
new='''let st=s.steps||[];
 let boxSteps=document.getElementById('steps');
 boxSteps.innerHTML=st.length?st.map((z,i)=>'<div class="step"><span class="num">'+(i+1)+'. '+z.label+'</span> <span class="time">'+z.time+'</span><div class="desc">'+(z.detail||'')+'</div></div>').join(''):'-';
 boxSteps.scrollTop=boxSteps.scrollHeight;'''
if old not in s: raise SystemExit("steps render bulunamadı")
s=s.replace(old,new)
p.write_text(s,encoding="utf-8")
print("HISTORY_UI_OK")
