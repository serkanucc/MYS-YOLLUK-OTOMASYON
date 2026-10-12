$ErrorActionPreference = "Stop"
$CLI = $env:PLAYWRIGHT_CLI_JS
if([string]::IsNullOrWhiteSpace($CLI)) {
    $npmRoot = & npm root -g 2>$null
    if($LASTEXITCODE -eq 0 -and $npmRoot) {
        $CLI = Join-Path (($npmRoot | Select-Object -Last 1).Trim()) "@playwright\cli\playwright-cli.js"
    }
}
if($env:APPDATA -and ([string]::IsNullOrWhiteSpace($CLI) -or -not (Test-Path -LiteralPath $CLI))) {
    $CLI = Join-Path $env:APPDATA "npm\node_modules\@playwright\cli\playwright-cli.js"
}
$SESSION = "chrome-main"
$GREEN = Join-Path $PSScriptRoot "PW-GREEN-CHECK.ps1"

function Get-State {
    if([string]::IsNullOrWhiteSpace($CLI) -or -not (Test-Path -LiteralPath $CLI)) { return $null }
    $raw = & node $CLI list --all --json 2>$null
    if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($raw -join ""))) { return $null }
    return ($raw -join [Environment]::NewLine) | ConvertFrom-Json
}

function Get-Green {
    $v = & powershell -NoProfile -ExecutionPolicy Bypass -File $GREEN 2>$null
    return (($v | Select-Object -Last 1) -eq "1")
}

function Detach-Session([string]$name) {
    & node $CLI "-s=$name" detach 2>$null | Out-Null
    Start-Sleep -Milliseconds 700
}

try {
    $state = Get-State
    $green = Get-Green
    if($null -eq $state) { Write-Output "NO_CONNECTION"; exit 20 }

    $browsers = @($state.browsers)
    $main = @($browsers | Where-Object { $_.name -eq $SESSION })
    $others = @($browsers | Where-Object { $_.name -ne $SESSION })

    if($main.Count -eq 1 -and $main[0].status -eq "open" -and $main[0].attached -eq $true) {
        foreach($x in $others) {
            if($x.attached -eq $true) {
                Write-Output ("DETACHING " + $x.name)
                Detach-Session $x.name
            }
        }
        $state = Get-State
        $browsers = @($state.browsers)
        $others = @($browsers | Where-Object { $_.name -ne $SESSION })
        if($others.Count -gt 0) { Write-Output ("CONFLICT: " + (($others | ForEach-Object {$_.name}) -join ", ")); exit 30 }
        if($green) { Write-Output "OK"; exit 0 }
        Write-Output "MAIN_EXISTS_GREEN_MISSING"; exit 40
    }

    # Aynı kullanıcı BAT'ındaki davranış gibi, ana oturum yokken bağlı diğer session'ları detach et; Chrome'u kapatma.
    foreach($x in $others) {
        if($x.attached -eq $true) {
            Write-Output ("DETACHING " + $x.name)
            Detach-Session $x.name
        }
    }

    $state = Get-State
    $browsers = @($state.browsers)
    if($browsers.Count -eq 0) { Write-Output "NO_CONNECTION"; exit 20 }

    Write-Output ("CONFLICT: chrome-main missing/invalid; sessions=" + (($browsers | ForEach-Object {$_.name}) -join ", "))
    exit 30
}
catch {
    Write-Output ("ERROR: " + $_.Exception.Message)
    exit 50
}
