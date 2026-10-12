import importlib.util
import json
import sys
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
spec = importlib.util.spec_from_file_location(
    "yolluk_controller",
    Path(__file__).resolve().parents[1] / "scripts" / "yolluk-controller.py",
)
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


def multipart(data, filename="selected-name.xlsx"):
    boundary = "----workbook-test-boundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="workbook"; filename="{filename}"\r\n'
        "Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
    ).encode("ascii") + data + f"\r\n--{boundary}--\r\n".encode("ascii")
    return boundary, body


# Gerçek yerel HTTP endpoint'lerini geçici hedef dosyayla dene; gerçek veri alanına dokunma.
with TemporaryDirectory() as temp_dir:
    controller.UPLOADED_WORKBOOK = Path(temp_dir) / "uploaded.xlsx"
    controller.RESULT_WORKBOOK = Path(temp_dir) / "result.xlsx"
    server = controller.ThreadingHTTPServer(("127.0.0.1", 0), controller.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base_url + "/") as response:
            page = response.read().decode("utf-8")
            assert 'id="workbookFile"' in page
            assert "Boş şablonu indir" in page
            assert "Sahte No Üret" in page
            assert 'id="downloadResult"' in page

        with urlopen(base_url + "/api/template") as response:
            template = response.read()
            assert response.headers.get_content_type() == (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        try:
            urlopen(base_url + "/api/result")
        except HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError("Henüz üretilmemiş sonuç Excel'i indirilebilir göründü")

        boundary, body = multipart(template)
        request = Request(
            base_url + "/api/upload",
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Origin": base_url,
            },
        )
        with urlopen(request) as response:
            result = json.loads(response.read())
            assert response.status == 200 and result["ok"]
        assert controller.UPLOADED_WORKBOOK.read_bytes() == template

        controller.RESULT_WORKBOOK.write_bytes(template)
        with urlopen(base_url + "/api/result") as response:
            assert response.read() == template
            assert response.headers.get_content_disposition() == "attachment"
            assert "MYS-Yolluk-Sonuclari.xlsx" in response.headers.get("Content-Disposition")
        assert controller.status()["resultWorkbookReady"]

        boundary, body = multipart(template)
        request = Request(
            base_url + "/api/upload",
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Origin": "http://malicious.example",
            },
        )
        try:
            urlopen(request)
        except HTTPError as error:
            assert error.code == 403
        else:
            raise AssertionError("Yabancı Origin'den dosya yükleme kabul edildi")

        # Panel başlatıcısı yüklenen sabit dosyayı argüman olarak motora iletmeli.
        old_log, old_steps, old_proc = controller.LOG, controller.steps, controller.PROC
        old_popen = controller.subprocess.Popen
        commands = []

        class FakeProcess:
            def poll(self):
                return None

        def fake_popen(command, **kwargs):
            commands.append(command)
            return FakeProcess()

        controller.LOG = Path(temp_dir) / "stage1.log"
        controller.steps = Path(temp_dir) / "live-steps.json"
        controller.subprocess.Popen = fake_popen
        try:
            ok, _ = controller.start(["--simulate-submit"])
            assert ok
            assert "--simulate-submit" in commands[0]
            assert not controller.RESULT_WORKBOOK.exists()
            assert commands[0][-2:] == ["--excel", str(controller.UPLOADED_WORKBOOK)]
        finally:
            controller.subprocess.Popen = old_popen
            controller.LOG, controller.steps, controller.PROC = old_log, old_steps, old_proc
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

print("WORKBOOK PANEL TESTS OK")
