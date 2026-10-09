import json,re,subprocess,time
from pathlib import Path
import openpyxl
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config/runner-settings.json").read_text(encoding="utf-8"))
T=(ROOT/"scripts/duplicate-check.js").read_text(encoding="utf-8")
wb=openpyxl.load_workbook(CFG["sourceWorkbook"],data_only=True,read_only=True)
ws=wb[wb.sheetnames[0]]
rows=list(ws.iter_rows(values_only=True));h=[str(x).strip() if x is not None else "" for x in rows[0]]
i=h.index("TC NO") if "TC NO" in h else h.index("TCKN")
t=str(rows[1][i])
js=re.sub(r"\s+"," ",T.replace("{{TCKN}}",t))
subprocess.run([r"C:\Users\serkan.suc\AppData\Roaming\npm\playwright-cli.cmd","-s="+str(CFG.get("browserSession","chrome-main")),"goto","https://butunlesik.hmb.gov.tr/hys/mys-yollukislemleri/yolluk"],check=True)
time.sleep(1)
p=subprocess.run([r"C:\Users\serkan.suc\AppData\Roaming\npm\playwright-cli.cmd","-s="+str(CFG.get("browserSession","chrome-main")),"eval",js],capture_output=True,text=True,encoding="utf-8",errors="replace")
if p.returncode: raise SystemExit(p.stderr or p.stdout)
m=re.search(r"### Result\s*\n([\s\S]*?)(?:\n### Ran|$)",p.stdout)
print(m.group(1).strip() if m else p.stdout)
