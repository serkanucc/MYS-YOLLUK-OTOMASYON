$ErrorActionPreference = "Stop"
$port = 8765

# Yalnızca bu otomasyonun boşta olan panelini kapat; başka servis/PID'lere dokunma.
$listenerIds = @(
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
)
if ($listenerIds.Count -eq 0) {
    Write-Host "8765 portunda eski panel yok; yeni panel başlatılacak."
    exit 0
}

foreach ($listenerId in $listenerIds) {
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $listenerId"
    if (-not $processInfo -or $processInfo.Name -notin @("python.exe", "pythonw.exe") -or
        $processInfo.CommandLine -notmatch 'scripts[\\/]+yolluk-controller\.py') {
        Write-Error "8765 portunu bu projeye ait olduğu doğrulanamayan bir işlem kullanıyor (PID $listenerId). İşlem kapatılmadı."
        exit 1
    }

    # Sunucu durumunu okuyamazsak veya otomasyon çalışıyorsa panel sürecini kesinlikle durdurma.
    try {
        $status = Invoke-RestMethod -Uri "http://127.0.0.1:$port/api/status" -TimeoutSec 3
    } catch {
        Write-Error "Mevcut panel durumu okunamadı. PID $listenerId güvenlik için kapatılmadı."
        exit 1
    }
    if ($status.runnerRunning) {
        Write-Error "Otomasyon hâlâ çalışıyor. Önce işlemin bitmesini bekleyin; panel kapatılmadı."
        exit 1
    }

    Write-Host "Boşta olan eski panel kapatılıyor (PID $listenerId)..."
    Stop-Process -Id $listenerId
}

$deadline = (Get-Date).AddSeconds(10)
do {
    Start-Sleep -Milliseconds 250
    $remaining = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
} while ($remaining.Count -gt 0 -and (Get-Date) -lt $deadline)

if ($remaining.Count -gt 0) {
    Write-Error "8765 portu 10 saniye içinde boşalmadı; yeni panel başlatılmadı."
    exit 1
}

Write-Host "Eski panel kapandı; güncel panel başlatılacak."
exit 0
