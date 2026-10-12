import sys
import tempfile
import importlib.util
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from playwright_connection import resolve_cli_js, launch_connection_setup

# Hazır bağlantıda launcher açılmaz; eksik başlangıç bağlantısı için açıkça istenirse bir kez çağrılır.
runner_path = Path(__file__).resolve().parents[1] / "scripts" / "stage1-live-run.py"
spec = importlib.util.spec_from_file_location("stage1_live_run", runner_path)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
with patch.object(runner, "playwright_health", return_value="OK"), \
     patch.object(runner, "launch_connection_setup") as launch:
    runner.wait_for_playwright(max_wait=0)
    launch.assert_not_called()

with patch.object(runner, "playwright_health", return_value="NO_CONNECTION"), \
     patch.object(runner, "resolve_cli_js", return_value="playwright-cli.js"), \
     patch.object(runner, "launch_connection_setup") as launch, \
     patch.object(runner, "step"), patch.object(runner, "log"), \
     patch.object(runner.time, "sleep"):
    runner.wait_for_playwright(max_wait=0,auto_start=True)
    launch.assert_called_once()

# Form akışı sırasında bağlantı kontrolü BAT/attach başlatmamalı.
with patch.object(runner, "playwright_health", return_value="NO_CONNECTION"), \
     patch.object(runner, "resolve_cli_js") as resolve_cli, \
     patch.object(runner, "launch_connection_setup") as launch, \
     patch.object(runner, "step"), patch.object(runner, "log"), \
     patch.object(runner.time, "sleep"):
    runner.wait_for_playwright(max_wait=0,auto_start=False,require_green=False)
    resolve_cli.assert_not_called()
    launch.assert_not_called()

# Her Playwright komutunda yalnız CLI attach durumu kontrol edilir; yeşil UI kontrolü başlangıçta kalır.
with patch.object(runner, "wait_for_playwright") as wait, \
     patch.object(runner.subprocess, "run", return_value=type("Result", (), {"returncode":0,"stdout":"ok","stderr":""})()):
    runner.pw("eval","1")
    wait.assert_called_once_with("Playwright işlemi öncesi kontrol",auto_start=False,require_green=False)


# CLI JS çözümlemesi config/PATH wrapper konumlarından taşınabilir şekilde bulunmalı.
with tempfile.TemporaryDirectory() as temp:
    npm_root = Path(temp) / "npm"
    npm_root.mkdir()
    wrapper = npm_root / "playwright-cli.cmd"
    wrapper.touch()
    cli_js = npm_root / "node_modules" / "@playwright" / "cli" / "playwright-cli.js"
    cli_js.parent.mkdir(parents=True)
    cli_js.touch()
    assert resolve_cli_js(str(wrapper)) == str(cli_js)

    # Bağlantı başlatıcısı proje içindeki BAT'ı ve çözülmüş CLI yolunu devralmalı.
    project = Path(temp) / "project"
    helper = project / "scripts" / "playwright-connection" / "PLAYWRIGHT-CHROME-BAGLANTI.bat"
    helper.parent.mkdir(parents=True)
    helper.touch()
    with patch("playwright_connection.subprocess.Popen") as popen:
        launch_connection_setup(project, cli_js)
        command, = popen.call_args.args
        assert command == ["cmd.exe", "/c", str(helper)]
        assert popen.call_args.kwargs["env"]["PLAYWRIGHT_CLI_JS"] == str(cli_js)

print("PLAYWRIGHT CONNECTION TESTS OK")
