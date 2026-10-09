import subprocess,time,urllib.request,json
root=r"C:\Users\serkan.suc\Desktop\MYS-YOLLUK-OTOMASYON"
subprocess.run(["taskkill","/F","/IM","python.exe"],capture_output=True)
time.sleep(1)
subprocess.Popen(["python",root+r"\scripts\yolluk-controller.py"],cwd=root,creationflags=subprocess.CREATE_NEW_CONSOLE)
time.sleep(1)
print(urllib.request.urlopen("http://127.0.0.1:8765/").status)
