import os
import subprocess
from pathlib import Path


def resolve_cli_js(cli_path, appdata=None):
    # CLI wrapper yanındaki veya kullanıcının npm kökündeki JS dosyasını bularak sabit kullanıcı yolunu önle.
    candidates = []
    if cli_path:
        path = Path(cli_path)
        if path.suffix.lower() == ".js":
            candidates.append(path)
        candidates.extend((
            path.parent / "playwright-cli.js",
            path.parent / "node_modules" / "@playwright" / "cli" / "playwright-cli.js",
            path.parent.parent / "node_modules" / "@playwright" / "cli" / "playwright-cli.js",
        ))
    if appdata:
        candidates.append(Path(appdata) / "npm" / "node_modules" / "@playwright" / "cli" / "playwright-cli.js")
    return next((str(path) for path in candidates if path.is_file()), None)


def has_green_group(script_path):
    # CLI attach tek başına yeterli değil; kullanıcının Chrome'da Allow & select'i tamamladığını da doğrula.
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Playwright Chrome bağlantı durumu okunamadı.")
    return result.stdout.strip().splitlines()[-1:] == ["1"]


def launch_connection_setup(root, cli_js):
    # Var olan bağlantı koruyucusunu görünür konsolda bir kez çalıştır; attach/izin adımını kullanıcı tamamlar.
    helper = Path(root) / "scripts" / "playwright-connection" / "PLAYWRIGHT-CHROME-BAGLANTI.bat"
    if not helper.is_file():
        raise FileNotFoundError(f"Playwright bağlantı başlatıcısı bulunamadı: {helper}")
    env = os.environ.copy()
    env["PLAYWRIGHT_CLI_JS"] = str(cli_js)
    subprocess.Popen(
        ["cmd.exe", "/c", str(helper)],
        cwd=str(Path(root)),
        env=env,
        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
    )
