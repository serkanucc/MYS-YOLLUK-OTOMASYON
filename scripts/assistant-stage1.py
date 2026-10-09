import argparse,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
sys.stderr.reconfigure(encoding="utf-8",errors="replace")
RUNNER=ROOT/"scripts/stage1-live-run.py"
MANIFEST=ROOT/"data/session-manifest.json"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--excel")
    ap.add_argument("--live",action="store_true")
    ap.add_argument("--approve",action="append",default=[])
    a=ap.parse_args()
    manifest={"stage":"STAGE1","mode":"LIVE" if a.live else "DRY_RUN",
              "sourceWorkbook":a.excel or None,"chatControlled":True,
              "humanApprovalRequiredForOverlap":False}
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    cmd=[sys.executable,str(RUNNER)]
    if a.live: cmd.append("--live")
    if a.excel: cmd+=["--excel",a.excel]
    for ident in a.approve: cmd+=["--approve",ident]
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace")
    print(p.stdout)
    if p.returncode: print(p.stderr,file=sys.stderr)
    return p.returncode

if __name__=="__main__": raise SystemExit(main())
